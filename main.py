import requests
import datetime

# 你的正式金鑰
CLIENT_ID = 'c1124209-ca5c1e20-3385-4a5a'
CLIENT_SECRET = '4ead6654-55c6-4d1e-adf6-d42edc4bd3c2'

class Auth():
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_auth_header(self):
        content_type = 'application/x-www-form-urlencoded'
        grant_type = 'client_credentials'
        url = 'https://tdx.transportdata.tw/auth/realms/number9/protocol/openid-connect/token'
        
        data = {
            'grant_type': grant_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        res = requests.post(url, data=data, headers={'content-type': content_type})
        res_json = res.json()
        return {'authorization': 'Bearer ' + res_json.get('access_token')}

def build_web():
    try:
        # 1. 取得認證
        auth = Auth(CLIENT_ID, CLIENT_SECRET)
        headers = auth.get_auth_header()
        
        # 2. 抓取數據 (國五即時路況)
        url = "https://tdx.transportdata.tw/api/basic/v2/Road/Traffic/Live/VD/Freeway/5?%24format=JSON"
        res = requests.get(url, headers=headers)
        vd_list = res.json().get('VDLives', [])
        
        # 3. 篩選雪隧數據
        targets = {"nfb0020N": "北上 (往台北)", "nfb0020S": "南下 (往宜蘭)"}
        results = {}
        for vd in vd_list:
            v_id = vd.get('VDID')
            if v_id in targets:
                lanes = vd.get('LaneVDs', [])
                lane_data = []
                for i, l in enumerate(lanes[:2]):
                    lane_data.append({
                        "name": "內側" if i == 0 else "外側",
                        "speed": l.get('Speed', 0),
                        "flow": l.get('Volume', 0) * 12
                    })
                results[targets[v_id]] = lane_data

        # 4. 產生網頁內容
        now = datetime.datetime.now() + datetime.timedelta(hours=8)
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
        <html>
        <head>
            <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ background: #121212; color: white; font-family: sans-serif; text-align: center; }}
                .card {{ background: #1e1e1e; border: 1px solid #333; border-radius: 15px; padding: 20px; margin: 15px auto; max-width: 400px; }}
                .lane-box {{ display: inline-block; width: 45%; background: #2a2a2a; padding: 10px; border-radius: 10px; margin: 5px; }}
                .speed {{ font-size: 2em; color: #2ecc71; font-weight: bold; }}
                .flow {{ font-size: 0.8em; color: #3498db; }}
            </style>
        </head>
        <body>
            <h2>🚗 雪隧即時路況監控</h2>
            <p>最後更新：{time_str}</p>
        """
        for direction, lanes in results.items():
            html += f'<div class="card"><h3>{direction}</h3>'
            for l in lanes:
                html += f'<div class="lane-box"><div>{l["name"]}</div><div class="speed">{l["speed"]}</div><div class="flow">載運量:{l["flow"]}</div></div>'
            html += '</div>'
        html += "</body></html>"
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
            
    except Exception as e:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"<html><body><h1>發生錯誤</h1><p>{str(e)}</p></body></html>")

if __name__ == "__main__":
    build_web()
