; ==============================================================
; 数律智检 · Inno Setup 安装脚本
; 用法：在开发机器上使用 Inno Setup Compiler 编译此脚本
;       或由 build_installer.bat 自动调用
; ==============================================================

#define AppName      "数律智检"
#define AppVersion   "1.0.0"
#define AppPublisher "数律智检研发团队"
#define AppURL       "https://github.com/KardeniaPoyu/MiniRAGuard"
#define AppExeName   "数律智检.exe"

[Setup]
; 应用基础信息
AppId={{B8A2F3D4-1C5E-4A9B-8F2D-7E6C3B9A1D5F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; 安装路径（默认写入 Program Files）
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes

; 输出配置
OutputDir=..\dist_installer
OutputBaseFilename=数律智检_Setup_v{#AppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes

; 最低 Windows 版本：Windows 10 1903+
MinVersion=10.0.18362
PrivilegesRequired=admin
WizardStyle=modern
WizardResizable=yes

; 启用卸载
Uninstallable=yes
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
CreateUninstallRegKey=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: checked
Name: "startmenuicon"; Description: "创建开始菜单快捷方式"; GroupDescription: "附加任务:"; Flags: checked

[Files]
; ── 便携式 Python 环境（含所有依赖，由 build_installer.bat 预先生成）──
Source: "..\build\portable_env\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs

; ── 后端代码 ──
Source: "..\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
Excludes: "__pycache__,*.pyc,vector_store,data"

; ── 前端静态资源 ──
Source: "..\admin_frontend\dist\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs createallsubdirs

; ── 启动器 ──
Source: "launcher.py"; DestDir: "{app}"; Flags: ignoreversion

; ── 初始化引导页 ──
Source: "..\setup_api.html"; DestDir: "{app}"; Flags: ignoreversion

; ── 编译好的轻量启动器 EXE ──
Source: "assets\launcher.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion

; ── 图标资源 ──
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 桌面快捷方式
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

; 开始菜单
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: startmenuicon
Name: "{group}\卸载 {#AppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon

[Run]
; 安装完成后可选择立即运行
Filename: "{app}\{#AppExeName}"; Description: "立即启动 {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时清除运行时生成的缓存和日志（用户数据在主目录不删除）
Type: filesandordirs; Name: "{app}\backend\__pycache__"
Type: filesandordirs; Name: "{app}\backend\data"
Type: filesandordirs; Name: "{app}\python\__pycache__"
