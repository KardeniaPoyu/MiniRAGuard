"""
数律智检 · 启动器 (单窗口高可靠版)
------------------
职责：
  1. 读取/写入 API Key 配置
  2. 统管理 GUI 窗口生命周期（单 start 循环，动态 URL 切换）
  3. 后端进程管理与异步状态同步
"""

import os
import sys
import json
import time
import socket
import threading
import subprocess
import webbrowser
import urllib.parse
import ctypes
from pathlib import Path

# ── 路径解析 ─────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BACKEND_DIR = os.path.join(BASE_DIR, "backend")
SETUP_PAGE = os.path.join(BASE_DIR, "setup_api.html")
LOADING_PAGE = os.path.join(BASE_DIR, "loading.html")
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".shulv_config.json")
BACKEND_LOG = os.path.join(os.path.expanduser("~"), ".shulv_backend.log")
PYTHON_EXE = os.path.join(BASE_DIR, "python", "python.exe")

def get_page_content(path):
    """读取本地 HTML 文件内容"""
    if not os.path.exists(path):
        return f"<html><body><h1>Error: File not found</h1><p>{path}</p></body></html>"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

# ── 配置管理 ──────────────────────────────────────────────────────────────
def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: pass
    return {}

def save_config(data: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── 进程与端口管理 ────────────────────────────────────────────────────────
_backend_proc = None
_target_port = None
_backend_error = None

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def show_error(title, message):
    """使用 Windows 原生 API 弹出错误提示"""
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)

def get_last_log_lines(n=10):
    if os.path.exists(BACKEND_LOG):
        try:
            with open(BACKEND_LOG, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                return "".join(lines[-n:])
        except Exception: pass
    return "无法读取日志文件"

def monitor_backend_process(proc):
    global _backend_error
    proc.wait()
    if proc.returncode != 0:
        error_msg = get_last_log_lines(15)
        _backend_error = f"后端进程意外退出 (代码: {proc.returncode})\n\n最近日志:\n{error_msg}"
        print(_backend_error)

def start_backend_thread(port: int, api_key: str):
    global _backend_proc
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = api_key
    env["PORT"] = str(port)
    
    # 使用独立的命令行控制台（黑框）运行后端，彻底解决由于管道阻塞、无头模式或句柄继承导致的卡死问题
    # 如果后端崩溃，黑框会暂停显示报错信息，方便排查
    cmd_args = [
        "cmd.exe", "/c",
        PYTHON_EXE, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port),
        "||", "pause"
    ]
    
    # 覆盖 PyInstaller 默认的 SW_HIDE，强制让黑框可见
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 1  # 1 = SW_SHOWNORMAL
    
    _backend_proc = subprocess.Popen(
        cmd_args,
        cwd=BACKEND_DIR, env=env, 
        creationflags=subprocess.CREATE_NEW_CONSOLE, 
        close_fds=True,
        startupinfo=startupinfo
    )
    
    # 启动进程监控线程
    threading.Thread(target=monitor_backend_process, args=(_backend_proc,), daemon=True).start()

def wait_for_port(port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _backend_error:
            return False
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(1)
    return False

# ── pywebview GUI ─────────────────────────────────────────────────────────
class JSApi:
    def __init__(self):
        self.window = None

    def save_api_key(self, key: str) -> dict:
        key = key.strip()
        if not key or len(key) < 10:
            return {"status": "error", "message": "API Key 格式无效"}
        cfg = load_config()
        cfg["DEEPSEEK_API_KEY"] = key
        save_config(cfg)
        
        # 立即在后台启动后端
        global _target_port
        _target_port = find_free_port()
        threading.Thread(target=start_backend_thread, args=(_target_port, key), daemon=True).start()
        
        # 启动后端后再导航到加载页
        # 注意：绝不能在 API 回调中直接调用 load_html，否则会破坏 COM 桥接导致后续点击卡死
        def delayed_transition():
            time.sleep(2.0) # 等待前端展示成功动画
            if self.window:
                self.window.load_html(get_page_content(LOADING_PAGE))
                
        threading.Thread(target=delayed_transition, daemon=True).start()
        
        return {"status": "success"}

    def _monitor_backend(self):
        if wait_for_port(_target_port):
            self.window.load_url(f"http://127.0.0.1:{_target_port}/login")
        else:
            msg = _backend_error if _backend_error else "后端启动超时，请检查系统资源或配置。"
            show_error("启动失败", msg)
            self.destroy_window()

    def get_target_port(self) -> int:
        return _target_port

    def open_log(self):
        """打开后端日志文件以便排查"""
        if os.path.exists(BACKEND_LOG):
            os.startfile(BACKEND_LOG)

    def destroy_window(self):
        if self.window: self.window.destroy()

    def load_backend(self, url: str):
        """由宿主进程主动切换 URL，必须异步延迟执行，以确保 JS 回调能成功 return"""
        def delayed_nav():
            import time
            time.sleep(0.5)
            if self.window:
                self.window.load_url(url)
        import threading
        threading.Thread(target=delayed_nav, daemon=True).start()
        return {"status": "success"}

def on_window_loaded(window):
    """窗口启动后的初始化操作"""
    config = load_config()
    api_key = config.get("DEEPSEEK_API_KEY", "")
    
    if api_key:
        # 有 Key，直接启动后端并进入加载页
        global _target_port
        _target_port = find_free_port()
        threading.Thread(target=start_backend_thread, args=(_target_port, api_key), daemon=True).start()
        
        # 启动后端后再导航到带参数的加载页
        # 这里的 JS 会负责监听后端状态并在就绪后跳转
        # 启动后端后再导航到加载页
        window.load_html(get_page_content(LOADING_PAGE))
    else:
        # 无 Key，留在 setup 页（由创建窗口时的初始 URL 决定）
        pass

def main():
    import webview # 延迟导入，防止打包体积异常
    config = load_config()
    api_key = config.get("DEEPSEEK_API_KEY", "")
    
    initial_content = get_page_content(LOADING_PAGE) if api_key else get_page_content(SETUP_PAGE)
    api = JSApi()
    
    window = webview.create_window(
        "数律智检 - 法律风险智能研判平台",
        url=None,
        html=initial_content,
        width=1440, height=900,
        min_size=(1200, 800),
        background_color="#0f172a",
        js_api=api
    )
    api.window = window

    # 启动 webview
    webview.start(on_window_loaded, window, debug=False)

    # 退出清理
    if _backend_proc:
        try:
            if os.name == 'nt':
                subprocess.call(
                    ['taskkill', '/F', '/T', '/PID', str(_backend_proc.pid)],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                _backend_proc.terminate()
        except Exception:
            pass

if __name__ == "__main__":
    main()
