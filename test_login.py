import httpx
import base64
import json

def test_login():
    with open("test_pfp.jpg", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    url = "http://localhost:8888/login"
    payload = {"image": img_b64}
    
    try:
        r = httpx.post(url, json=payload, timeout=120)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
