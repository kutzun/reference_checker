; Inno Setup Script for Reference Checker
[Setup]
AppName=Reference Checker
AppVersion=1.2.2
DefaultDirName={autopf}\ReferenceChecker
DefaultGroupName=Reference Checker
UninstallDisplayIcon={app}\ReferenceChecker.exe
OutputBaseFilename=ReferenceChecker_Setup_v1.2.2
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=LICENSE

[Files]
Source: "dist\ReferenceChecker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Reference Checker"; Filename: "{app}\ReferenceChecker.exe"
Name: "{autodesktop}\Reference Checker"; Filename: "{app}\ReferenceChecker.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\ReferenceChecker.exe"; Description: "Launch Reference Checker"; Flags: nowait postinstall skipifsilent