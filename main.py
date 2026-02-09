import datetime
import requests

# === 你的最新金鑰 ===
CLIENT_ID = 'c1124209-ca5c1e20-3385-4a5a'
CLIENT_SECRET = '235328ba-36b5-4037-b908-d2c20205f522'

def get_token():
    auth_url = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token'
    
    # 嚴格對齊官方要求
    payload = f'grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}'
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    try:
        response = requests.post(auth_url, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get('access_token'), "驗證成功"
        else:
            # 這裡會抓出 TDX 給出的具體原因 (例如: invalid_client)
            return None, f"金鑰驗證失敗: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"連線異常: {str(e)}"

def get_data(token):
    headers = {'authorization': f'Bearer {token}'}
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
    try:
        res = requests.get(url, headers=headers, timeout=15)
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
            return final_results
        return None
    except:
        return None

def build_web():
    token, auth_msg = get_token()
    data = get_data(token) if token else None
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>雪隧路況正式版</title>
        <style>
            body {{ background: #121212; color: white; font-family: sans-serif; text-align: center; padding: 10px; }}
            .card {{ background: #1e1e1e; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 450px; border: 1px solid #333; }}
            .title {{ font-size: 1.4em; color: #f1c40f; font-weight: bold; margin-bottom: 15px; }}
            .lane-container {{ display: flex; justify-content: space-around; }}
            .lane-box {{ background: #2a2a2a; padding: 15px; border-radius: 12px; width: 42%; }}
            .speed {{ color: #2ecc71; font-size: 2.2em; font-weight: bold; }}
            .flow {{ color: #3498db; font-size: 0.8em; margin-top: 5px; }}
            .debug {{ font-size: 0.7em; color: #ff4757; background: #000; padding: 10px; margin-top: 20px; text-align: left; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <h2>📊 雪隧即時數據 (正式版)</h2>
        <p style="color:#aaa;">更新時間：{time_str}</p>
    """
    
    if not token:
        html += f"<div class='card'><h3>驗證尚未通過</h3><div class='debug'>{auth_msg}</div></div>"
    elif not data:
        html += "<div class='card'>驗證成功，但 API 暫時沒回傳數據。請等 1 分鐘再按一次更新。</div>"
    else:
        for direct, lanes in data.items():
            html += f'<div class="card"><div class="title">{direct}</div><div class="lane-container">'
            for l in lanes:
                html += f'''
                <div class="lane-box">
                    <div style="font-size:0.8em; color:#888;">{l["name"]}</div>
                    <div class="speed">{l["speed"]}</div>
                    <div class="flow">流量: {l["flow"]}</div>
                </div>
                '''
            best = "內側" if lanes[0]['speed'] >= lanes[1]['speed'] else "外側"
            html += f'</div><p style="color:#e67e22; font-weight:bold; margin-top:15px;">💡 建議走：{best}車道</p></div>'
            
    html += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
