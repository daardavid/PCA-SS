@echo off
setlocal EnableExtensions
rem Si quieres usar ✓, descomenta la siguiente línea y guarda el archivo en UTF-8 con BOM:
rem chcp 65001 >nul

rem Asegura que todo corra relativo a la carpeta del script
pushd "%~dp0"

echo ==============================================
echo   PCAPP - Test Build Script (Quick Test)
echo ==============================================
echo.

echo [TEST] Verificando archivos de configuracion...

if not exist "PCAPP.spec" (
  echo [ERROR] No se encontro PCAPP.spec
  goto :end_error
) else (
  echo [OK] PCAPP.spec encontrado
)

if not exist "PCAPP-Setup.iss" (
  echo [ERROR] No se encontro PCAPP-Setup.iss
  goto :end_error
) else (
  echo [OK] PCAPP-Setup.iss encontrado
)

if not exist "pca_gui.py" (
  echo [ERROR] No se encontro pca_gui.py (archivo principal)
  goto :end_error
) else (
  echo [OK] pca_gui.py encontrado
)

echo.
echo [TEST] Verificando Python en PATH...
where python >nul 2>&1 || where py >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro Python en PATH
  goto :end_error
)

for %%P in (python,py) do ( %%P --version 2>nul && set "PYEXE=%%P" )
echo Usando: %PYEXE%

echo.
echo [TEST] Verificando dependencias de Python...
%PYEXE% -c "import tkinter, pandas, matplotlib, sklearn, numpy" 2>nul
if errorlevel 1 (
  echo [ERROR] Faltan dependencias. Ejecuta: pip install -r requirements.txt
  goto :end_error
) else (
  echo [OK] Dependencias principales encontradas
)

echo.
echo [OK] Estructura correcta. Puedes ejecutar: build.bat
goto :eof

:end_error
pause
exit /b 1
