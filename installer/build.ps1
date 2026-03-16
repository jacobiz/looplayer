# LoopPlayer ローカルビルドスクリプト
# 使い方: ./installer/build.ps1 [-Version 1.0.0]
# 前提: VLC と Inno Setup が Chocolatey でインストール済み
#   choco install vlc innosetup

param(
    [string]$Version = "1.0.0"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$DistDir = Join-Path $RepoRoot "dist"

Write-Host "=== LoopPlayer ビルド開始 (v$Version) ===" -ForegroundColor Cyan

# 出力ディレクトリを準備
if (Test-Path $DistDir) {
    Remove-Item -Path "$DistDir\LoopPlayer*" -Force -ErrorAction SilentlyContinue
}

# Step 1: PyInstaller で exe をビルド
Write-Host "[1/3] PyInstaller でバンドル中..." -ForegroundColor Yellow
Push-Location $RepoRoot
pyinstaller installer/looplayer.spec
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller ビルドに失敗しました"
    exit 1
}
Pop-Location

# Step 2: Inno Setup でインストーラを作成
Write-Host "[2/3] Inno Setup でインストーラを生成中..." -ForegroundColor Yellow
$IssPath = Join-Path $PSScriptRoot "looplayer.iss"
iscc /DAppVersion=$Version $IssPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Inno Setup ビルドに失敗しました"
    exit 1
}

# Step 3: SHA256 チェックサムを生成
Write-Host "[3/3] SHA256 チェックサムを生成中..." -ForegroundColor Yellow
$InstallerPath = Join-Path $DistDir "LoopPlayer-Setup-$Version.exe"
if (-not (Test-Path $InstallerPath)) {
    Write-Error "インストーラファイルが見つかりません: $InstallerPath"
    exit 1
}

$Hash = (Get-FileHash $InstallerPath -Algorithm SHA256).Hash
$ChecksumContent = "SHA256: $Hash  LoopPlayer-Setup-$Version.exe"
$ChecksumPath = Join-Path $DistDir "SHA256SUMS.txt"
$ChecksumContent | Out-File -FilePath $ChecksumPath -Encoding UTF8

# ファイルサイズ確認（SC-002: 200MB 以下）
$SizeMB = [math]::Round((Get-Item $InstallerPath).Length / 1MB, 1)
Write-Host ""
Write-Host "=== ビルド完了 ===" -ForegroundColor Green
Write-Host "インストーラ : $InstallerPath"
Write-Host "ファイルサイズ: ${SizeMB} MB $(if ($SizeMB -le 200) { '✓ (200MB 以下)' } else { '✗ (200MB 超過！)' })"
Write-Host "SHA256      : $Hash"
Write-Host "チェックサム : $ChecksumPath"
