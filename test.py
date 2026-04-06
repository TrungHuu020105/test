import asyncio
import websockets
import json
import psutil

async def stream_metrics():
    # ĐỊA CHỈ IP MÁY A (SERVER)
    uri = "ws://192.168.137.1:8000/ws/Laptop_B" 
    
    print(f"🔗 Đang kết nối tới Server {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Đã kết nối! Đang gửi dữ liệu...")
            while True:
                # Lấy thông số thực tế từ máy B
                payload = {
                    "cpu": psutil.cpu_percent(interval=1), # Lấy mẫu trong 1s
                    "ram": psutil.virtual_memory().percent
                }
                
                # Gửi sang máy A
                await websocket.send(json.dumps(payload))
                
    except Exception as e:
        print(f"❗ Lỗi: {e}")

if __name__ == "__main__":
    asyncio.run(stream_metrics())
