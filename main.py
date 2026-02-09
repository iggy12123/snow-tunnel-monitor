// main.js
// Node.js 18+ 可直接跑（內建 fetch）
// 記得先把 CLIENT_ID / CLIENT_SECRET 換成你的

const CLIENT_ID = 'c1124209-ca5c1e20-3385-4a5a';
const CLIENT_SECRET = '4ead6654-55c6-4d1e-adf6-d42edc4bd3c2';

const TOKEN_URL = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token';

// 雪隧（國道5號）API
const SPEED_API = 'https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/LiveTrafficSpeed/Freeway';
const VOLUME_API = 'https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/LiveTrafficVolume/Freeway';

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

async function fetchTDX(api, token) {
  const res = await fetch(`${api}?$format=JSON`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  return res.json();
}

function filterSnowTunnel(data) {
  // 國道5號 + 雪山隧道
  return data.filter(item =>
    item.FreewayID === '005' &&
    item.RoadName?.includes('雪山')
  );
}

function summarize(speedData, volumeData) {
  const lanes = {};

  volumeData.forEach(v => {
    const key = `${v.Direction}_${v.LaneID}`;
    lanes[key] = lanes[key] || {};
    lanes[key].volume = v.Volume || 0;
  });

  speedData.forEach(s => {
    const key = `${s.Direction}_${s.LaneID}`;
    lanes[key] = lanes[key] || {};
    lanes[key].speed = s.Speed || 0;
  });

  return lanes;
}

function printResult(lanes) {
  console.log('📊 雪山隧道 即時交通狀況\n');

  const dirMap = { 'N': '北上', 'S': '南下' };
  const laneMap = { '1': '左側車道', '2': '右側車道' };

  let maxLane = null;
  let maxVolume = 0;

  Object.entries(lanes).forEach(([key, data]) => {
    const [dir, lane] = key.split('_');
    const volume = data.volume || 0;
    const speed = data.speed || 0;

    console.log(
      `${dirMap[dir]}｜${laneMap[lane]}：` +
      `速率 ${speed} km/h｜載運量 ${volume} 輛`
    );

    if (volume > maxVolume) {
      maxVolume = volume;
      maxLane = `${dirMap[dir]} ${laneMap[lane]}`;
    }
  });

  console.log('\n🚨 車流量最多的車道');
  console.log(`➡️ ${maxLane}（${maxVolume} 輛）`);
}

async function main() {
  try {
    const token = await getAccessToken();

    const speedRaw = await fetchTDX(SPEED_API, token);
    const volumeRaw = await fetchTDX(VOLUME_API, token);

    const speedData = filterSnowTunnel(speedRaw);
    const volumeData = filterSnowTunnel(volumeRaw);

    const lanes = summarize(speedData, volumeData);

    printResult(lanes);
  } catch (err) {
    console.error('❌ 發生錯誤', err);
  }
}

main();
