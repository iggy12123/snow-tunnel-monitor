import datetime
import requests

def get_data():
    # TDX 公開 API 網址：抓取國道五號所有偵測點
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        vd_list = data.get('VDLives', [])
    except:
        return None

    # 定義雪隧最具代表性的兩個偵測點 (約在隧道中段 20K-22K)
    # 北向 (N) 往台北, 南向 (S) 往宜蘭
    targets = {
        "nfb0020N": "北上 (往台北)", 
        "nfb0020S": "南下 (往宜蘭)"
    }
    
    results = {}
    for vd in vd_list:
        v_id = vd.get('VDID')
        if v_id in targets:
            lanes = vd.get('LaneVDs', [])
            # 通常 Lane 0 是內側，Lane 1 是外側
            lane_data = []
            for i, lane in enumerate(lanes[:2]):
                lane_name = "內側" if i == 0 else "外側"
                lane_data.append({
                    "name": lane_name,
                    "speed": lane.get('Speed', 0),
                    "flow": lane.get('Volume', 0) * 12 # 將 5 分鐘流量換算為時速流量
                })
            results[targets[v_id]] = lane_data
    return results

def build_web():
    data = get_data()
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>雪隧全方位監控</title>
        <style>
            body {{ font-family: sans-serif; background-color: #121212; color: #e0e0e0; text-align: center; padding: 10px; }}
            .container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; }}
            .card {{ background: #1e1e1e; border: 1px solid #333; border-radius: 15px; width: 320px; padding: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
            .direction {{ font-size: 1.5em; color: #f1c40f; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 5px; }}
            .lane {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 10px; background: #252525; border-radius: 8px; }}
            .speed {{ color: #2ecc71; font-weight: bold; }}
            .flow {{ color: #3498db; }}
            .rec {{ color: #e67e22; font-weight: bold; margin-top: 10px; font-size: 1.1em; }}
        </style>
    </head>
    <body>
        <h2>🛣️ 雪山隧道即時數據看板</h2>
        <p>更新時間：{time_str}</p>
        <div class="container">
    """
    
    if not data:
        html += "<p>暫時無法獲取政府數據，請稍後再試</p>"
    else:
        for direct, lanes in data.items():
            best = "內側" if lanes[0]['speed'] >= lanes[1]['speed'] else "外側"
            html += f"""
            <div class="card">
                <div class="direction">{direct}</div>
                {"".join([f'<div class="lane"><span>{l["name"]}</span><span class="speed">{l["speed"]} km/h</span><span class="flow">{l["flow"]} 輛/時</span></div>' for l in lanes])}
                <div class="rec">💡 建議走：{best}</div>
            </div>
            """
            
    html += "</div><p style='color:#666; font-size:0.8em; margin-top:20px;'>數據源：交通部 TDX (5分鐘統計值)</p></body></html>"
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
