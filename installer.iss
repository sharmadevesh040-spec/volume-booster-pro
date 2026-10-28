; Volume Booster Pro - Inno Setup Script
; Generates a professional single-executable setup wizard: VolumeBoosterPro-Setup.exe

#define MyAppName "Volume Booster Pro"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Volume Booster Pro Team"
#define MyAppURL "https://github.com"
#define MyAppExeName "VolumeBoosterPro.exe"

[Setup]
; App Identity
AppId={{8B13DE38-8CE7-4F68-9A74-D7CB2F082531}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation Path: Install per-user in %LOCALAPPDATA%\Programs (no UAC / admin required)
DefaultDirName={localappdata}\Programs\VolumeBoosterPro
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

; Output settings
OutputDir=dist
OutputBaseFilename=VolumeBoosterPro-Setup
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Branding
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "startmenuicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "startupicon"; Description: "Start automatically with Windows"; GroupDescription: "Windows Integration:"; Flags: checkedonce

[Files]
Source: "dist\VolumeBoosterPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\icon.ico"
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--minimized"; Tasks: startupicon; IconFilename: "{app}\assets\icon.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

