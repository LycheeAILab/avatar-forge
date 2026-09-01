param(
  [string]$Version = "2.1.0"
)

$ErrorActionPreference = "Stop"
$repo = "https://github.com/LycheeAILab/avatar-forge/releases/download/v$Version"
$archiveName = "avatar-forge-workbuddy-$Version.zip"
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("avatar-forge-install-" + [guid]::NewGuid().ToString("N"))
$archive = Join-Path $tempRoot $archiveName
$checksums = Join-Path $tempRoot "SHA256SUMS"
$extract = Join-Path $tempRoot "extract"
$skillsRoot = Join-Path $env:USERPROFILE ".workbuddy\skills"
$target = Join-Path $skillsRoot "avatar-forge-pipeline"

New-Item -ItemType Directory -Path $tempRoot, $extract, $skillsRoot -Force | Out-Null
Invoke-WebRequest "$repo/$archiveName" -OutFile $archive
Invoke-WebRequest "$repo/SHA256SUMS" -OutFile $checksums

$expectedLine = Get-Content -LiteralPath $checksums | Where-Object { $_ -match [regex]::Escape($archiveName) } | Select-Object -First 1
if (-not $expectedLine) { throw "No checksum found for $archiveName" }
$expected = ($expectedLine -split '\s+')[0].ToLowerInvariant()
$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "SHA256 verification failed" }

Expand-Archive -LiteralPath $archive -DestinationPath $extract -Force
$source = Join-Path $extract "avatar-forge-pipeline"
if (-not (Test-Path -LiteralPath (Join-Path $source "SKILL.md"))) { throw "Invalid WorkBuddy Skill archive" }

if (Test-Path -LiteralPath $target) {
  $backup = "$target.backup-$(Get-Date -Format 'yyyyMMddHHmmss')"
  Move-Item -LiteralPath $target -Destination $backup
  Write-Host "Previous installation moved to $backup"
}
Move-Item -LiteralPath $source -Destination $target

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw "Python 3.9 or newer is required" }
& $python.Source -m pip install --user -r (Join-Path $target "requirements.txt")
& $python.Source (Join-Path $target "scripts\doctor.py")
if ($LASTEXITCODE -ne 0) { throw "Avatar Forge doctor failed" }
Write-Host "Avatar Forge $Version is installed for WorkBuddy at $target"
