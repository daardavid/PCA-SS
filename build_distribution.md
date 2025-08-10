# Guía de Distribución - PCAPP

## 1. Preparación con PyInstaller

### Instalar PyInstaller
```bash
pip install pyinstaller
```

### Crear archivo spec personalizado
```bash
pyi-makespec --onedir --windowed --name="PCAPP" main.py
```

### Editar el archivo .spec generado
```python
# PCAPP.spec
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/*', 'config/'),
        ('i18n_*.py', '.'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'matplotlib.backends.backend_tkagg',
        'pandas',
        'numpy',
        'sklearn',
        'seaborn',
        'openpyxl',
        'PIL',
        'yaml'
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
    name='PCAPP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico'  # Agrega un icono si tienes
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PCAPP'
)
```

### Compilar la aplicación
```bash
pyinstaller PCAPP.spec
```

## 2. Estructura de distribución resultante

Después de PyInstaller, tendrás:
```
dist/
  PCAPP/
    PCAPP.exe
    _internal/
      ... (todas las dependencias)
    config/
      app_config.yaml
    README.md
    LICENSE.txt
```

## 3. Script de Inno Setup adaptado

### Instalar Inno Setup
Descarga desde: https://jrsoftware.org/isinfo.php

### Archivo PCA-Setup.iss
```innosetup
; PCAPP-Setup.iss
[Setup]
AppId={{8E7F2A1B-4C3D-4E5F-8901-234567890ABC}}
AppName=PCAPP
AppVersion=1.0.0
AppPublisher=Instituto de Investigaciones Económicas UNAM
AppPublisherURL=https://github.com/tuusuario/PCA-SS
AppSupportURL=https://github.com/tuusuario/PCA-SS/issues
AppUpdatesURL=https://github.com/tuusuario/PCA-SS/releases
DefaultDirName={autopf}\PCAPP
DefaultGroupName=PCAPP
UninstallDisplayIcon={app}\PCAPP.exe
OutputBaseFilename=PCAPP-Setup-1.0.0
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
SetupIconFile=app_icon.ico
; Instalación por usuario (sin requerir admin)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\PCAPP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PCAPP"; Filename: "{app}\PCAPP.exe"; IconFilename: "{app}\PCAPP.exe"
Name: "{group}\Manual de Usuario"; Filename: "{app}\README.md"
Name: "{group}\{cm:UninstallProgram,PCAPP}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PCAPP"; Filename: "{app}\PCAPP.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Run]
Filename: "{app}\PCAPP.exe"; Description: "Iniciar PCAPP"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWin64 then begin
    MsgBox('Esta aplicación requiere Windows de 64 bits.', mbError, MB_OK);
    Result := False;
  end;
end;
```

## 4. Script de automatización

### build.bat
```batch
@echo off
echo === Construyendo PCAPP ===

echo Limpiando directorios anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo Compilando con PyInstaller...
pyinstaller PCAPP.spec

if errorlevel 1 (
    echo Error en PyInstaller
    pause
    exit /b 1
)

echo Copiando archivos adicionales...
copy LICENSE.txt dist\PCAPP\
copy README.md dist\PCAPP\

echo Creando instalador con Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" PCAPP-Setup.iss

if errorlevel 1 (
    echo Error en Inno Setup
    pause
    exit /b 1
)

echo === Build completado ===
echo Instalador creado en: Output\PCAPP-Setup-1.0.0.exe
pause
```

## 5. Consideraciones especiales para tu aplicación

### Dependencias de datos
- Tus archivos Excel en `Fortun 500/` y `Programa Socioeconómicos/` pueden incluirse como datos de ejemplo
- Los logs se crearán automáticamente en la instalación del usuario

### Matplotlib en EXE
Agrega al spec:
```python
import matplotlib
datas += matplotlib.get_py2exe_datafiles()
```

### Configuración persistente
Tu sistema de `settings.json` funcionará perfectamente, se guardará en:
- `%APPDATA%\PCA-Socioeconomicos\` (recomendado)
- O en la carpeta de instalación si prefieres

## 6. Distribución final

### GitHub Releases
1. Sube el `.exe` generado
2. Incluye checksums SHA256
3. Documenta requisitos del sistema

### Winget (opcional futuro)
Crear manifiesto para `winget install unam.pca-socioeconomicos`

## 7. Testing checklist

- [ ] VM Windows 10 limpia
- [ ] VM Windows 11 limpia  
- [ ] Instalación sin admin
- [ ] Desinstalación completa
- [ ] Funcionalidad completa post-instalación
- [ ] Archivos de configuración se crean correctamente
- [ ] Exportación de resultados funciona
- [ ] Gráficos matplotlib se muestran correctamente
