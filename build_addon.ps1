[CmdletBinding()]
param(
    [string]$Version = "",
    [switch]$Dev
)

$ErrorActionPreference = "Stop"

# Garante que roda a partir da pasta do script
$rootDir = $PSScriptRoot
if (-not $rootDir) {
    $rootDir = Get-Location
}
Set-Location $rootDir

# 1. Detectar Versão
if ([string]::IsNullOrWhiteSpace($Version)) {
    $manifestPath = Join-Path $rootDir "roblox_animations\blender_manifest.toml"
    if (Test-Path $manifestPath) {
        $content = Get-Content $manifestPath -Raw
        if ($content -match '(?m)^\s*version\s*=\s*["'']([^"'']+)["'']') {
            $Version = $matches[1]
        }
    }
}

if ([string]::IsNullOrWhiteSpace($Version)) {
    $initPath = Join-Path $rootDir "roblox_animations\__init__.py"
    if (Test-Path $initPath) {
        $content = Get-Content $initPath -Raw
        if ($content -match '"version":\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)') {
            $Version = "$($matches[1]).$($matches[2]).$($matches[3])"
        }
    }
}

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = "dev"
}

$addonName = "roblox_animations"
$addonSrcDir = Join-Path $rootDir $addonName
if (-not (Test-Path $addonSrcDir)) {
    Write-Error "Pasta '$addonName' não foi encontrada em '$rootDir'!"
    exit 1
}

$zipLegacy = Join-Path $rootDir "rbx_anims_v$($Version)_legacy.zip"
$zipBlender4 = Join-Path $rootDir "rbx_anims_v$($Version).zip"
$tempBuild = Join-Path $rootDir "temp_build"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Blender Addon Builder - Versao: $Version" -ForegroundColor Cyan
if ($Dev) {
    Write-Host "  Modo: DEV (incluindo testes e arquivos de desenvolvimento)" -ForegroundColor Yellow
}
Write-Host "================================================================" -ForegroundColor Cyan

# 2. Limpeza prévia
if (Test-Path $zipLegacy) { Remove-Item $zipLegacy -Force }
if (Test-Path $zipBlender4) { Remove-Item $zipBlender4 -Force }
if (Test-Path $tempBuild) { Remove-Item $tempBuild -Recurse -Force }

$tempAddonDir = Join-Path $tempBuild $addonName
New-Item -ItemType Directory -Path $tempAddonDir -Force | Out-Null

# 3. Copiar arquivos excluindo lixo
Write-Host "[1/3] Copiando arquivos do addon..." -ForegroundColor Green

$excludedNames = @('__pycache__', '.ruff_cache', '.pytest_cache', '.mypy_cache', '.vscode', '.git', '.idea', '.DS_Store')
if (-not $Dev) {
    $excludedNames += 'tests'
}

$files = Get-ChildItem -Path $addonSrcDir -Recurse | Where-Object {
    $item = $_
    $skip = $false
    foreach ($ex in $excludedNames) {
        if ($item.FullName -match "[\\/]$([regex]::Escape($ex))([\\/]|$)") {
            $skip = $true
            break
        }
    }
    -not $skip
}

foreach ($file in $files) {
    $relPath = $file.FullName.Substring($addonSrcDir.Length).TrimStart('\', '/')
    $destPath = Join-Path $tempAddonDir $relPath

    if ($file.PSIsContainer) {
        if (-not (Test-Path $destPath)) {
            New-Item -ItemType Directory -Path $destPath -Force | Out-Null
        }
    } else {
        $parentDir = Split-Path $destPath -Parent
        if (-not (Test-Path $parentDir)) {
            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
        }
        Copy-Item -Path $file.FullName -Destination $destPath -Force
    }
}

# 4. Criar ZIP Blender 3.x (Legacy: pasta roblox_animations na raiz)
Write-Host "[2/3] Criando $zipLegacy (Blender 3.x)..." -ForegroundColor Green
Compress-Archive -Path $tempAddonDir -DestinationPath $zipLegacy -Force

# 5. Criar ZIP Blender 4.x+ (Extensions: arquivos na raiz)
Write-Host "[3/3] Criando $zipBlender4 (Blender 4.x+)..." -ForegroundColor Green
$addonFiles = Get-ChildItem -Path $tempAddonDir
Compress-Archive -Path $addonFiles.FullName -DestinationPath $zipBlender4 -Force

# 6. Limpeza do temp
if (Test-Path $tempBuild) {
    Remove-Item $tempBuild -Recurse -Force
}

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  SUCESSO! Addon compilado em 2 formatos:" -ForegroundColor Green
Write-Host "  1. $(Split-Path $zipLegacy -Leaf)  -> Blender 3.x (pasta na raiz do zip)" -ForegroundColor White
Write-Host "  2. $(Split-Path $zipBlender4 -Leaf) -> Blender 4.x+ / Extensions (manifest na raiz)" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan
