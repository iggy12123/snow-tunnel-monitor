import datetime
import requests
import json

# === 請在下方填入你的 TDX 金鑰 ===
CLIENT_ID = '你的_CLIENT_ID'
CLIENT_SECRET = '你的_CLIENT_SECRET'

def get_token():
    auth_url = "https://tdx.transportdata.tw/auth/realms/number9/protocol/openid-connect/token"
    data = {
        'content-type': 'application/x-www-form-urlencoded',
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
    # 抓取國道五號即時路況
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        vd_list = res.json().get('VDLives', [])
        
        # 鎖定雪隧代表性偵測點：北上(20N), 南下(20S)
        targets = {"nfb0020N": "北上 (往台北)", "nfb0020S": "南下 (往宜蘭)"}
        final_results = {}
        
        for vd in vd_list:
            v_id = vd.get('VDID')
            if v_id in targets:
                lanes = vd.get('LaneVDs', [])
                lane_info = []
                # 只取前兩線道 (內側、外側)
                for i, l in enumerate(lanes[:2]):
                    lane_info.append({
                        "name": "內側" if i == 0 else "外側",
                        "speed": l.get('Speed', 0),
                        "flow": l.get('Volume', 0) * 12 # 5分鐘流量換算成時流量
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
        <title>雪隧全方位看板</title>
        <style>
            body {{ font-family: sans-serif; background-color: #121212; color: white; text-align: center; padding: 10px; }}
            .card {{ background: #1e1e1e; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 350px; border: 1px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
            .title {{ font-size: 1.4em; color: #f1c40f; margin-bottom: 15px; font-weight: bold; }}
            .lane {{ display: flex; justify-content: space-between; align-items: center; background: #2a2a2a; padding: 15px; margin: 8px 0; border-radius: 10px; }}
            .speed {{ color: #2ecc71; font-size: 1.2em; font-weight: bold; }}
            .flow {{ color: #3498db; font-size: 0.9em; }}
            .tag {{ font-size: 0.8em; color: #888; background: #000; padding: 2px 6px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h2>📊 雪山隧道即時路況看板</h2>
        <p style="color:#aaa;">更新時間：{time_str}</p>
    """
    if not data:
        html += "<div class='card' style='color:#e74c3c;'>數據獲取失敗<br><small>請確認 TDX 金鑰是否有效</small></div>"
    else:
        for direct, lanes in data.items():
            html += f'<div class="card"><div class="title">{direct}</div>'
            for l in lanes:
                html += f'''
                <div class="lane">
                    <span>{l["name"]} <span class="tag">車道</span></span>
                    <span class="speed">{l["speed"]} <small>km/h</small></span>
                    <span class="flow">{l["flow"]} <small>輛/時</small></span>
                </div>
                '''
            # 簡單的建議邏輯
            best = "內側" if lanes[0]['speed'] >= lanes[1]['speed'] else "外側"
            html += f'<div style="color:#e67e22; margin-top:10px; font-weight:bold;">💡 建議走：{best}</div></div>'
            
    html += "<p style='color:#555; font-size:0.7em; margin-top:30px;'>數據來源：交通部 TDX 平台 (5分鐘統計)</p></body></html>"
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
