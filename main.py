import datetime

def get_status():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 目前為模擬數據，跑通後可串接真實 API
    inner_speed = 62 
    outer_speed = 75
    suggestion = "走外側較快" if outer_speed > inner_speed else "走內側較快"
    
    html_content = f"""
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>雪隧路況自動分析</title></head>
    <body style="font-family: sans-serif; text-align: center; padding-top: 50px; background-color: #f0f2f5;">
        <h1>宜蘭通勤助手：雪隧路況</h1>
        <p>更新時間：{now} (UTC)</p>
        <div style="font-size: 28px; background: white; border-radius: 20px; display: inline-block; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            建議車道：<strong style="color: #2ecc71;">{suggestion}</strong><br>
            <hr style="margin: 20px 0;">
            <div style="font-size: 20px;">
                內側車道：{inner_speed} km/h<br>
                外側車道：{outer_speed} km/h
            </div>
        </div>
        <p style="color: #888; font-size: 12px; margin-top: 30px;">每 10 分鐘自動更新</p>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    get_status()
