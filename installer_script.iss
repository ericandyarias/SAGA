; Propósito: instalador de Windows (Inno Setup).
; Copia SAGA.exe, el icono y el catálogo de fábrica a AppData del usuario.
; Compilar con Inno Setup o con build_installer_completo.bat.

#define MyAppName "SAGA"
#define MyAppVersion "1.0"
#define MyAppPublisher "SAGA - Sistema Administrativo Gastronómico - Arias"
#define MyAppExeName "SAGA.exe"

[Setup]
AppId={{B7E4A91C-3F28-4D6A-9C15-8A2E6F4B1D70}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=SAGA_Setup
SetupIconFile=Icono Hamburguesa.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=no
DisableReadyPage=no
DisableFinishedPage=no
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\SAGA.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "Icono Hamburguesa.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\data\config_inicial_bdd\*"; DestDir: "{tmp}\SAGAData\config_inicial_bdd"; Flags: ignoreversion
Source: "dist\data\ventas.json"; DestDir: "{tmp}\SAGAData"; Flags: ignoreversion
Source: "dist\data\orden_actual.txt"; DestDir: "{tmp}\SAGAData"; Flags: ignoreversion
Source: "dist\data\imagenes\*"; DestDir: "{tmp}\SAGAData\imagenes"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel1.Caption := 'Bienvenido al instalador de SAGA';
  WizardForm.WelcomeLabel2.Caption := 'Sistema Administrativo Gastronómico - Arias';
end;

procedure CopyDirRecursive(SourceDir, DestDir: string);
var
  FindRec: TFindRec;
  SourcePath, DestPath: string;
begin
  if not DirExists(DestDir) then
    CreateDir(DestDir);

  if FindFirst(SourceDir + '\*', FindRec) then
  begin
    try
      repeat
        if (FindRec.Name <> '.') and (FindRec.Name <> '..') then
        begin
          SourcePath := SourceDir + '\' + FindRec.Name;
          DestPath := DestDir + '\' + FindRec.Name;
          if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0 then
            CopyDirRecursive(SourcePath, DestPath)
          else
            CopyFile(SourcePath, DestPath, False);
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
  if CurStep = ssPostInstall then
  begin
    AppDataPath := ExpandConstant('{userappdata}\SAGA');
    TempDataPath := ExpandConstant('{tmp}\SAGAData');

    if not DirExists(AppDataPath) then
      CreateDir(AppDataPath);

    if DirExists(TempDataPath) then
    begin
      if DirExists(TempDataPath + '\config_inicial_bdd') then
        CopyDirRecursive(TempDataPath + '\config_inicial_bdd', AppDataPath + '\config_inicial_bdd');
      if FileExists(TempDataPath + '\ventas.json') then
        CopyFile(TempDataPath + '\ventas.json', AppDataPath + '\ventas.json', False);
      if FileExists(TempDataPath + '\orden_actual.txt') then
        CopyFile(TempDataPath + '\orden_actual.txt', AppDataPath + '\orden_actual.txt', False);

      if DirExists(TempDataPath + '\imagenes') then
      begin
        if DirExists(AppDataPath + '\imagenes') then
          DelTree(AppDataPath + '\imagenes', True, True, True);
        CopyDirRecursive(TempDataPath + '\imagenes', AppDataPath + '\imagenes');
      end;
    end;

    if not DirExists(AppDataPath + '\tickets') then
      CreateDir(AppDataPath + '\tickets');
  end;
end;

