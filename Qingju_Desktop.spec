# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# 第三方复杂库全量采集逻辑
libs = [
    'chromadb', 'pydantic', 'sentence_transformers', 'uvicorn', 'fastapi', 
    'opentelemetry', 'onnxruntime', 'numpy', 'tokenizers'
]
datas, binaries, hiddenimports = [], [], []

for lib in libs:
    d, b, h = collect_all(lib)
    datas += d
    binaries += b
    hiddenimports += h

# 合并原有静态资源
datas += [
    ('admin_frontend/dist', 'admin_frontend/dist'),
    ('setup_api.html', '.'),
    ('rent_agent_backend/data', 'rent_agent_backend/data'),
    ('rent_agent_backend/vector_store', 'rent_agent_backend/vector_store'),
]

block_cipher = None

a = Analysis(
    ['main_desktop.py'],
    pathex=['rent_agent_backend'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        'uvicorn.logging',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan.off',
        'uvicorn.lifespan',
        'starlette.staticfiles'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='数律智检',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='数律智检',
)
