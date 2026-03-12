param(
	[Parameter(Mandatory = $true)]
	[string]$GitHubOwner,
	[string]$RepositoryName = "forza-precision-telemetry",
	[string]$Publisher = "Antigravity & User",
	[ValidateSet("stable", "beta", "dev")]
	[string]$Channel = "stable",
	[string]$LicenseName = "GPL v2",
	[string]$LicenseUrl = "https://www.gnu.org/licenses/gpl-2.0.html"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ghPath = Join-Path $root ".tools\bin\gh.exe"

function Invoke-External {
	param(
		[Parameter(Mandatory = $true)]
		[string]$Executable,
		[Parameter(Mandatory = $false)]
		[string[]]$Arguments = @()
	)

	& $Executable @Arguments
	if ($LASTEXITCODE -ne 0) {
		$joinedArgs = $Arguments -join " "
		throw "Command failed ($LASTEXITCODE): $Executable $joinedArgs"
	}
}

if (!(Test-Path $ghPath)) {
	throw "gh executable not found at $ghPath"
}

Invoke-External -Executable $ghPath -Arguments @("auth", "status")

& (Join-Path $root "scripts\build.ps1")

$manifestPath = Join-Path $root "manifest.ini"
$manifestContent = Get-Content -Path $manifestPath
$nameLine = $manifestContent | Where-Object { $_ -match "^\s*name\s*=" } | Select-Object -First 1
$versionLine = $manifestContent | Where-Object { $_ -match "^\s*version\s*=" } | Select-Object -First 1

if (-not $nameLine -or -not $versionLine) {
	throw "name/version fields are missing in manifest.ini"
}

$addonName = ($nameLine -split "=", 2)[1].Trim()
$addonVersion = ($versionLine -split "=", 2)[1].Trim()
$tag = "v$addonVersion"
$assetName = "$addonName-$addonVersion.nvda-addon"
$assetPath = Join-Path $root "dist\$assetName"

if (!(Test-Path $assetPath)) {
	throw "Built add-on asset not found: $assetPath"
}

$repoSlug = "$GitHubOwner/$RepositoryName"

$hasOrigin = $false
try {
	$originUrl = git -C $root remote get-url origin 2>$null
	if ($LASTEXITCODE -eq 0 -and $originUrl) { $hasOrigin = $true }
} catch {
	$hasOrigin = $false
}

if (-not $hasOrigin) {
	Invoke-External -Executable $ghPath -Arguments @("repo", "create", $repoSlug, "--public", "--source", $root, "--remote", "origin", "--push")
} else {
	git -C $root push -u origin HEAD
	if ($LASTEXITCODE -ne 0) {
		throw "Failed to push current branch to origin."
	}
}

$releaseExists = $true
try {
	Invoke-External -Executable $ghPath -Arguments @("release", "view", $tag, "--repo", $repoSlug)
} catch {
	$releaseExists = $false
}

if ($releaseExists) {
	Invoke-External -Executable $ghPath -Arguments @("release", "upload", $tag, $assetPath, "--repo", $repoSlug, "--clobber")
} else {
	Invoke-External -Executable $ghPath -Arguments @("release", "create", $tag, $assetPath, "--repo", $repoSlug, "--title", $tag, "--notes-file", (Join-Path $root "CHANGELOG.md"))
}

$downloadUrl = "https://github.com/$repoSlug/releases/download/$tag/$assetName"
$sourceUrl = "https://github.com/$repoSlug"

$query = @{
	template = "registerAddon.yml"
	title = "[Submit add-on]: Forza Precision Telemetry Announcer $addonVersion"
	"download-url" = $downloadUrl
	"source-url" = $sourceUrl
	publisher = $Publisher
	channel = $Channel
	"license-name" = $LicenseName
	"license-url" = $LicenseUrl
}

$encoded = ($query.GetEnumerator() | ForEach-Object {
	"{0}={1}" -f [Uri]::EscapeDataString($_.Key), [Uri]::EscapeDataString($_.Value)
}) -join "&"

$issueUrl = "https://github.com/nvaccess/addon-datastore/issues/new?$encoded"

Write-Host "Repository:"
Write-Host $sourceUrl
Write-Host "Release asset:"
Write-Host $downloadUrl
Write-Host "Open this URL to submit to NVDA add-on datastore:"
Write-Host $issueUrl

Start-Process $issueUrl
