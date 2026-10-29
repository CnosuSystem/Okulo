
#define MyAppName "Okulo"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "Cnosu System"
#define MyAppExeName "Okulo.exe"
#define MyAppId "{{7F3A2D91-8C64-4E5B-A217-9D6F0B82C431}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Allow the user to choose per-user or all-users installation
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Installer output
OutputDir=Output
OutputBaseFilename=Okulo-Setup
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
ChangesAssociations=yes

; Uninstaller
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName},0

; Application handling
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "Create a desktop shortcut"; \
    GroupDescription: "Additional shortcuts:"; \
    Flags: unchecked

[Files]
Source: "dist\Okulo\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Okulo"; \
    Filename: "{app}\Okulo.exe"; \
    WorkingDir: "{app}"

Name: "{autodesktop}\Okulo"; \
    Filename: "{app}\Okulo.exe"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon

Name: "{group}\Uninstall Okulo"; \
    Filename: "{uninstallexe}"

[Registry]
; Register .oemf in the appropriate scope:
; HKLM for all users, HKCU for the current user.
Root: HKA; \
    Subkey: "Software\Classes\.oemf"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "Okulo.OEMF"; \
    Flags: uninsdeletevalue

; File type description
Root: HKA; \
    Subkey: "Software\Classes\Okulo.OEMF"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "Okulo OEMF File"; \
    Flags: uninsdeletekey

; Use the first icon embedded in Okulo.exe
Root: HKA; \
    Subkey: "Software\Classes\Okulo.OEMF\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\Okulo.exe,0"

[UninstallDelete]
; Intentionally no blanket deletion of the installation directory.
; Inno Setup removes files installed by this script.
