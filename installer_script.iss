; Script de Inno Setup para Papucho Foodtruck
; Instrucciones: Abre este archivo en Inno Setup Compiler y compila
; O usa el script build_installer_completo.bat para automatizar todo

#define MyAppName "Papucho Foodtruck"
#define MyAppVersion "1.0"
#define MyAppPublisher "Papucho Foodtruck"
#define MyAppURL "https://www.papuchofoodtruck.com"
#define MyAppExeName "PapuchoFoodtruck.exe"

[Setup]
; Información básica de la aplicación
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=installer
OutputBaseFilename=PapuchoFoodtruck_Setup16
SetupIconFile=Icono Hamburguesa.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
; Configuración adicional
DisableProgramGroupPage=no
DisableReadyPage=no
DisableFinishedPage=no
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Archivo ejecutable principal
Source: "dist\PapuchoFoodtruck.exe"; DestDir: "{app}"; Flags: ignoreversion
; Icono de la aplicación (para uso en la ventana)
Source: "Icono Hamburguesa.ico"; DestDir: "{app}"; Flags: ignoreversion
; INCLUIR DATOS DIRECTAMENTE EN EL INSTALADOR (carpeta temporal)
; Estos datos se copiarán a AppData durante la instalación
Source: "dist\data\productos.json"; DestDir: "{tmp}\PapuchoData"; Flags: ignoreversion
Source: "dist\data\ingredientes.json"; DestDir: "{tmp}\PapuchoData"; Flags: ignoreversion
Source: "dist\data\config.json"; DestDir: "{tmp}\PapuchoData"; Flags: ignoreversion
Source: "dist\data\orden_actual.txt"; DestDir: "{tmp}\PapuchoData"; Flags: ignoreversion
Source: "dist\data\imagenes\*"; DestDir: "{tmp}\PapuchoData\imagenes"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\data\tickets\*"; DestDir: "{tmp}\PapuchoData\tickets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function FileExistsCheck(FileName: string): Boolean;
var
  FullPath: string;
begin
  FullPath := ExpandConstant('{src}\') + FileName;
  Result := FileExists(FullPath);
end;

procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel1.Caption := 'Bienvenido al instalador de Papucho Foodtruck';
  WizardForm.WelcomeLabel2.Caption := 'Este asistente le guiará a través del proceso de instalación.';
end;

// Función auxiliar para copiar directorio recursivamente
procedure CopyDirRecursive(SourceDir, DestDir: string);
var
  FindRec: TFindRec;
  SourcePath, DestPath: string;
begin
  // Crear directorio destino si no existe
  if not DirExists(DestDir) then
    CreateDir(DestDir);
  
  // Buscar todos los archivos y subdirectorios
  if FindFirst(SourceDir + '\*', FindRec) then
  begin
    try
      repeat
        if (FindRec.Name <> '.') and (FindRec.Name <> '..') then
        begin
          SourcePath := SourceDir + '\' + FindRec.Name;
          DestPath := DestDir + '\' + FindRec.Name;
          
          if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0 then
          begin
            // Es un directorio, copiar recursivamente
            CopyDirRecursive(SourcePath, DestPath);
          end
          else
          begin
            // Es un archivo, copiarlo (sobrescribir si existe)
            CopyFile(SourcePath, DestPath, True);
          end;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;


procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataPath: string;
  TempDataPath: string;
begin
  // Cuando se completa la instalación, copiar datos a AppData
  if CurStep = ssPostInstall then
  begin
    // Obtener ruta de AppData del usuario
    AppDataPath := ExpandConstant('{userappdata}\Papucho Foodtruck');
    // Los datos están en la carpeta temporal del instalador
    TempDataPath := ExpandConstant('{tmp}\PapuchoData');
    
    // Crear directorio en AppData
    if not DirExists(AppDataPath) then
      CreateDir(AppDataPath);
    
    // Copiar TODOS los datos desde la carpeta temporal a AppData
    // Los datos fueron extraídos del instalador a {tmp}\PapuchoData
    if DirExists(TempDataPath) then
    begin
      // Copiar TODOS los archivos JSON y de texto (SOBRESCRIBIR si existen)
      if FileExists(TempDataPath + '\productos.json') then
        CopyFile(TempDataPath + '\productos.json', AppDataPath + '\productos.json', True);
      if FileExists(TempDataPath + '\ingredientes.json') then
        CopyFile(TempDataPath + '\ingredientes.json', AppDataPath + '\ingredientes.json', True);
      if FileExists(TempDataPath + '\config.json') then
        CopyFile(TempDataPath + '\config.json', AppDataPath + '\config.json', True);
      if FileExists(TempDataPath + '\orden_actual.txt') then
        CopyFile(TempDataPath + '\orden_actual.txt', AppDataPath + '\orden_actual.txt', True);
      
      // Copiar carpeta de imágenes completa (recursivamente) - TODAS las imágenes
      if DirExists(TempDataPath + '\imagenes') then
      begin
        // Eliminar carpeta destino si existe para copiar todo de nuevo
        if DirExists(AppDataPath + '\imagenes') then
        begin
          DelTree(AppDataPath + '\imagenes', True, True, True);
        end;
        CopyDirRecursive(TempDataPath + '\imagenes', AppDataPath + '\imagenes');
      end;
      
      // Copiar carpeta de tickets completa (recursivamente) - TODOS los tickets
      if DirExists(TempDataPath + '\tickets') then
      begin
        // No eliminar tickets existentes, solo agregar los nuevos
        CopyDirRecursive(TempDataPath + '\tickets', AppDataPath + '\tickets');
      end
      else
      begin
        // Crear carpeta tickets vacía si no existe
        if not DirExists(AppDataPath + '\tickets') then
          CreateDir(AppDataPath + '\tickets');
      end;
    end;
  end;
end;
