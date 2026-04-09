import sys, os
sys.path.insert(0, os.path.abspath('backend'))
import base64
import json
import time
import requests
from pathlib import Path

IMAGE_PATH = "test_contract.png"

with open(IMAGE_PATH, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

import socket
print("Waiting for port 8001 to be ready...")
while True:
    try:
        with socket.create_connection(("127.0.0.1", 8001), timeout=1) as s:
            break
    except OSError:
        time.sleep(1)
print("Server is Ready!")

b64 = b64 + " " # 强行扰动 MD5 绕开缓存

results = []

def run_test(test_id):
    results.append(f"=== Test {test_id} ===")
    try:
        start = time.time()
        resp = requests.post(
            "http://127.0.0.1:8001/api/analyze",
            json={"images": [b64]},
            timeout=120
        )
        elapsed = time.time() - start
        
        results.append(f"HTTP 状态码: {resp.status_code}")
        results.append(f"请求耗时: {elapsed:.2f}s")
        return elapsed
    except Exception as e:
        results.append(f"❌ 运行错误: {e}")
        return 120

print("Running Test 1 (Cold Start expected ~40s)")
t1 = run_test(1)

print("Running Test 2 (Cache Hit expected <2s)")
t2 = run_test(2)

results.append("\n=== 耗时对比 ===")
results.append(f"第一次耗时: {t1:.2f}s")
results.append(f"第二次耗时: {t2:.2f}s")

Path("api_analyze_opt_result.txt").write_text("\n".join(results), encoding="utf-8")
print("Done")
