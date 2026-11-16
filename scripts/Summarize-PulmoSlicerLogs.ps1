[CmdletBinding()]
param(
    [string]$LogDirectory = (Join-Path $env:LOCALAPPDATA 'PulmoSlicerAI\logs')
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $LogDirectory -PathType Container)) {
    throw "Log directory does not exist: $LogDirectory"
}

$summaries = foreach ($file in Get-ChildItem -LiteralPath $LogDirectory -Filter 'run-*.jsonl') {
    $records = @(
        Get-Content -LiteralPath $file.FullName |
            Where-Object { $_.Trim() } |
            ForEach-Object { $_ | ConvertFrom-Json }
    )
    $start = $records | Where-Object event -eq 'run_started' | Select-Object -First 1
    $finish = $records | Where-Object event -eq 'run_finished' | Select-Object -Last 1
    $resources = @($records | Where-Object event -eq 'resources')
    $cpuValues = @($resources | Where-Object { $null -ne $_.cpu_percent } | ForEach-Object cpu_percent)
    $ramValues = @($resources | Where-Object { $null -ne $_.memory_percent } | ForEach-Object memory_percent)

    [pscustomobject]@{
        File = $file.Name
        RunId = $start.run_id
        Task = $start.task
        Success = $finish.success
        ElapsedSeconds = $finish.elapsed_seconds
        SliceStride = $start.slice_stride
        ResourcePolicy = $start.resource_policy
        RequestedThreads = $start.requested_threads
        ResampleWorkers = $start.resample_workers
        SavingWorkers = $start.saving_workers
        AverageSystemCpuPercent = if ($cpuValues.Count) {
            [math]::Round(($cpuValues | Measure-Object -Average).Average, 1)
        } else { $null }
        PeakSystemCpuPercent = if ($cpuValues.Count) {
            ($cpuValues | Measure-Object -Maximum).Maximum
        } else { $null }
        PeakSystemRamPercent = if ($ramValues.Count) {
            ($ramValues | Measure-Object -Maximum).Maximum
        } else { $null }
    }
}

$summaries | Sort-Object File | Format-Table -AutoSize
