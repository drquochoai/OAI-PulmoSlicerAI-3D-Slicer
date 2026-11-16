[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$SlicerHome = 'D:\Program Files\3D Slicer 5.12.4',
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'PulmoSlicerAI\5.12.4')
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$sourceModule = Join-Path $repositoryRoot 'slicer_extension\PulmoSlicerAI'
$sourceEngine = Join-Path $repositoryRoot 'pulmoslicer_engine'
$slicerExecutable = Join-Path $SlicerHome 'Slicer.exe'
$targetModule = Join-Path $InstallRoot 'slicer-module'
$targetEngine = Join-Path $targetModule 'pulmoslicer_engine'
$launcher = Join-Path $InstallRoot 'Run-PulmoSlicerAI.ps1'

if (-not (Test-Path -LiteralPath $slicerExecutable -PathType Leaf)) {
    throw "Khong tim thay Slicer.exe tai: $slicerExecutable"
}
if (-not (Test-Path -LiteralPath $sourceModule -PathType Container)) {
    throw "Thieu source module: $sourceModule"
}
if (Test-Path -LiteralPath $InstallRoot) {
    throw "Thu muc cai da ton tai: $InstallRoot. Khong ghi de tu dong; hay doi InstallRoot hoac sao luu ban cu."
}

if ($PSCmdlet.ShouldProcess($InstallRoot, 'Cai PulmoSlicer AI cho nguoi dung hien tai')) {
    New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
    Copy-Item -LiteralPath $sourceModule -Destination $targetModule -Recurse -Force
    Copy-Item -LiteralPath $sourceEngine -Destination $targetEngine -Recurse -Force

    $launcherContent = @(
        '$ErrorActionPreference = ''Stop'''
        '& ''__SLICER_EXECUTABLE__'' --additional-module-paths ''__MODULE_PATH__'' --python-code "slicer.util.selectModule(''PulmoSlicerAI'')"'
    ) -join [Environment]::NewLine
    $launcherContent = $launcherContent.Replace('__SLICER_EXECUTABLE__', $slicerExecutable)
    $launcherContent = $launcherContent.Replace('__MODULE_PATH__', $targetModule)
    Set-Content -LiteralPath $launcher -Value $launcherContent -Encoding utf8

    & (Join-Path $PSScriptRoot 'Test-SlicerEnvironment.ps1') -SlicerHome $SlicerHome
    Write-Host "Da cai vao: $InstallRoot"
    Write-Host "Lan sau chay: powershell -ExecutionPolicy Bypass -File `"$launcher`""
}
