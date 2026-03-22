# 📦 INSTRUCCIONES PARA CREAR EL INSTALADOR

## PASO 0: Verificar Python (IMPORTANTE)

**Antes de continuar**, verifica que Python esté instalado y funcionando:

```bash
python --version
```

Si ves un error como "Python no se encontró" o "Python was not found":
- **Ve primero a la sección "SOLUCIÓN DE PROBLEMAS" más abajo**
- O instala Python desde: https://www.python.org/downloads/
- **IMPORTANTE:** Al instalar, marca "Add Python to PATH"

---

## PASO 1: Instalar PyInstaller

Abre una terminal (PowerShell o CMD) en la carpeta del proyecto y ejecuta:

```bash
python -m pip install pyinstaller
```

**Nota:** Si `pip` no funciona, usa `python -m pip` (más confiable en Windows)

---

## PASO 2: Generar el Ejecutable (.exe)

### Opción A: Usar el script automático (RECOMENDADO)

1. Haz doble clic en el archivo `build_installer.bat`
2. Espera a que termine el proceso
3. El ejecutable estará en la carpeta `dist\PapuchoFoodtruck.exe`

### Opción B: Manual

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
pyinstaller --clean papucho_foodtruck.spec
```

---

## PASO 3: Verificar el Ejecutable

1. Ve a la carpeta `dist`
2. Ejecuta `PapuchoFoodtruck.exe` para verificar que funciona
3. Asegúrate de que la carpeta `data` esté junto al .exe

---

## PASO 4: Crear el Instalador con Inno Setup

### 4.1. Instalar Inno Setup

1. Descarga Inno Setup desde: https://jrsoftware.org/isdl.php
2. Instálalo (es gratuito)

### 4.2. Compilar el Instalador

1. Abre Inno Setup Compiler
2. Ve a: **File → Open**
3. Selecciona el archivo: `installer_script.iss`
4. Ve a: **Build → Compile** (o presiona F9)
5. Espera a que termine la compilación
6. El instalador estará en: `installer\PapuchoFoodtruck_Setup.exe`

---

## PASO 5: Probar el Instalador

1. Ejecuta `PapuchoFoodtruck_Setup.exe`
2. Sigue el asistente de instalación
3. Verifica que la aplicación se instale correctamente
4. Prueba ejecutar la aplicación desde el menú de inicio

---

## 📋 ESTRUCTURA FINAL

Después de compilar, deberías tener:

```
papucho-foodtruck/
├── dist/
│   ├── PapuchoFoodtruck.exe
│   └── data/
│       ├── productos.json
│       ├── orden_actual.txt
│       └── tickets/
├── installer/
│   └── PapuchoFoodtruck_Setup.exe  ← ESTE ES EL INSTALADOR FINAL
└── build/ (puedes ignorar esta carpeta)
```

---

## 🔧 PERSONALIZACIÓN OPCIONAL

### Icono de la Aplicación

El icono ya está configurado y se generará automáticamente. El archivo `icono.ico` se crea usando el script `crear_icono.py`.

**El icono aparecerá en:**
- El ejecutable `.exe` (en el Explorador de archivos)
- El instalador (ventana del instalador)
- El escritorio (si el usuario elige crear un acceso directo)
- El menú de inicio
- El Panel de Control → Programas y características (desinstalación)

**Para regenerar el icono:**
```bash
python crear_icono.py
```

**Para usar un icono personalizado:**
1. Crea o descarga un archivo `icono.ico` (debe ser formato ICO con múltiples tamaños)
2. Reemplaza el archivo `icono.ico` en la raíz del proyecto
3. El icono se usará automáticamente en la próxima compilación

### Cambiar el Nombre de la Aplicación

Edita `installer_script.iss` y modifica:
```iss
#define MyAppName "Tu Nombre Aquí"
```

### Cambiar la Versión

Edita `installer_script.iss` y modifica:
```iss
#define MyAppVersion "1.0"
```

---

## ⚠️ NOTAS IMPORTANTES

1. **Primera vez**: El proceso puede tardar varios minutos
2. **Antivirus**: Algunos antivirus pueden marcar el .exe como sospechoso (falso positivo). Esto es normal con PyInstaller
3. **Tamaño**: El ejecutable será grande (~50-100MB) porque incluye Python
4. **Pruebas**: Siempre prueba el instalador en una máquina limpia antes de distribuirlo

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### ⚠️ ERROR CRÍTICO: "Python no se encontró" o "Python was not found"

Este es el error más común. Significa que Python no está instalado o no está en el PATH.

**Solución 1: Verificar si Python está instalado (pero no en PATH)**

1. Busca Python en tu sistema:
   - Presiona `Win + R`
   - Escribe: `%LOCALAPPDATA%\Programs\Python`
   - O busca en: `C:\Users\TuUsuario\AppData\Local\Programs\Python`
   - O en: `C:\Python3X` (donde X es la versión)

2. Si encuentras Python, agrégalo al PATH:
   - Presiona `Win + X` → "Sistema"
   - Click en "Configuración avanzada del sistema"
   - Click en "Variables de entorno"
   - En "Variables del sistema", busca "Path" y click en "Editar"
   - Click en "Nuevo" y agrega la ruta de Python (ej: `C:\Python314`)
   - Click en "Nuevo" otra vez y agrega la carpeta Scripts (ej: `C:\Python314\Scripts`)
   - Click "Aceptar" en todas las ventanas
   - **Cierra y vuelve a abrir** la terminal

3. Si no encuentras Python, instálalo:
   - Ve a: https://www.python.org/downloads/
   - Descarga la última versión de Python 3.x
   - **IMPORTANTE:** Al instalar, marca la casilla "Add Python to PATH"
   - Instala normalmente
   - **Cierra y vuelve a abrir** la terminal

**Solución 2: Usar Python desde la ruta completa**

Si sabes dónde está Python, puedes usarlo directamente:

```bash
# Ejemplo (ajusta la ruta según tu instalación):
C:\Python314\python.exe -m pip install pyinstaller
```

**Solución 3: Deshabilitar el alias de Microsoft Store**

Si Windows te redirige a Microsoft Store:

1. Presiona `Win + I` (Configuración)
2. Ve a: "Aplicaciones" → "Configuración avanzada de aplicaciones" → "Alias de ejecución de aplicaciones"
3. Desactiva los alias de "App Installer" para `python.exe` y `python3.exe`
4. Cierra y vuelve a abrir la terminal

### Error: "pip no reconocido" o "pip no encontrado"

**Solución 1 (Recomendada):** Usa `python -m pip` en lugar de solo `pip`:
```bash
python -m pip install pyinstaller
```

**Solución 2:** Verifica que Python esté instalado:
```bash
python --version
```

**Solución 3:** Si Python no está en el PATH:
- Abre "Configuración del sistema" → "Variables de entorno"
- Agrega Python al PATH (normalmente: `C:\Python3X` y `C:\Python3X\Scripts`)

### Error: "PyInstaller no encontrado"
```bash
python -m pip install --upgrade pyinstaller
```

### Error: "No se encuentra main.py"
- Asegúrate de estar en la carpeta correcta del proyecto

### Error: "Falta la carpeta data"
- Verifica que `papucho_foodtruck.spec` incluya:
  ```python
  datas=[('data', 'data')],
  ```

### El ejecutable no funciona
- Prueba ejecutarlo desde la terminal para ver errores:
  ```bash
  dist\PapuchoFoodtruck.exe
  ```

---

## ✅ CHECKLIST FINAL

- [ ] PyInstaller instalado
- [ ] Ejecutable generado en `dist\PapuchoFoodtruck.exe`
- [ ] Ejecutable probado y funcionando
- [ ] Inno Setup instalado
- [ ] Instalador compilado en `installer\PapuchoFoodtruck_Setup.exe`
- [ ] Instalador probado en máquina limpia

---

¡Listo! Ya tienes tu instalador profesional. 🎉
