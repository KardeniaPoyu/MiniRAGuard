import sys, os
sys.path.insert(0, os.path.abspath('rent_agent_backend'))
import base64
import json
import time
import requests
import traceback
from pathlib import Path

IMAGE_PATH = "test_contract.png"

results = []

def run_test(test_id):
    results.append(f"=== Test {test_id} ===")
    try:
        if not Path(IMAGE_PATH).exists():
             results.append(f"❌ 图片不存在: {IMAGE_PATH}")
             return None, 120
             
        with open(IMAGE_PATH, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        start = time.time()
        resp = requests.post(
            "http://127.0.0.1:8000/api/analyze",
            json={"images": [b64]},
            timeout=120
        )
        elapsed = time.time() - start
        
        results.append(f"HTTP 状态码: {resp.status_code}")
        results.append(f"总耗时: {elapsed:.2f}s")
        
        if resp.status_code == 200:
            result_json = resp.json()
            results.append("JSON 响应成功获取")
            results.append(json.dumps(result_json, ensure_ascii=False, indent=2))
            return result_json, elapsed
        else:
            results.append(f"Error: {resp.text}")
            return None, elapsed
    except Exception as e:
        results.append(f"❌ 运行异常: {e}")
        results.append(traceback.format_exc())
        return None, 120

# Run Test 1
res1, t1 = run_test(1)

# Save results text
Path("api_analyze_result_trace.txt").write_text("\n".join(results), encoding="utf-8")
print("Done")
