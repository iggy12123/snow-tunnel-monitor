import datetime
import requests

def get_data():
    # 使用不需金鑰的公開 URL (訪客模式)
    url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24top=50&%24format=JSON"
    try:
        # 加上簡單的 Header 讓請求看起來比較像正常瀏覽
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        vd_list = res.json().get('VDLives', [])
        
        # 鎖定雪隧北上(20N)與南下(20S)
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
    data = get_data()
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>雪隧路況 (應急版)</title>
        <style>
            body {{ font-family: sans-serif; background-color: #121212; color: white; text-align: center; padding: 10px; }}
            .card {{ background: #1e1e1e; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 350px; border: 1px solid #333; }}
            .title {{ font-size: 1.4em; color: #f1c40f; margin-bottom: 15px; font-weight: bold; }}
            .lane {{ display: flex; justify-content: space-between; align-items: center; background: #2a2a2a; padding: 15px; margin: 8px 0; border-radius: 10px; }}
            .speed {{ color: #2ecc71; font-size: 1.2em; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>📊 雪隧路況 (訪客模式)</h2>
        <p style="color:#aaa;">更新時間：{time_str}</p>
    """
    if not data:
        html += "<div class='card'>數據獲取中或達到政府限制<br><small>請過 30 分鐘再試</small></div>"
    else:
        for direct, lanes in data.items():
            html += f'<div class="card"><div class="title">{direct}</div>'
            for l in lanes:
                html += f'<div class="lane"><span>{l["name"]}</span><span class="speed">{l["speed"]} km/h</span></div>'
            best = "內側" if lanes[0]['speed'] >= lanes[1]['speed'] else "外側"
            html += f'<div style="color:#e67e22; margin-top:10px; font-weight:bold;">💡 建議走：{best}</div></div>'
            
    html += "</body></html>"
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    build_web()
