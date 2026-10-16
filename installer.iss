; installer.iss - Inno Setup script for Edge Course Checker
; Build the exe first (build.ps1), then compile this with ISCC.exe:
;   ISCC.exe installer.iss
; The setup is written to .\output\

#define MyAppName      "Edge Course Checker"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "devFazla"
#define MyAppURL       "https://devfazla.com"
#define MyAppExeName   "EdgeCourseChecker.exe"

[Setup]
AppId={{8A6E1B2C-3D4E-5F60-7A8B-9C0D1E2F3A4B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=EdgeCourseChecker-Setup-{#MyAppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
; Smooth in-place upgrade: close a running old app, don't relaunch automatically.
; User data (settings.json, input\, results\) is left untouched so the new
; version merges over the old install.
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; If you switch the spec to one-folder, use instead:
; Source: "dist\EdgeCourseChecker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; WorkingDir is {app} so the input/ and results/ folders are created next to the app.
Name: "{group}\{#MyAppName}";         Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";   Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
