@echo off
echo ========================================
echo Construyendo instalador Papucho Foodtruck
echo ========================================
echo.

REM Verificar que PyInstaller esté instalado
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller no está instalado. Instalando...
    python -m pip install pyinstaller
)

REM Limpiar builds anteriores
echo Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM Construir el ejecutable
echo.
echo Construyendo ejecutable...
pyinstaller --clean papucho_foodtruck.spec

if errorlevel 1 (
    echo.
    echo ERROR: Fallo al construir el ejecutable
    pause
    exit /b 1
)

echo.
echo ========================================
echo Ejecutable construido exitosamente!
echo Se encuentra en: dist\PapuchoFoodtruck.exe
echo ========================================
echo.
echo Ahora puedes crear el instalador con Inno Setup
echo usando el archivo: installer_script.iss
echo.
pause
