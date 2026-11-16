[CmdletBinding()]
param(
    [string]$SlicerRevision = '34645',
    [string]$SlicerMajorMinor = '5.12',
    [string]$Platform = 'win-amd64'
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$stageRoot = Join-Path $repositoryRoot 'build\slicer-package-staging'
$packageRoot = Join-Path $stageRoot 'PulmoSlicerAI-2026.11.16.10'
$distRoot = Join-Path $repositoryRoot 'dist'
$moduleSource = Join-Path $repositoryRoot 'slicer_extension\PulmoSlicerAI'
$descriptorSource = Join-Path $repositoryRoot 'slicer_extension\PulmoSlicerAI.s4ext'
$moduleDestination = Join-Path $packageRoot "lib\Slicer-$SlicerMajorMinor\qt-scripted-modules"
$shareDestination = Join-Path $packageRoot "share\Slicer-$SlicerMajorMinor"
$archiveName = "$SlicerRevision-$Platform-PulmoSlicerAI-gitlocal-2026-11-16.zip"
$archivePath = Join-Path $distRoot $archiveName

$rootFull = [System.IO.Path]::GetFullPath($repositoryRoot).TrimEnd('\') + '\'
$stageFull = [System.IO.Path]::GetFullPath($stageRoot)
if (-not $stageFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe staging path: $stageFull"
}
if (-not (Test-Path -LiteralPath (Join-Path $moduleSource 'PulmoSlicerAI.py') -PathType Leaf)) {
    throw "Missing module source: $moduleSource"
}

if (Test-Path -LiteralPath $stageRoot) {
    Remove-Item -LiteralPath $stageRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $moduleDestination -Force | Out-Null
New-Item -ItemType Directory -Path $shareDestination -Force | Out-Null
New-Item -ItemType Directory -Path $distRoot -Force | Out-Null

Copy-Item -LiteralPath (Join-Path $moduleSource 'PulmoSlicerAI.py') -Destination $moduleDestination
$libraryDestination = Join-Path $moduleDestination 'PulmoSlicerAILib'
Copy-Item -LiteralPath (Join-Path $moduleSource 'PulmoSlicerAILib') -Destination $libraryDestination -Recurse
Get-ChildItem -LiteralPath $libraryDestination -Directory -Recurse -Filter '__pycache__' |
    Remove-Item -Recurse -Force
$engineSource = Join-Path $repositoryRoot 'pulmoslicer_engine'
$engineDestination = Join-Path $moduleDestination 'pulmoslicer_engine'
Copy-Item -LiteralPath $engineSource -Destination $engineDestination -Recurse
Get-ChildItem -LiteralPath $engineDestination -Directory -Recurse -Filter '__pycache__' |
    Remove-Item -Recurse -Force
Copy-Item -LiteralPath $descriptorSource -Destination (Join-Path $shareDestination 'PulmoSlicerAI.s4ext')

$manifest = [ordered]@{
    extension = 'PulmoSlicerAI'
    package_revision = '2026.11.16.10'
    slicer_version = '5.12.4'
    slicer_revision = $SlicerRevision
    platform = $Platform
    research_only = $true
    ptl_runtime = 'auto-download-on-first-use'
    ptl_checkpoint_redistribution = $false
    compute_backend_policy = 'auto-cuda-rocm-compatible-then-cpu'
    directml_totalsegmentator_supported = $false
    dependencies = @('TotalSegmentator')
    recommendations = @('SlicerVMTK', 'SegmentEditorExtraEffects', 'MarkupsToModel')
    interactive_html = [ordered]@{
        contract = '1.0.0'
        viewer = 'Three.js 0.187.0'
        bundler = 'esbuild 0.28.2'
        offline_single_file = $true
        default_select_all_valid = $true
    }
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $shareDestination 'PulmoSlicerAI-package.json') -Encoding utf8

if (Test-Path -LiteralPath $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}
Compress-Archive -Path $packageRoot -DestinationPath $archivePath -CompressionLevel Optimal
$hash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $archiveName" | Set-Content -LiteralPath "$archivePath.sha256" -Encoding ascii
Write-Host "Created: $archivePath"
Write-Host "SHA256: $hash"
