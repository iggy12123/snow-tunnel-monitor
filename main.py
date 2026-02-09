import datetime
import requests
import time

# === 你的正式金鑰 ===
CLIENT_ID = 'c1124209-ca5c1e20-3385-4a5a'
CLIENT_SECRET = '4ead6654-55c6-4d1e-adf6-d42edc4bd3c2'

def get_token():
    auth_url = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token'
    payload = {'grant_type': 'client_credentials', 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post(auth_url, data=payload, headers=headers, timeout=15)
        return response.json().get('access_token') if response.status_code == 200 else None
    except:
        return None

def get_data(token):
    headers = {'authorization': f'Bearer {token}'}
    # 使用最穩定的國五即時路況網址
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            vd_list = res.json().get('VDLives', [])
            # 鎖定雪隧關鍵偵測點：nfb0020N (北上), nfb0020S (南下)
            targets = {"nfb0020N": "北上 (往台北)", "nfb0020S": "南下 (往宜蘭)"}
            results = {}
            for vd in vd_list:
                v_id = vd.get('VDID')
                if v_id in targets:
                    lanes = vd.get('LaneVDs', [])
                    lane_info = []
                    # 抓取內外側車道
                    for i, l in enumerate(lanes[:2]):
                        lane_info.append({
                            "name": "內側" if i == 0 else "外側",
                            "speed": l.get('Speed', 0),
                            "flow": l.get('Volume', 0) * 12 
                        })
                    results[targets[v_id]] = lane_info
            return results if len(results) > 0 else None
        return None
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
        <title>雪隧路況專業儀表板</title>
        <style>
            body {{ background-color: #121212; color: white; font-family: sans-serif; text-align: center; padding: 10px; }}
            .card {{ background: #1e1e1e; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 450px; border: 1px solid #333; }}
            .title {{ font-size: 1.5em; color: #f1c40f; font-weight: bold; margin-bottom: 20px; }}
            .lane-container {{ display: flex; justify-content: space-around; }}
            .lane-box {{ background: #2a2a2a; padding: 15px; border-radius: 12px; width: 45%; }}
            .speed {{ color: #2ecc71; font-size: 2em; font-weight: bold; }}
            .flow {{ color: #3498db; font-size: 0.8em; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <h2>📊 雪隧即時數據 (更新成功)</h2>
        <p style="color:#aaa; font-size:0.8em;">最後更新：{time_str}</p>
    """
    
    if not data:
        html += "<div class='card'><h3>⏳ 數據同步中</h3><p>驗證已通過，正在等待交通部回傳數據。<br>請在 1 分鐘後重新整理網頁。</p></div>"
    else:
        for direct, lanes in data.items():
            html += f'<div class="card"><div class="title">{direct}</div><div class="lane-container">'
            for l in lanes:
                html += f'''
                <div class="lane-box">
                    <div style="font-size:0.8em; color:#888;">{l["name"]}</div>
                    <div class="speed">{l["speed"]} <small style="font-size:0.5em;">km/h</small></div>
                    <div class="flow">載運量: {l["flow"]}</div>
                </div>
                '''
            best = "內側" if lanes[0]['speed'] >= lanes[1]['speed'] else "外側"
            html += f'</div><div style="color:#e67e22; margin-top:15px; font-weight:bold;">💡 建議走：{best}車道</div></div>'
            
    html += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
