# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('admin_frontend/dist', 'admin_frontend/dist'),      # 包含前端界面
        ('setup_api.html', '.'),                            # 包含初始化页面
        ('rent_agent_backend/data', 'rent_agent_backend/data'), # 包含本地数据库
        ('rent_agent_backend/vector_store', 'rent_agent_backend/vector_store'), # 包含AI法条索引
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan.off',
        'uvicorn.lifespan',
        'fastapi',
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
    console=False,                  # 设置为 False，这样启动时不会弹黑窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='admin_frontend/public/favicon.ico' # 如果有图标可以设置
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
