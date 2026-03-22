@echo off
echo ========================================
echo INSTALACION DE DRIVER USB PARA IMPRESORA
echo ========================================
echo.
echo Este script te ayudara a instalar el driver USB necesario.
echo.
echo PASO 1: Descargar Zadig
echo.
echo Abre tu navegador y ve a: https://zadig.akeo.ie/
echo Descarga Zadig y ejecutalo.
echo.
echo PASO 2: Configurar Zadig
echo.
echo 1. Conecta tu impresora Xprinter EX-E200M por USB
echo 2. Abre Zadig
echo 3. En el menu "Options", marca "List All Devices"
echo 4. Selecciona tu impresora de la lista desplegable
echo 5. En el campo derecho, selecciona "libusb-win32" o "WinUSB"
echo 6. Haz clic en "Install Driver" o "Replace Driver"
echo 7. Espera a que termine la instalacion
echo 8. Cierra Zadig
echo.
echo PASO 3: Reiniciar
echo.
echo Reinicia tu computadora para que los cambios tengan efecto.
echo.
echo PASO 4: Probar
echo.
echo Despues de reiniciar, ejecuta:
echo   python utils/probar_impresora.py
echo.
pause
