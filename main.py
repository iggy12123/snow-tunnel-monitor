import datetime
import requests

# === 你的正式金鑰 (已移除前後可能存在的空格) ===
CLIENT_ID = 'c1124209-ca5c1e20-3385-4a5a'.strip()
CLIENT_SECRET = '4ead6654-55c6-4d1e-adf6-d42edc4bd3c2'.strip()

def get_token():
    # 使用 TDX 官方標準的 OIDC Token 請求網址
    auth_url = "https://tdx.transportdata.tw/auth/realms/number9/protocol/openid-connect/token"
    
    # TDX 規定必須使用 x-www-form-urlencoded 格式發送
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        # 使用 data 參數發送以確保格式正確
        response = requests.post(auth_url, data=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.json().get('access_token'), "驗證成功"
        else:
            # 這裡會捕捉到為什麼 404 或其他錯誤的詳細原因
            return None, f"金鑰驗證失敗 (錯誤碼: {response.status_code})"
    except Exception as e:
        return None, f"網路連線異常: {str(e)}"

def get_data(token):
    headers = {
        'authorization': f'Bearer {token}',
        'Accept-Encoding': 'gzip'
    }
    # 抓取國五即時路況數據
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            vd_list = res.json().get('VDLives', [])
            # 鎖定雪隧北上(nfb0020N)與南下(nfb0020S)
            targets = {"nfb0020N": "北上 (往台北)", "nfb0020S": "南下 (往宜蘭)"}
            final_results = {}
            
            for vd in vd_list:
                v_id = vd.get('VDID')
                if v_id in targets:
                    lanes = vd.get('LaneVDs', [])
                    lane_info = []
                    # 抓取內、外側車道數據
                    for i, l in enumerate(lanes[:2]):
                        lane_info.append({
                            "name": "內側" if i == 0 else "外側",
                            "speed": l.get('Speed', 0),
                            "flow": l.get('Volume', 0) * 12 # 換算時流量
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
        <title>雪隧路況專屬看板</title>
        <style>
            body {{ font-family: sans-serif; background-color: #121212; color: white; text-align: center; padding: 15px; }}
            .card {{ background: #1e1e1e; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 450px; border: 1px solid #333; }}
            .title {{ font-size: 1.4em; color: #f1c40f; font-weight: bold; margin-bottom: 15px; }}
            .lane-container {{ display: flex; justify-content: space-around; }}
            .lane-box {{ background: #2a2a2a; padding: 15px; border-radius: 12px; width: 45%; }}
            .speed {{ color: #2ecc71; font-size: 1.8em; font-weight: bold; }}
            .flow {{ color: #3498db; font-size: 0.8em; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <h2>🚗 雪山隧道即時數據</h2>
        <p style="color:#aaa; font-size:0.8em;">最後更新：{time_str}</p>
    """
    
    if not token:
        html += f"<div class='card' style='border-color:red;'>⚠️ 驗證失敗：{auth_msg}</div>"
    elif not data:
        html += "<div class='card'>數據連線中，請稍後再試</div>"
    else:
        for direct, lanes in data.items():
            html += f'<div class="card"><div class="title">{direct}</div><div class="lane-container">'
            for l in lanes:
                html += f'''
                <div class="lane-box">
                    <div style="font-size:0.8em; color:#888;">{l["name"]}</div>
                    <div class="speed">{l["speed"]} <small style="font-size:0.5em;">km/h</small></div>
                    <div class="flow">流量: {l["flow"]}</div>
                </div>
                '''
            best = "內側" if lanes[0]['speed'] >= lanes[1]['speed'] else "外側"
            html += f'</div><div style="color:#e67e22; margin-top:15px; font-weight:bold;">💡 建議走：{best}車道</div></div>'
            
    html += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
