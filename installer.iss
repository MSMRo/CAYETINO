; =============================================================================
; PROYECTO CAYETINO - GUION DE INSTALACIÓN INNO SETUP (installer.iss)
; Genera el instalador ejecutable .exe para distribuir en cualquier PC con Windows
; =============================================================================

#define MyAppName "Cayetino ESP32"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "UPCH - Ing. Biomedica"
#define MyAppExeName "Cayetino_ESP32.exe"

[Setup]
AppId={{E5D9F8A1-4B2C-4A8D-9E1F-7C3B5A6D8E9F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Cayetino_ESP32
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=Instalador_Cayetino_ESP32_v1.0_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableDirPage=no
DisableProgramGroupPage=no
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Archivos principales de la aplicación compilada
Source: "dist\Cayetino_ESP32\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Cayetino_ESP32\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Código de firmware y esquemáticos de referencia
Source: "FIRMWARES\*"; DestDir: "{app}\FIRMWARES"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\{#MyAppName}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
