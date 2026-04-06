"""
Client Agent Script - Thu thập CPU/RAM metrics và gửi lên Server qua WebSocket.

Chạy script:
    python client_agent.py --client-id "client_1" --server ws://192.168.137.1:8000

Hoặc sử dụng giá trị mặc định:
    python client_agent.py
"""

import asyncio
import json
import psutil
import websockets
from datetime import datetime
import argparse
import socket
import sys


class MetricsCollector:
    """
    Thu thập system metrics (CPU, RAM) từ máy hiện tại.
    """
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Lấy CPU usage percentage."""
        return psutil.cpu_percent(interval=0.1)
    
    @staticmethod
    def get_ram_usage() -> float:
        """Lấy RAM usage percentage."""
        ram = psutil.virtual_memory()
        return ram.percent
    
    @staticmethod
    def get_metrics() -> dict:
        """Lấy tất cả metrics."""
        return {
            "cpu": MetricsCollector.get_cpu_usage(),
            "ram": MetricsCollector.get_ram_usage(),
            "timestamp": datetime.now().isoformat()
        }


class WebSocketClient:
    """
    WebSocket client để kết nối tới server và gửi metrics.
    """
    
    def __init__(self, client_id: str, server_url: str, interval: int = 1):
        """
        Initialize WebSocket client.
        
        Args:
            client_id: Client identifier
            server_url: WebSocket server URL (e.g., ws://192.168.137.1:8000)
            interval: Interval in seconds to send metrics (default: 1)
        """
        self.client_id = client_id
        self.server_url = f"{server_url}/ws/{client_id}"
        self.interval = interval
        self.websocket = None
        self.connected = False
        self.collector = MetricsCollector()
    
    async def connect(self):
        """
        Kết nối tới WebSocket server.
        """
        max_retries = 5
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"🔗 Đang kết nối tới server: {self.server_url}...")
                self.websocket = await websockets.connect(self.server_url)
                self.connected = True
                print(f"✅ Client {self.client_id} đã kết nối thành công!")
                return True
                
            except Exception as e:
                print(f"⚠️ Lỗi kết nối (lần {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Chờ {retry_delay} giây trước khi thử lại...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"❌ Không thể kết nối sau {max_retries} lần thử!")
                    return False
    
    async def send_metrics(self):
        """
        Gửi metrics lên server mỗi {interval} giây.
        """
        while self.connected:
            try:
                # Lấy metrics
                metrics = self.collector.get_metrics()
                
                # Convert thành JSON
                json_data = json.dumps(metrics)
                
                # Gửi
                await self.websocket.send(json_data)
                print(f"📤 [{self.client_id}] Gửi: CPU={metrics['cpu']:.1f}% | RAM={metrics['ram']:.1f}%")
                
                # Nhận confirmation từ server (optional)
                try:
                    response = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=2.0
                    )
                    print(f"📥 [{self.client_id}] Server response: {response}")
                except asyncio.TimeoutError:
                    pass  # Không nhận được response, tiếp tục
                
            except websockets.exceptions.ConnectionClosed:
                print(f"❌ [{self.client_id}] Mất kết nối với server!")
                self.connected = False
                break
                
            except Exception as e:
                print(f"⚠️ [{self.client_id}] Lỗi khi gửi metrics: {e}")
                self.connected = False
                break
            
            # Chờ trước khi gửi lần tiếp theo
            await asyncio.sleep(self.interval)
    
    async def run(self):
        """
        Chạy client: kết nối và gửi metrics liên tục.
        """
        # Kết nối
        if not await self.connect():
            return
        
        try:
            # Gửi metrics liên tục
            await self.send_metrics()
            
        except KeyboardInterrupt:
            print(f"\n🛑 [{self.client_id}] Dừng bởi người dùng")
        except Exception as e:
            print(f"❌ [{self.client_id}] Error: {e}")
        finally:
            await self.disconnect()
    
    async def disconnect(self):
        """
        Đóng kết nối.
        """
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print(f"🔌 [{self.client_id}] Đã đóng kết nối")


async def main():
    """
    Main function - Parse arguments và chạy client.
    """
    parser = argparse.ArgumentParser(
        description="WebSocket Client Agent để gửi system metrics"
    )
    
    parser.add_argument(
        "--client-id",
        type=str,
        default=socket.gethostname(),  # Sử dụng hostname làm client_id mặc định
        help="Client identifier (default: hostname của máy)"
    )
    
    parser.add_argument(
        "--server",
        type=str,
        default="ws://192.168.137.1:8000",
        help="WebSocket server URL (default: ws://192.168.137.1:8000)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=1,
        help="Interval in seconds to send metrics (default: 1)"
    )
    
    args = parser.parse_args()
    
    # Print thông tin khởi động
    print("=" * 60)
    print("🚀 WebSocket Metrics Client Agent")
    print("=" * 60)
    print(f"Client ID: {args.client_id}")
    print(f"Server: {args.server}")
    print(f"Gửi metrics mỗi: {args.interval} giây")
    print("=" * 60)
    
    # Khởi tạo và chạy client
    client = WebSocketClient(
        client_id=args.client_id,
        server_url=args.server,
        interval=args.interval
    )
    
    await client.run()


if __name__ == "__main__":
    # Chạy async main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt!")
        sys.exit(0)
