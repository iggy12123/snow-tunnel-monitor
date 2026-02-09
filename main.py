import datetime
import requests

# === 你的 TDX 正式金鑰 ===
CLIENT_ID = 'c1124209-ca5c1e20-3385-4a5a'
CLIENT_SECRET = '4ead6654-55c6-4d1e-adf6-d42edc4bd3c2'

def get_token():
    auth_url = "https://tdx.transportdata.tw/auth/realms/number9/protocol/openid-connect/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    try:
        response = requests.post(auth_url, data=data, timeout=10)
        return response.json().get('access_token')
    except:
        return None

def get_data(token):
    headers = {'authorization': f'Bearer {token}'}
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        vd_list = res.json().get('VDLives', [])
        # 鎖定雪隧北上與南下關鍵偵測點
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
        return final_results
    except:
        return None

def build_web():
    token = get_token()
    data = get_data(token) if token else None
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>雪隧路況專屬看板</title>
        <style>
            body {{ font-family: sans-serif; background-color: #121212; color: white; text-align: center; padding: 10px; }}
            .card {{ background: #1e1e1e; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 350px; border: 1px solid #333; }}
            .title {{ font-size: 1.4em; color: #f1c40f; font-weight: bold; margin-bottom: 15px; }}
            .lane {{ display: flex; justify-content: space-between; align-items: center; background: #2a2a2a; padding: 15px; margin: 8px 0; border-radius: 10px; }}
            .speed {{ color: #2ecc71; font-size: 1.2em; font-weight: bold; }}
            .flow {{ color: #3498db; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <h2>🚗 雪山隧道早晚尖峰看板</h2>
        <p style="color:#aaa;">更新時間：{time_str}</p>
    """
    if not data:
        html += "<div class='card'>連線失敗，請檢查金鑰</div>"
    else:
        for direct, lanes in data.items():
            html += f'<div class="card"><div class="title">{direct}</div>'
            for l in lanes:
                html += f'<div class="lane"><span>{l["name"]}</span><span class="speed">{l["speed"]} km/h</span><span class="flow">{l["flow"]} 輛/時</span></div>'
            best = "內側" if lanes[0]['speed'] >= lanes[1]['speed'] else "外側"
            html += f'<div style="color:#e67e22; margin-top:10px; font-weight:bold;">💡 建議：走{best}</div></div>'
            
    html += "<p style='color:#555; font-size:0.7em; margin-top:30px;'>基礎會員版：每月 3,000 次額度</p></body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
