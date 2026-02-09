import datetime
import requests

# === 你的最新金鑰 (請確保 Secret 是重新產生的那組) ===
CLIENT_ID = 'c1124209-ca5c1e20-3385-4a5a'
CLIENT_SECRET = '235328ba-36b5-4037-b908-d2c20205f522'

def get_token():
    # 根據官方手冊，使用 TDXConnect 驗證入口
    auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    
    # 嚴格對應手冊要求的參數名稱
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID.strip(),
        'client_secret': CLIENT_SECRET.strip()
    }
    
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    try:
        response = requests.post(auth_url, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get('access_token'), "驗證成功"
        else:
            return None, f"金鑰驗證失敗 (狀態碼: {response.status_code})"
    except Exception as e:
        return None, f"網路連線異常: {str(e)}"

def get_data(token):
    headers = {'authorization': f'Bearer {token}'}
    # 國五即時路況數據網址
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            vd_list = res.json().get('VDLives', [])
            # 雪隧關鍵點偵測 (20N 北上, 20S 南下)
            targets = {"nfb0020N": "北上 (往台北)", "nfb0020S": "南下 (往宜蘭)"}
            final_results = {}
            for vd in vd_list:
                v_id = vd.get('VDID')
                if v_id in targets:
                    lanes = vd.get('LaneVDs', [])
                    lane_info = []
                    # 統計內外側車道
                    for i, l in enumerate(lanes[:2]):
                        lane_info.append({
                            "name": "內側" if i == 0 else "外側",
                            "speed": l.get('Speed', 0),
                            "flow": l.get('Volume', 0) * 12 # 換算時流量 (載運量)
                        })
                    final_results[targets[v_id]] = lane_info
            return final_results, "數據抓取成功"
        return None, f"API 回傳錯誤 (代碼: {res.status_code})"
    except Exception as e:
        return None, f"抓取異常: {str(e)}"

def build_web():
    token, auth_msg = get_token()
    data, data_msg = (None, "等待驗證中")
    if token:
        data, data_msg = get_data(token)
    
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>雪隧即時儀表板</title>
        <style>
            body {{ font-family: sans-serif; background-color: #121212; color: white; text-align: center; padding: 15px; }}
            .card {{ background: #1e1e1e; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 450px; border: 1px solid #333; }}
            .title {{ font-size: 1.5em; color: #f1c40f; font-weight: bold; margin-bottom: 20px; }}
            .lane-row {{ display: flex; justify-content: space-around; }}
            .lane-box {{ background: #2a2a2a; padding: 15px; border-radius: 12px; width: 42%; }}
            .speed {{ color: #2ecc71; font-size: 1.8em; font-weight: bold; }}
            .flow {{ color: #3498db; font-size: 0.8em; margin-top: 5px; }}
            .status-msg {{ font-size: 0.8em; color: #888; background: #222; padding: 10px; border-radius: 8px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h2>🚗 雪隧即時路況監控</h2>
        <p style="color:#aaa; font-size:0.9em;">更新時間：{time_str}</p>
    """
    
    if data:
        for direct, lanes in data.items():
            html += f'<div class="card"><div class="title">{direct}</div><div class="lane-row">'
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
    else:
        html += f"<div class='card' style='border-color:#ff4757;'><h3>⚠️ 讀取中</h3><p>{auth_msg}</p><p>{data_msg}</p></div>"
            
    html += "<p style='color:#444; font-size:0.7em; margin-top:30px;'>數據來源：交通部 TDX 平台</p></body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
