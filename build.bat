@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo    PCAPP - Build Script
echo ===============================================
echo.

:: Verificar que estamos en el directorio correcto
if not exist "pca_gui.py" (
    echo ERROR: No se encontro pca_gui.py en el directorio actual
    echo Asegurate de ejecutar este script desde la carpeta del proyecto
    pause
    exit /b 1
)

:: Verificar dependencias
echo [1/6] Verificando dependencias...
python -c "import tkinter, pandas, matplotlib, sklearn, numpy, seaborn, openpyxl, PIL, yaml" 2>nul
if errorlevel 1 (
    echo ERROR: Faltan dependencias de Python
    echo Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

:: Verificar PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: No se pudo instalar PyInstaller
        pause
        exit /b 1
    )
)

:: Limpiar directorios anteriores
echo [2/6] Limpiando directorios anteriores...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "Output" rmdir /s /q "Output"
if exist "__pycache__" rmdir /s /q "__pycache__"

:: Crear directorio de salida
mkdir "Output" 2>nul

:: Compilar con PyInstaller
echo [3/6] Compilando aplicacion con PyInstaller...
echo Esto puede tomar varios minutos...
pyinstaller PCAPP.spec --clean --noconfirm

if errorlevel 1 (
    echo ERROR: Fallo la compilacion con PyInstaller
    echo Revisa los errores arriba
    pause
    exit /b 1
)

:: Verificar que se genero el ejecutable
if not exist "dist\PCAPP\PCAPP.exe" (
    echo ERROR: No se genero el ejecutable
    pause
    exit /b 1
)

:: Copiar archivos adicionales
echo [4/6] Copiando archivos adicionales...
copy "README.md" "dist\PCAPP\" >nul 2>&1
copy "requirements.txt" "dist\PCAPP\" >nul 2>&1

:: Crear LICENSE.txt si no existe
if not exist "LICENSE.txt" (
    echo Creando LICENSE.txt basico...
    (
    echo MIT License
    echo.
    echo Copyright ^(c^) 2024 David Armando Abreu Rosique
    echo.
    echo Permission is hereby granted, free of charge, to any person obtaining a copy
    echo of this software and associated documentation files ^(the "Software"^), to deal
    echo in the Software without restriction, including without limitation the rights
    echo to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    echo copies of the Software, and to permit persons to whom the Software is
    echo furnished to do so, subject to the following conditions:
    echo.
    echo The above copyright notice and this permission notice shall be included in all
    echo copies or substantial portions of the Software.
    ) > LICENSE.txt
)
copy "LICENSE.txt" "dist\PCAPP\" >nul 2>&1

:: Probar el ejecutable
echo [5/6] Probando el ejecutable generado...
echo Iniciando aplicacion por 5 segundos para verificar que funciona...
start "" "dist\PCAPP\PCAPP.exe"
timeout /t 5 /nobreak >nul
taskkill /f /im "PCAPP.exe" 2>nul

:: Crear instalador con Inno Setup
echo [6/6] Creando instalador con Inno Setup...

:: Buscar Inno Setup en ubicaciones comunes
set "INNO_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set "INNO_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"

if "!INNO_PATH!"=="" (
    echo ADVERTENCIA: No se encontro Inno Setup
    echo Descargalo desde: https://jrsoftware.org/isinfo.php
    echo.
    echo El ejecutable se encuentra en: dist\PCAPP\PCAPP.exe
    echo Puedes crear el instalador manualmente ejecutando PCAPP-Setup.iss
) else (
    echo Encontrado Inno Setup en: !INNO_PATH!
    "!INNO_PATH!" "PCAPP-Setup.iss"
    
    if errorlevel 1 (
        echo ADVERTENCIA: Error al crear el instalador
        echo El ejecutable se encuentra en: dist\PCAPP\
    ) else (
        echo.
        echo ===============================================
        echo           BUILD COMPLETADO EXITOSAMENTE
        echo ===============================================
        echo.
        echo Archivos generados:
        echo - Aplicacion: dist\PCAPP\PCAPP.exe
        echo - Instalador: Output\PCAPP-Setup-1.0.0.exe
        echo.
        
        :: Mostrar tamanos de archivo
        for %%F in ("dist\PCAPP\PCAPP.exe") do (
            set size=%%~zF
            set /a sizeMB=!size!/1024/1024
            echo Tamaño del ejecutable: !sizeMB! MB
        )
        
        for %%F in ("Output\PCAPP-Setup-1.0.0.exe") do (
            set size=%%~zF
            set /a sizeMB=!size!/1024/1024
            echo Tamaño del instalador: !sizeMB! MB
        )
        
        echo.
        echo Para distribuir: usa el archivo del instalador
        echo Para testing: usa directamente el ejecutable
    )
)

echo.
echo ===============================================
pause
