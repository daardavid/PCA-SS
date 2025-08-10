; PCAPP-Setup.iss
; Script de Inno Setup para PCAPP
; Versión adaptada para aplicación Python/Tkinter

[Setup]
; Identificación única de la aplicación
AppId={{8E7F2A1B-4C3D-4E5F-8901-PCA234567890}}
AppName=PCAPP
AppVersion=1.0.0
AppVerName=PCAPP 1.0.0
AppPublisher=Instituto de Investigaciones Económicas UNAM
AppPublisherURL=https://github.com/daardavid/PCA-SS
AppSupportURL=https://github.com/daardavid/PCA-SS/issues  
AppUpdatesURL=https://github.com/daardavid/PCA-SS/releases
AppCopyright=Copyright (C) 2024 David Armando Abreu Rosique

; Configuración de instalación
DefaultDirName={autopf}\PCAPP
DefaultGroupName=PCAPP
AllowNoIcons=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=README.md
OutputDir=Output
OutputBaseFilename=PCAPP-Setup-1.0.0
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\PCAPP.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

; Permisos - instalación por usuario (sin admin)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1
Name: "associate"; Description: "Asociar archivos .json de proyectos PCA"; GroupDescription: "Asociaciones de archivo:"

[Files]
; Aplicación principal y dependencias
Source: "dist\PCAPP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentación
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme
; Datos de ejemplo (opcional)
Source: "Fortun 500\*.xlsx"; DestDir: "{app}\ejemplos\Fortune500"; Flags: ignoreversion recursesubdirs; Excludes: "*.tmp,*.bak"
Source: "Programa Socioeconómicos\*.xlsx"; DestDir: "{app}\ejemplos\Socioeconomicos"; Flags: ignoreversion recursesubdirs; Excludes: "*.tmp,*.bak"

[Registry]
; Asociación de archivos .json para proyectos PCA
Root: HKA; Subkey: "Software\Classes\.pcaproject"; ValueType: string; ValueName: ""; ValueData: "PCAProject"; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\PCAProject"; ValueType: string; ValueName: ""; ValueData: "Proyecto PCAPP"; Flags: uninsdeletekey; Tasks: associate  
Root: HKA; Subkey: "Software\Classes\PCAProject\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\PCAPP.exe,0"; Tasks: associate
Root: HKA; Subkey: "Software\Classes\PCAProject\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\PCAPP.exe"" ""%1"""; Tasks: associate

[Icons]
; Menú de inicio
Name: "{group}\PCAPP"; Filename: "{app}\PCAPP.exe"; WorkingDir: "{app}"
Name: "{group}\Manual de Usuario"; Filename: "{app}\README.md"
Name: "{group}\Ejemplos"; Filename: "{app}\ejemplos"
Name: "{group}\{cm:UninstallProgram,PCAPP}"; Filename: "{uninstallexe}"

; Escritorio (opcional)
Name: "{autodesktop}\PCAPP"; Filename: "{app}\PCAPP.exe"; WorkingDir: "{app}"; Tasks: desktopicon

; Barra de tareas rápida (Windows 7 y anteriores)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\PCAPP"; Filename: "{app}\PCAPP.exe"; WorkingDir: "{app}"; Tasks: quicklaunchicon

[Run]
; Ejecutar aplicación después de instalación
Filename: "{app}\PCAPP.exe"; Description: "{cm:LaunchProgram,PCAPP}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpiar datos de usuario al desinstalar (opcional)
Type: filesandordirs; Name: "{userappdata}\PCAPP"

[Code]
// Verificaciones antes de la instalación
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Verificar Windows de 64 bits
  if not IsWin64 then begin
    MsgBox('Esta aplicación requiere Windows de 64 bits.', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  
  // Verificar versión mínima de Windows (Windows 10)
  if not (GetWindowsVersion >= $0A000000) then begin
    if MsgBox('Esta aplicación está optimizada para Windows 10 o superior. ¿Desea continuar con la instalación?', 
              mbConfirmation, MB_YESNO) = IDNO then begin
      Result := False;
    end;
  end;
end;

// Configuración después de la instalación
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    // Crear directorio de configuración de usuario
    CreateDir(ExpandConstant('{userappdata}\PCAPP'));
    CreateDir(ExpandConstant('{userappdata}\PCAPP\projects'));
    CreateDir(ExpandConstant('{userappdata}\PCAPP\logs'));
  end;
end;

// Información al desinstalar
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if MsgBox('¿Está seguro de que desea desinstalar PCAPP?' + #13#10 + 
            'Se conservarán sus proyectos guardados en Documentos.', 
            mbConfirmation, MB_YESNO) = IDNO then
    Result := False;
end;
