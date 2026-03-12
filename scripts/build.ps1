Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$manifestPath = Join-Path $root "manifest.ini"
$pluginPath = Join-Path $root "globalPlugins"
$installTasksPath = Join-Path $root "installTasks.py"
$distPath = Join-Path $root "dist"

if (!(Test-Path $manifestPath)) { throw "manifest.ini not found: $manifestPath" }
if (!(Test-Path $pluginPath)) { throw "globalPlugins not found: $pluginPath" }
if (!(Test-Path $installTasksPath)) { throw "installTasks.py not found: $installTasksPath" }

$manifestContent = Get-Content -Path $manifestPath
$nameLine = $manifestContent | Where-Object { $_ -match "^\s*name\s*=" } | Select-Object -First 1
$versionLine = $manifestContent | Where-Object { $_ -match "^\s*version\s*=" } | Select-Object -First 1

if (-not $nameLine) { throw "name field is missing in manifest.ini" }
if (-not $versionLine) { throw "version field is missing in manifest.ini" }

$addonName = ($nameLine -split "=", 2)[1].Trim()
$addonVersion = ($versionLine -split "=", 2)[1].Trim()

if ([string]::IsNullOrWhiteSpace($addonName)) { throw "name value is empty in manifest.ini" }
if ([string]::IsNullOrWhiteSpace($addonVersion)) { throw "version value is empty in manifest.ini" }

if (!(Test-Path $distPath)) {
	New-Item -Path $distPath -ItemType Directory | Out-Null
}

$zipPath = Join-Path $distPath "$addonName-$addonVersion.zip"
$addonPath = Join-Path $distPath "$addonName-$addonVersion.nvda-addon"

if (Test-Path $zipPath) { Remove-Item -Path $zipPath -Force }
if (Test-Path $addonPath) { Remove-Item -Path $addonPath -Force }

Compress-Archive -Path @(
	$pluginPath,
	$installTasksPath,
	$manifestPath
) -DestinationPath $zipPath -CompressionLevel Optimal -Force

Move-Item -Path $zipPath -Destination $addonPath -Force

$hash = Get-FileHash -Path $addonPath -Algorithm SHA256

Write-Host "Addon package created:"
Write-Host $addonPath
Write-Host "SHA256:"
Write-Host $hash.Hash
