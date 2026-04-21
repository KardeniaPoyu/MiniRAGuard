"""
数律智检 · 启动器
------------------
职责：
  1. 读取/写入 API Key 配置（存于用户主目录，软件重装不丢失）
  2. 在后台静默启动 FastAPI 后端（使用便携 Python 环境）
  3. 调用 pywebview 打开原生窗口展示 Web UI
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import webbrowser

# ── 路径解析（兼容开发环境与安装后的生产路径）──────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
SETUP_PAGE = os.path.join(BASE_DIR, "setup_api.html")
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".shulv_config.json")

# 便携 Python 解释器路径（构建时由安装脚本写入）
PYTHON_EXE = os.path.join(BASE_DIR, "python", "python.exe")
if not os.path.exists(PYTHON_EXE):
    # 开发模式：使用系统 Python
    PYTHON_EXE = sys.executable

# ── 配置管理 ──────────────────────────────────────────────────────────────
def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(data: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── 端口工具 ──────────────────────────────────────────────────────────────
def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def wait_for_port(port: int, timeout: float = 30.0) -> bool:
    """轮询等待后端端口就绪"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False

# ── 后端进程管理 ──────────────────────────────────────────────────────────
_backend_proc = None

def start_backend(port: int, api_key: str) -> None:
    global _backend_proc
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = api_key
    env["PORT"] = str(port)

    # 使用便携 Python 启动后端，-m 方式确保路径隔离
    _backend_proc = subprocess.Popen(
        [
            PYTHON_EXE, "-m", "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--log-level", "error",
        ],
        cwd=BACKEND_DIR,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW,  # 不弹黑窗口
    )

# ── pywebview GUI ─────────────────────────────────────────────────────────
class JSApi:
    """暴露给引导页 JavaScript 使用的 Python 接口"""
    def __init__(self):
        self.window = None  # 由外部注入

    def save_api_key(self, key: str) -> dict:
        if not key or len(key.strip()) < 10:
            return {"status": "error", "message": "API Key 格式无效"}
        cfg = load_config()
        cfg["DEEPSEEK_API_KEY"] = key.strip()
        save_config(cfg)
        return {"status": "success"}

    def get_status(self) -> dict:
        cfg = load_config()
        return {"has_key": bool(cfg.get("DEEPSEEK_API_KEY"))}


def run_with_webview(start_url: str, api: JSApi):
    import webview
    win = webview.create_window(
        "数律智检 - 基层治理风险研判平台",
        url=start_url,
        width=1440,
        height=900,
        min_size=(1200, 800),
        background_color="#0f172a",
        confirm_close=True,
    )
    api.window = win
    win.expose(api)
    webview.start(debug=False)


def run_with_browser(start_url: str):
    """降级方案：直接使用系统浏览器（无 pywebview 时使用）"""
    webbrowser.open(start_url)
    input("系统已在浏览器中打开，按 Enter 键退出程序...")


# ── 主流程 ────────────────────────────────────────────────────────────────
def main():
    config = load_config()
    api_key = config.get("DEEPSEEK_API_KEY", "")

    api = JSApi()

    if not api_key:
        # ── 首次运行：显示配置引导页 ──────────────────────────────────────
        setup_url = "file:///" + SETUP_PAGE.replace("\\", "/")

        try:
            run_with_webview(setup_url, api)
        except ImportError:
            # pywebview 未安装时降级到浏览器
            webbrowser.open(setup_url)

        # 引导页关闭后，重新读取配置
        config = load_config()
        api_key = config.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            return  # 用户未填写，直接退出

    # ── 正常运行：启动后端 + 打开主界面 ─────────────────────────────────
    port = find_free_port()

    backend_thread = threading.Thread(
        target=start_backend, args=(port, api_key), daemon=True
    )
    backend_thread.start()

    if not wait_for_port(port, timeout=30):
        import tkinter.messagebox as mb
        mb.showerror("启动失败", "后端服务启动超时，请重新运行程序。")
        return

    main_url = f"http://127.0.0.1:{port}/login"

    try:
        run_with_webview(main_url, api)
    except ImportError:
        run_with_browser(main_url)

    # 清理后端进程
    if _backend_proc:
        _backend_proc.terminate()


if __name__ == "__main__":
    main()
