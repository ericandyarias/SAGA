@echo off
REM Propósito: generar SAGA.exe (PyInstaller) y el instalador (Inno Setup) de un saque.
chcp 65001 >nul
setlocal EnableExtensions
echo ========================================
echo   GENERADOR DE INSTALADOR
echo   SAGA - Sistema Administrativo Gastronomico - Arias
echo ========================================
echo.

cd /d "%~dp0"

if not exist "main.py" (
    echo ERROR: No se encontro main.py
    echo Ejecuta este script desde la carpeta raiz del proyecto.
    pause
    exit /b 1
)

set "PYTHON="
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"

if "%PYTHON%"=="" (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON=python"
)

if "%PYTHON%"=="" (
    where py >nul 2>&1
    if not errorlevel 1 set "PYTHON=py"
)

if "%PYTHON%"=="" (
    for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" set "PYTHON=%%D\python.exe"
    )
)

if "%PYTHON%"=="" (
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo Instala Python desde https://www.python.org/downloads/
    echo Marca "Add Python to PATH" durante la instalacion.
    echo.
    echo Si ya lo instalaste, podes usar: py -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo Usando: %PYTHON%
echo.

echo Dejando datos virgenes para el instalador...
"%PYTHON%" preparar_datos_instalador.py
if errorlevel 1 (
    echo ERROR: No se pudieron preparar los datos.
    pause
    exit /b 1
)
echo.

echo Verificando PyInstaller...
"%PYTHON%" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller no esta instalado. Instalando...
    "%PYTHON%" -m pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: No se pudo instalar PyInstaller
        pause
        exit /b 1
    )
)

echo.
echo Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo.
echo ========================================
echo Construyendo ejecutable...
echo ========================================
"%PYTHON%" -m PyInstaller --clean saga.spec
if errorlevel 1 (
    echo.
    echo ERROR: Fallo al construir el ejecutable
    pause
    exit /b 1
)

if not exist "dist\SAGA.exe" (
    echo.
    echo ERROR: El ejecutable no se genero correctamente
    pause
    exit /b 1
)

echo.
echo Copiando catalogo y datos virgenes a dist\data...
if exist "dist\data" rmdir /s /q "dist\data"
mkdir "dist\data"
xcopy /E /I /Y "data\*" "dist\data\" >nul
if errorlevel 1 (
    echo ERROR: No se pudieron copiar los datos
    pause
    exit /b 1
)

if exist "dist\data\tickets" (
    del /q "dist\data\tickets\*.*" >nul 2>&1
)

echo.
echo Ejecutable construido: dist\SAGA.exe
echo.

set "INNO_SETUP_PATH="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "INNO_SETUP_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "INNO_SETUP_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%INNO_SETUP_PATH%"=="" (
    echo.
    echo FALTA INNO SETUP.
    echo El ejecutable ya esta listo, pero el instalador .exe no se puede compilar.
    echo.
    echo 1. Instala Inno Setup 6 desde https://jrsoftware.org/isdl.php
    echo 2. Volve a ejecutar este script, o abre installer_script.iss y pulsa F9.
    echo.
    echo El instalador final va a quedar en: installer\SAGA_Setup.exe
    echo.
    pause
    exit /b 0
)

if not exist installer mkdir installer

echo ========================================
echo Compilando instalador con Inno Setup...
echo ========================================
echo.
"%INNO_SETUP_PATH%" "installer_script.iss"
if errorlevel 1 (
    echo.
    echo ERROR: Fallo al compilar el instalador
    pause
    exit /b 1
)

if exist "installer\SAGA_Setup.exe" (
    echo.
    echo ========================================
    echo INSTALADOR GENERADO
    echo ========================================
    echo.
    echo Ubicacion: installer\SAGA_Setup.exe
    echo.
    explorer installer
) else (
    echo.
    echo ADVERTENCIA: No se encontro installer\SAGA_Setup.exe
    echo Revisa los mensajes de Inno Setup arriba.
    echo.
)

echo.
pause
