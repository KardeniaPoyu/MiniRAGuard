import os
import sys
import json
import threading
import time
import uvicorn
import webview
import socket
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 导入现有的后端业务逻辑
# 确保项目根目录和后端文件夹都在 sys.path 中，解决打包后的模块导入问题
base_dir = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys, '_MEIPASS'):
    base_dir = sys._MEIPASS

sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, "rent_agent_backend"))

from rent_agent_backend.main import app as backend_app

# 1. 配置文件管理与资源定位
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".qingju_config.json")

def resource_path(relative_path):
    """ 获取资源的绝对路径，兼容开发环境和 PyInstaller 打包环境 """
    try:
        # PyInstaller 会创建一个临时文件夹并将路径存入 _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# 2. 寻找空闲端口
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

PORT = find_free_port()

# 3. 拦截与设置 API 密钥的逻辑
def start_logic():
    config = load_config()
    
    # 获取并注入 API Key 到环境变量中供业务模块使用
    api_key = config.get("DEEPSEEK_API_KEY")
    if api_key:
        os.environ["DEEPSEEK_API_KEY"] = api_key
    
    # 启动后端服务
    uvicorn.run(backend_app, host="127.0.0.1", port=PORT, log_level="error")

# 4. GUI 控制器
class Api:
    def __init__(self, window):
        self.window = window

    def save_api_key(self, key):
        if not key or len(key) < 10:
            return {"status": "error", "message": "无效的 API 密钥"}
        
        config = load_config()
        config["DEEPSEEK_API_KEY"] = key
        save_config(config)
        os.environ["DEEPSEEK_API_KEY"] = key
        
        # 刷新页面进入主程序
        self.window.load_url(f"http://127.0.0.1:{PORT}/dashboard")
        return {"status": "success"}

def run_app():
    config = load_config()
    api_key = config.get("DEEPSEEK_API_KEY")
    
    # 后端线程化启动
    t = threading.Thread(target=start_logic, daemon=True)
    t.start()

    # 等待后端稍微启动
    time.sleep(1)

    # 初始加载 URL
    if not api_key:
        # 使用资源定位辅助函数
        setup_path = resource_path("setup_api.html")
        formatted_setup_path = setup_path.replace('\\', '/')
        start_url = f"file:///{formatted_setup_path}"
    else:
        start_url = f"http://127.0.0.1:{PORT}/login"

    # 创建窗口
    window = webview.create_window(
        '数律智检 - 基层治理风险研判平台',
        url=start_url,
        width=1440,
        height=900,
        min_size=(1200, 800),
        text_select=True,
        confirm_close=True,
        background_color='#0f172a'
    )

    # 注入 API
    window.expose(Api(window))
    
    webview.start(debug=False)

if __name__ == "__main__":
    # 使用资源定位辅助函数挂载前端静态资源
    dist_path = resource_path(os.path.join("admin_frontend", "dist"))
    if os.path.exists(dist_path):
        backend_app.mount("/", StaticFiles(directory=dist_path, html=True), name="ui")
    else:
        print(f"警告: 未找到静态资源目录 {dist_path}，请确保已运行 npm run build")
    
    run_app()
