; looplay! Inno Setup インストーラスクリプト
; ビルド方法: iscc /DAppVersion=1.0.0 installer\looplayer.iss

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
; アプリ識別情報
AppName=looplay!
AppVersion={#AppVersion}
AppPublisher=looplay! Project
AppId={{8B4A6C2D-3F1E-4D7A-9B5C-0E2F8A1D6C4B}

; インストール先（管理者権限不要、ユーザースコープ）
DefaultDirName={localappdata}\looplay
DefaultGroupName=looplay!
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline

; アンインストール登録
CreateUninstallRegKey=yes
UninstallDisplayName=looplay!
UninstallDisplayIcon={app}\looplay.exe

; バージョン情報（exe に埋め込む）
VersionInfoVersion={#AppVersion}
VersionInfoProductName=looplay!
VersionInfoCompany=looplay! Project

; 出力設定
OutputDir=..\dist
OutputBaseFilename=looplay-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes

; ウィザード外観
WizardStyle=modern
ShowLanguageDialog=auto

; インストール中にアプリが実行されている場合は閉じる
CloseApplications=yes
CloseApplicationsFilter=looplay.exe

[Languages]
; Windows システム言語が日本語の場合は日本語 UI、それ以外は英語 UI
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; アプリ本体（PyInstaller の onefile 出力）
Source: "..\dist\looplay.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; スタートメニュー
Name: "{group}\looplay!"; Filename: "{app}\looplay.exe"
; デスクトップ
Name: "{commondesktop}\looplay!"; Filename: "{app}\looplay.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
; インストール完了後に起動するオプション
Filename: "{app}\looplay.exe"; \
  Description: "{cm:LaunchProgram,looplay!}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; アプリインストールディレクトリを削除（ユーザーデータ ~/.looplayer/ は対象外）
Type: filesandordirs; Name: "{app}"
