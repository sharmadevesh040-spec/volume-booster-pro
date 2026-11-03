; Volume Booster Pro - Professional Windows Inno Setup Script
; Generates: VolumeBoosterPro-Setup.exe

#define MyAppName "Volume Booster Pro"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Volume Booster Pro Team"
#define MyAppURL "https://github.com"
#define MyAppExeName "VolumeBoosterPro.exe"
#define MyAppGuid "{8B13DE38-8CE7-4F68-9A74-D7CB2F082531}"

[Setup]
; Application Identity
AppId={{#MyAppGuid}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation Target: Defaults to Program Files for standard commercial installation
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; User Privileges: Admin required for Program Files, with non-admin override supported
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline dialog
UsedUserAreasWarning=no

; Architecture & Platform Requirements (Windows 10 / 11 64-bit)
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

; Installer Branding & Wizard Artwork
SetupIconFile=assets\icon.ico
WizardImageFile=assets\wizard_large.bmp
WizardSmallImageFile=assets\wizard_small.bmp
WizardStyle=modern

; Output Configuration
OutputDir=dist
OutputBaseFilename=VolumeBoosterPro-Setup
Compression=lzma2/ultra64
SolidCompression=yes

; Uninstaller & Upgrade Configuration
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\assets\icon.ico
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
CloseApplications=yes
RestartApplications=no

; End User License Agreement
LicenseFile=LICENSE.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "startmenuicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "integrate_apo"; Description: "Enable Equalizer APO integration (system-wide zero-latency boost)"; GroupDescription: "Audio Engine Configuration:"; Check: IsEqualizerApoInstalled
Name: "startupicon"; Description: "Start Volume Booster Pro automatically with Windows"; GroupDescription: "Windows Integration:"; Flags: unchecked

[Files]
; Main application binaries
Source: "dist\VolumeBoosterPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\icon.ico"; Comment: "System-Wide Audio Enhancer & DSP Equalizer"
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon; IconFilename: "{app}\assets\icon.ico"; Comment: "System-Wide Audio Enhancer & DSP Equalizer"

[Registry]
; Windows startup option, disabled by default (configured only if user checks startupicon task)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"" --minimized"; Tasks: startupicon; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Gracefully terminate running instances during uninstall
Filename: "taskkill.exe"; Parameters: "/f /im {#MyAppExeName}"; RunOnceId: "KillApp"; Flags: runhidden

[UninstallDelete]
Type: files; Name: "{app}\assets\*"
Type: dirifempty; Name: "{app}\assets"
Type: files; Name: "{app}\*"
Type: dirifempty; Name: "{app}"

[Code]
var
  AudioEnginePage: TOutputMsgWizardPage;
  ApoDetected: Boolean;
  ApoDir: String;

// Check if Equalizer APO is installed
function DetectEqualizerApo(): Boolean;
var
  InstallPath: String;
begin
  Result := False;
  ApoDir := '';
  if RegQueryStringValue(HKLM, 'SOFTWARE\EqualizerAPO', 'InstallPath', InstallPath) then
  begin
    if DirExists(InstallPath) and FileExists(InstallPath + '\EqualizerAPO.dll') then
    begin
      ApoDir := InstallPath;
      Result := True;
      Exit;
    end;
  end;
  if DirExists('C:\Program Files\EqualizerAPO') and FileExists('C:\Program Files\EqualizerAPO\EqualizerAPO.dll') then
  begin
    ApoDir := 'C:\Program Files\EqualizerAPO';
    Result := True;
    Exit;
  end;
  if DirExists('C:\Program Files (x86)\EqualizerAPO') and FileExists('C:\Program Files (x86)\EqualizerAPO\EqualizerAPO.dll') then
  begin
    ApoDir := 'C:\Program Files (x86)\EqualizerAPO';
    Result := True;
    Exit;
  end;
end;

function IsEqualizerApoInstalled(): Boolean;
begin
  Result := ApoDetected;
end;

// Check if VC++ 2015-2022 x64 Redistributable is installed
function IsVCRedistInstalled(): Boolean;
var
  Installed: Cardinal;
begin
  Result := False;
  if RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Installed', Installed) then
  begin
    if Installed = 1 then
      Result := True;
  end;
end;

procedure InitializeWizard();
var
  MsgText: String;
begin
  ApoDetected := DetectEqualizerApo();

  // Create custom Audio Engine Setup information page
  AudioEnginePage := CreateOutputMsgPage(
    wpSelectTasks,
    'Audio Engine Architecture & Diagnostics',
    'Volume Booster Pro System-Wide Audio Integration',
    ''
  );

  if ApoDetected then
  begin
    MsgText := 'Equalizer APO Status: DETECTED' + #13#10 +
               'Location: ' + ApoDir + #13#10#13#10 +
               'Volume Booster Pro will configure native kernel-level audio processing via audiodg.exe. ' +
               'This enables zero-latency, zero-CPU amplification across all Windows applications (Chrome, YouTube, Spotify, VLC, Games).' + #13#10#13#10 +
               'Safety Notice: Your existing audio device configuration will NOT be overwritten without creating a backup copy (config.txt.bak).' + #13#10 +
               'You can toggle or calibrate amplification at any time inside the app.';
  end
  else
  begin
    MsgText := 'Equalizer APO Status: NOT INSTALLED' + #13#10#13#10 +
               'Volume Booster Pro will operate using its high-precision Built-in Real-Time DSP Audio Engine.' + #13#10#13#10 +
               'For kernel-level zero-latency amplification, you can install Equalizer APO anytime using the 1-click Setup button inside Volume Booster Pro.' + #13#10#13#10 +
               'No system audio drivers or default playback devices will be modified during setup.';
  end;

  AudioEnginePage.MsgLabel.Caption := MsgText;
end;

function InitializeSetup(): Boolean;
var
  PrevVersion: String;
begin
  Result := True;

  // Check 64-bit Windows requirement
  if not Is64BitInstallMode then
  begin
    MsgBox('Volume Booster Pro requires a 64-bit edition of Windows 10 or Windows 11.', mbCriticalError, MB_OK);
    Result := False;
    Exit;
  end;

  // Existing installation detection for smooth upgrade
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppGuid}_is1', 'DisplayVersion', PrevVersion) or
     RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppGuid}_is1', 'DisplayVersion', PrevVersion) then
  begin
    Log('Detected existing installation version: ' + PrevVersion);
  end;

  // Runtime dependency check
  if not IsVCRedistInstalled() then
  begin
    Log('VC++ 2015-2022 x64 Redistributable check: Not detected in registry, bundled PyInstaller runtime will be utilized.');
  end;
end;

// Safe integration with Equalizer APO after files are copied
procedure IntegrateWithEqualizerApo();
var
  ConfigPath, BackupPath, ProfilePath: String;
  FileLines: TArrayOfString;
  I: Integer;
  AlreadyIntegrated: Boolean;
begin
  if (not ApoDetected) or (ApoDir = '') then Exit;

  ConfigPath := ApoDir + '\config\config.txt';
  BackupPath := ApoDir + '\config\config.txt.bak';
  ProfilePath := ApoDir + '\config\VolumeBoosterPro.txt';

  // 1. Create default profile if not exists
  if not FileExists(ProfilePath) then
  begin
    SaveStringToFile(ProfilePath,
      '# Volume Booster Pro Audio Profile' + #13#10 +
      'Device: all' + #13#10 +
      'Preamp: +1.94 dB' + #13#10 +
      'Filter 1: ON LSC Fc 150.0 Hz Gain +1.50 dB' + #13#10 +
      'Filter 2: ON PK Fc 2200.0 Hz Gain +2.00 dB Q 1.00' + #13#10 +
      'Filter 3: ON HSC Fc 7000.0 Hz Gain +1.00 dB' + #13#10,
      False);
  end;

  // 2. Safe atomic update of config.txt with backup
  if FileExists(ConfigPath) then
  begin
    if LoadStringsFromFile(ConfigPath, FileLines) then
    begin
      AlreadyIntegrated := False;
      for I := 0 to GetArrayLength(FileLines) - 1 do
      begin
        if Pos('VolumeBoosterPro.txt', FileLines[I]) > 0 then
        begin
          AlreadyIntegrated := True;
          Break;
        end;
      end;

      if not AlreadyIntegrated then
      begin
        // Create backup if not already present
        if not FileExists(BackupPath) then
        begin
          CopyFile(ConfigPath, BackupPath, False);
        end;

        // Append include directive safely
        SetArrayLength(FileLines, GetArrayLength(FileLines) + 2);
        FileLines[GetArrayLength(FileLines) - 2] := '';
        FileLines[GetArrayLength(FileLines) - 1] := 'Include: VolumeBoosterPro.txt';
        SaveStringsToFile(ConfigPath, FileLines, False);
        Log('Equalizer APO config.txt successfully updated with Include: VolumeBoosterPro.txt');
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('integrate_apo') then
    begin
      try
        IntegrateWithEqualizerApo();
      except
        Log('Warning: Could not configure Equalizer APO integration automatically.');
      end;
    end;
  end;
end;

// Uninstaller: Optional settings removal and clean APO rollback
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  SettingsDir, ConfigPath, ProfilePath: String;
  FileLines, CleanLines: TArrayOfString;
  I, CleanIdx: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // 1. Audio Configuration Rollback
    if DetectEqualizerApo() and (ApoDir <> '') then
    begin
      ConfigPath := ApoDir + '\config\config.txt';
      ProfilePath := ApoDir + '\config\VolumeBoosterPro.txt';

      if FileExists(ConfigPath) and LoadStringsFromFile(ConfigPath, FileLines) then
      begin
        SetArrayLength(CleanLines, GetArrayLength(FileLines));
        CleanIdx := 0;
        for I := 0 to GetArrayLength(FileLines) - 1 do
        begin
          if (Pos('VolumeBoosterPro.txt', FileLines[I]) = 0) and (Pos('Volume Booster Pro', FileLines[I]) = 0) then
          begin
            CleanLines[CleanIdx] := FileLines[I];
            CleanIdx := CleanIdx + 1;
          end;
        end;
        SetArrayLength(CleanLines, CleanIdx);
        SaveStringsToFile(ConfigPath, CleanLines, False);
        Log('Cleaned Volume Booster Pro directive from Equalizer APO config.txt');
      end;

      if FileExists(ProfilePath) then
      begin
        DeleteFile(ProfilePath);
      end;
    end;

    // 2. Optional removal of user presets and settings
    SettingsDir := ExpandConstant('{localappdata}\{#MyAppName}');
    if DirExists(SettingsDir) then
    begin
      if MsgBox('Do you want to delete your custom presets and audio settings from this computer?', mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(SettingsDir, True, True, True);
      end;
    end;
  end;
end;
