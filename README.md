# Thay 192.168.1.100 bằng IP server của bạn
python client_agent.py --client-id "TestClient"

python client_agent.py --server ws://172.16.49.15:8000/api --client-id "TestClient"

curl http://172.16.49.15:8000/api/health
