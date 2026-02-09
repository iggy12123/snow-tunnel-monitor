import datetime
import requests

# === 你的正式金鑰 (請確認 Secret 是最後那組 4ead...) ===
CLIENT_ID = 'c1124209-ca5c1e20-3385-4a5a'
CLIENT_SECRET = '4ead6654-55c6-4d1e-adf6-d42edc4bd3c2'

def get_token():
    auth_url = 'https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token'
    # 使用 x-www-form-urlencoded 格式
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post(auth_url, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get('access_token'), "驗證成功"
        else:
            return None, f"驗證失敗: {response.status_code}"
    except Exception as e:
        return None, f"連線異常: {str(e)}"

def get_data(token):
    headers = {'authorization': f'Bearer {token}', 'Accept-Encoding': 'gzip'}
    # 取得國五所有即時路況
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        vd_list = res.json().get('VDLives', [])
        
        # 參考範例網站，鎖定雪隧最具代表性的兩個偵測點
        # nfb0020N: 北上 20K (隧道內), nfb0020S: 南下 20K (隧道內)
        targets = {"nfb0020N": "北上 (往台北)", "nfb0020S": "南下 (往宜蘭)"}
        final_results = {}
        
        for vd in vd_list:
            v_id = vd.get('VDID')
            if v_id in targets:
                lanes = vd.get('LaneVDs', [])
                lane_info = []
                for i, l in enumerate(lanes[:2]): # 只拿內、外兩線
                    lane_info.append({
                        "name": "內側" if i == 0 else "外側",
                        "speed": l.get('Speed', 0),
                        "flow": l.get('Volume', 0) * 12 # 換算時流量 (載運量)
                    })
                final_results[targets[v_id]] = lane_info
        return final_results
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
        <title>雪隧即時路況看板</title>
        <style>
            body {{ background-color: #121212; color: white; font-family: -apple-system, sans-serif; text-align: center; padding: 10px; }}
            .card {{ background: #1e1e1e; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 450px; border: 1px solid #333; }}
            .header {{ font-size: 1.5em; font-weight: bold; margin-bottom: 20px; color: #f1c40f; display: flex; align-items: center; justify-content: center; }}
            .lane-container {{ display: flex; justify-content: space-around; gap: 10px; }}
            .lane-box {{ background: #2a2a2a; padding: 15px; border-radius: 12px; width: 48%; }}
            .lane-name {{ font-size: 0.9em; color: #888; margin-bottom: 5px; }}
            .speed {{ color: #2ecc71; font-size: 2.5em; font-weight: bold; line-height: 1; }}
            .flow {{ color: #3498db; font-size: 0.8em; margin-top: 8px; }}
            .suggestion {{ color: #e67e22; margin-top: 15px; font-weight: bold; border-top: 1px solid #333; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div style="font-size: 1.8em; font-weight: bold; margin: 10px 0;">📊 雪隧即時路況監控</div>
        <p style="color:#aaa; font-size:0.8em; margin-bottom: 20px;">更新時間：{time_str}</p>
    """
    
    if not token:
        html += f"<div class='card' style='border-color: #ff4757;'>⚠️ 認證失敗：{auth_msg}</div>"
    elif not data:
        html += "<div class='card'>🔄 數據同步中，請稍後再試</div>"
    else:
        for direct, lanes in data.items():
            html += f'<div class="card"><div class="header">📍 {direct}</div><div class="lane-container">'
            for l in lanes:
                html += f'''
                <div class="lane-box">
                    <div class="lane-name">{l["name"]}車道</div>
                    <div class="speed">{l["speed"]}</div>
                    <div style="font-size:0.6em; color:#2ecc71;">km/h</div>
                    <div class="flow">載運量: {l["flow"]}</div>
                </div>
                '''
            # 判斷路隊長位置
            best = "內側" if lanes[0]['speed'] >= lanes[1]['speed'] else "外側"
            html += f'</div><div class="suggestion">💡 建議走：{best}車道</div></div>'
            
    html += "<p style='color:#444; font-size:0.7em; margin-top:30px;'>數據來源：交通部 TDX 平台</p></body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
