#define MyAppName "Genshin MIDI Bridge"
#define MyAppVersion "1.0.2"
#define MyAppExeName "Genshin-MIDI-Bridge.exe"

[Setup]
AppId={{8A68241B-70C6-4A89-98BD-48CB3BC01DA0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Genshin MIDI Bridge
DefaultGroupName=Genshin MIDI Bridge
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=Genshin-MIDI-Bridge-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Genshin MIDI Bridge"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Genshin MIDI Bridge"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Genshin MIDI Bridge"; Flags: nowait postinstall skipifsilent
