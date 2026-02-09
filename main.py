import datetime
import requests
import json

# === 請再次確認這兩串有沒有多餘的空格 ===
CLIENT_ID = 'c1124209-ca5c1e20-3385-4a5a'
CLIENT_SECRET = '4ead6654-55c6-4d1e-adf6-d42edc4bd3c2'

def get_token():
    auth_url = "https://tdx.transportdata.tw/auth/realms/number9/protocol/openid-connect/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID.strip(), # 自動去掉前後空格
        'client_secret': CLIENT_SECRET.strip()
    }
    try:
        response = requests.post(auth_url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json().get('access_token'), "成功"
        else:
            return None, f"金鑰驗證失敗 (錯誤碼: {response.status_code})"
    except Exception as e:
        return None, f"連線異常: {str(e)}"

def get_data(token):
    headers = {'authorization': f'Bearer {token}'}
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            vd_list = res.json().get('VDLives', [])
            targets = {"nfb0020N": "北上 (往台北)", "nfb0020S": "南下 (往宜蘭)"}
            final_results = {}
            for vd in vd_list:
                v_id = vd.get('VDID')
                if v_id in targets:
                    lanes = vd.get('LaneVDs', [])
                    lane_info = []
                    for i, l in enumerate(lanes[:2]):
                        lane_info.append({
                            "name": "內側" if i == 0 else "外側",
                            "speed": l.get('Speed', 0),
                            "flow": l.get('Volume', 0) * 12 
                        })
                    final_results[targets[v_id]] = lane_info
            return final_results, "成功"
        else:
            return None, f"抓取數據失敗 (錯誤碼: {res.status_code})"
    except Exception as e:
        return None, f"數據讀取異常: {str(e)}"

def build_web():
    token, auth_msg = get_token()
    data, data_msg = (None, "尚未讀取")
    if token:
        data, data_msg = get_data(token)
    
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>雪隧路況偵錯版</title>
        <style>
            body {{ font-family: sans-serif; background-color: #121212; color: white; text-align: center; padding: 20px; }}
            .card {{ background: #1e1e1e; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 400px; border: 1px solid #444; }}
            .error {{ color: #ff4757; font-size: 0.9em; background: #2f3542; padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .lane {{ display: flex; justify-content: space-around; margin-top: 15px; }}
            .speed {{ font-size: 2em; color: #2ecc71; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>🔍 雪隧數據讀取狀態</h2>
        <p>更新時間：{time_str}</p>
        
        <div class="card">
            <p>1. 身分驗證：{auth_msg}</p>
            <p>2. 數據抓取：{data_msg}</p>
        </div>
    """
    
    if data:
        for direct, lanes in data.items():
            html += f'<div class="card"><h3>{direct}</h3><div class="lane">'
            for l in lanes:
                html += f'<div><small>{l["name"]}</small><div class="speed">{l["speed"]}</div><small>流量:{l["flow"]}</small></div>'
            html += '</div></div>'
    else:
        html += '<div class="card" style="border-color: #ff4757;">⚠️ 目前無法讀取數據，請稍後再試</div>'
        
    html += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
