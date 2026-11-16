[CmdletBinding()]
param(
    [string]$SlicerHome = 'D:\Program Files\3D Slicer 5.12.4',
    [switch]$SkipPreflight
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$slicerExecutable = Join-Path $SlicerHome 'Slicer.exe'
$modulePath = Join-Path $repositoryRoot 'slicer_extension\PulmoSlicerAI'

if (-not $SkipPreflight) {
    & (Join-Path $PSScriptRoot 'Test-SlicerEnvironment.ps1') -SlicerHome $SlicerHome
}
if (-not (Test-Path -LiteralPath $slicerExecutable -PathType Leaf)) {
    throw "Khong tim thay Slicer.exe tai: $slicerExecutable"
}

Write-Host 'Dang mo 3D Slicer voi PulmoSlicer AI...'
& $slicerExecutable `
    --additional-module-paths $modulePath `
    --python-code "slicer.util.selectModule('PulmoSlicerAI')"

