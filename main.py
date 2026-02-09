// main.js
// Node.js 18+
// 雪山隧道（國道5號）即時速率 + 車流量

const CLIENT_ID = process.env.TDX_CLIENT_ID || 'c1124209-ca5c1e20-3385-4a5a';
const CLIENT_SECRET = process.env.TDX_CLIENT_SECRET || '4ead6654-55c6-4d1e-adf6-d42edc4bd3c2';

const TOKEN_URL =
  'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token';

const SPEED_API =
  'https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/LiveTrafficSpeed/Freeway';
const VOLUME_API =
  'https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/LiveTrafficVolume/Freeway';

async function getAccessToken() {
  const body = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: CLIENT_ID,
    client_secret: CLIENT_SECRET
  });

  const res = await fetch(TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body
  });

  const data = await res.json();
  return data.access_token;
}

async function fetchTDX(url, token) {
  const res = await fetch(`${url}?$format=JSON`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.json();
}

// 國道 5 號（含雪隧）
function filterFreeway5(data) {
  return data.filter(item => item.FreewayID === '005');
}

function getDirection(dir) {
  if (dir === 'N' || dir === 1 || dir === '1') return '北上';
  if (dir === 'S' || dir === 2 || dir === '2') return '南下';
  return '未知方向';
}

function getLane(lane) {
  if (!lane) return '未知車道';
  if (lane.includes('1')) return '左側車道';
  if (lane.includes('2')) return '右側車道';
  return `車道 ${lane}`;
}

function mergeData(speedData, volumeData) {
  const result = {};

  volumeData.forEach(v => {
    const key = `${v.Direction}_${v.LaneID}`;
    result[key] = result[key] || {};
    result[key].volume = v.Volume ?? 0;
  });

  speedData.forEach(s => {
    const key = `${s.Direction}_${s.LaneID}`;
    result[key] = result[key] || {};
    result[key].speed = s.Speed ?? 0;
  });

  return result;
}

function printResult(data) {
  console.log('\n📊 雪山隧道（國道5號）即時交通狀況\n');

  let maxVolume = 0;
  let maxLane = '';

  for (const [key, val] of Object.entries(data)) {
    const [dir, lane] = key.split('_');

    const speed = val.speed ?? 0;
    const volume = val.volume ?? 0;

    const text = `${getDirection(dir)}｜${getLane(lane)}：速率 ${speed} km/h｜載運量 ${volume} 輛`;
    console.log(text);

    if (volume > maxVolume) {
      maxVolume = volume;
      maxLane = `${getDirection(dir)} ${getLane(lane)}`;
    }
  }

  console.log('\n🚨 車流量最多的車道');
  console.log(`➡️ ${maxLane}（${maxVolume} 輛）\n`);
}

async function main() {
  try {
    const token = await getAccessToken();

    const speedRaw = await fetchTDX(SPEED_API, token);
    const volumeRaw = await fetchTDX(VOLUME_API, token);

    const speedData = filterFreeway5(speedRaw);
    const volumeData = filterFreeway5(volumeRaw);

    const merged = mergeData(speedData, volumeData);

    printResult(merged);
  } catch (err) {
    console.error('❌ 錯誤：', err);
  }
}

main();
