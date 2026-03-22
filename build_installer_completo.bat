@echo off
chcp 65001 >nul
echo ========================================
echo   GENERADOR DE INSTALADOR COMPLETO
echo   Papucho Foodtruck
echo ========================================
echo.

REM Verificar que estamos en la carpeta correcta
if not exist "main.py" (
    echo ERROR: No se encontró main.py
    echo Asegúrate de ejecutar este script desde la carpeta raíz del proyecto.
    pause
    exit /b 1
)

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor, instala Python desde https://www.python.org/downloads/
    echo IMPORTANTE: Marca "Add Python to PATH" durante la instalación
    pause
    exit /b 1
)

REM Verificar que PyInstaller esté instalado
echo Verificando PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller no está instalado. Instalando...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: No se pudo instalar PyInstaller
        pause
        exit /b 1
    )
)

REM Limpiar builds anteriores
echo.
echo Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

REM Construir el ejecutable
echo.
echo ========================================
echo Construyendo ejecutable...
echo ========================================
pyinstaller --clean papucho_foodtruck.spec

if errorlevel 1 (
    echo.
    echo ERROR: Fallo al construir el ejecutable
    pause
    exit /b 1
)

REM Verificar que el ejecutable se creó
if not exist "dist\PapuchoFoodtruck.exe" (
    echo.
    echo ERROR: El ejecutable no se generó correctamente
    pause
    exit /b 1
)

REM Copiar TODOS los datos actuales de data\ a dist\data (necesario para el instalador)
echo.
echo Copiando archivos de datos actuales...
if not exist "dist\data" mkdir "dist\data"
REM Limpiar dist\data primero para asegurar que se copien los datos más recientes
if exist "dist\data" (
    echo Limpiando datos antiguos en dist\data...
    rmdir /s /q "dist\data"
    mkdir "dist\data"
)
REM Copiar TODOS los datos actuales (sobrescribiendo)
echo Copiando datos desde data\ a dist\data...
xcopy /E /I /Y "data\*" "dist\data\" >nul 2>&1
if errorlevel 1 (
    echo ADVERTENCIA: Algunos archivos no se pudieron copiar
) else (
    echo Datos copiados exitosamente
)

echo.
echo ========================================
echo Ejecutable construido exitosamente!
echo ========================================
echo.

REM Verificar que Inno Setup esté instalado
echo Verificando Inno Setup...
set "INNO_SETUP_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_SETUP_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_SETUP_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set "INNO_SETUP_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 5\ISCC.exe" (
    set "INNO_SETUP_PATH=C:\Program Files\Inno Setup 5\ISCC.exe"
)

if "%INNO_SETUP_PATH%"=="" (
    echo.
    echo ADVERTENCIA: Inno Setup no se encontró en las ubicaciones estándar.
    echo.
    echo Por favor, compila el instalador manualmente:
    echo 1. Abre Inno Setup Compiler
    echo 2. File ^> Open
    echo 3. Selecciona installer_script.iss
    echo 4. Build ^> Compile (o presiona F9)
    echo.
    echo El instalador se generará en: installer\PapuchoFoodtruck_Setup16.exe
    echo.
    pause
    exit /b 0
)

REM Crear carpeta installer si no existe
if not exist installer mkdir installer

REM Compilar el instalador
echo.
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

REM Verificar que el instalador se creó
if exist "installer\PapuchoFoodtruck_Setup16.exe" (
    echo.
    echo ========================================
    echo ¡INSTALADOR GENERADO EXITOSAMENTE!
    echo ========================================
    echo.
    echo Ubicación: installer\PapuchoFoodtruck_Setup16.exe
    echo.
    
    REM Obtener el tamaño del archivo
    for %%A in ("installer\PapuchoFoodtruck_Setup16.exe") do set SIZE=%%~zA
    set /a SIZE_MB=%SIZE:~0,-6%
    echo Tamaño aproximado: %SIZE_MB% MB
    echo.
    echo El instalador está listo para distribuir.
    echo.
    
    REM Preguntar si quiere abrir la carpeta
    set /p ABRIR="¿Deseas abrir la carpeta del instalador? (S/N): "
    if /i "%ABRIR%"=="S" (
        explorer installer
    )
) else (
    echo.
    echo ADVERTENCIA: El instalador no se generó en la ubicación esperada.
    echo Verifica los mensajes de Inno Setup arriba.
    echo.
)

echo.
pause
