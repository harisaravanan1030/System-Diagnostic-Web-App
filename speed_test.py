import speedtest
import datetime

def run_speed_test():
    try:
        # Enforcing secure=True uses HTTPS, which often bypasses ISP HTTP throttling and is more accurate.
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        
        # Download (convert to Mbps, use multiple threads explicitly)
        download_speed = st.download(threads=None) / 10**6
        
        # Upload (convert to Mbps, use multiple threads)
        upload_speed = st.upload(threads=None, pre_allocate=False) / 10**6
        
        # Ping
        ping = st.results.ping
        
        server_info = st.results.server
        isp = st.results.client.get('isp', 'Unknown ISP')
        location = f"{server_info.get('name', 'Unknown')}, {server_info.get('country', 'Unknown')}"
        
        now = datetime.datetime.now()
        
        return {
            "success": True,
            "download": round(download_speed, 2),
            "upload": round(upload_speed, 2),
            "ping": round(ping, 2),
            "isp": isp,
            "server": location,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
