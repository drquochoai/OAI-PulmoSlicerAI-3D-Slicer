[CmdletBinding()]
param(
    [string]$SlicerHome = 'D:\Program Files\3D Slicer 5.12.4'
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$slicerExecutable = Join-Path $SlicerHome 'Slicer.exe'
$modulePath = Join-Path $repositoryRoot 'slicer_extension\PulmoSlicerAI'
$smokeScript = Join-Path $repositoryRoot 'tools\slicer_environment_smoke.py'
$evidenceDirectory = Join-Path $repositoryRoot 'evidence\local'
$evidencePath = Join-Path $evidenceDirectory 'slicer-smoke.json'
$slicerLogDirectory = Join-Path $env:LOCALAPPDATA 'Temp\Slicer'

if (-not (Test-Path -LiteralPath $slicerExecutable -PathType Leaf)) {
    throw "Khong tim thay Slicer.exe tai: $slicerExecutable"
}
if (-not (Test-Path -LiteralPath (Join-Path $modulePath 'PulmoSlicerAI.py') -PathType Leaf)) {
    throw "Khong tim thay module PulmoSlicerAI tai: $modulePath"
}

New-Item -ItemType Directory -Path $evidenceDirectory -Force | Out-Null
$existingLogNames = @(
    Get-ChildItem -LiteralPath $slicerLogDirectory -Filter 'Slicer_5.12.4_*.log' -ErrorAction SilentlyContinue |
        ForEach-Object { $_.FullName }
)

Write-Host "Dang kiem tra Slicer va cac extension, khong doc du lieu benh nhan..."
$arguments = @(
    '--no-main-window',
    '--no-splash',
    '--additional-module-paths', "`"$modulePath`"",
    '--python-script', "`"$smokeScript`""
)
$process = Start-Process -FilePath $slicerExecutable -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden

$latestLog = Get-ChildItem -LiteralPath $slicerLogDirectory -Filter 'Slicer_5.12.4_*.log' |
    Where-Object { $_.FullName -notin $existingLogNames } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($null -eq $latestLog) {
    throw 'Slicer khong tao log preflight moi.'
}
$marker = Select-String -LiteralPath $latestLog.FullName -Pattern 'PULMOSLICER_SMOKE_RESULT=' |
    Select-Object -Last 1
if ($null -eq $marker) {
    throw "Khong tim thay ket qua preflight trong log: $($latestLog.FullName)"
}
$json = $marker.Line.Substring($marker.Line.IndexOf('PULMOSLICER_SMOKE_RESULT=') + 25)
$result = $json | ConvertFrom-Json
$json | Set-Content -LiteralPath $evidencePath -Encoding utf8
if (-not $result.passed) {
    throw "Slicer preflight that bai. Xem: $evidencePath"
}
Write-Host "PASS. Bao cao: $evidencePath"

