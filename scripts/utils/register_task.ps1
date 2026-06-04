# register_task.ps1
# Run once to set up scheduled task.
# .\scripts\utils\register_task.ps1

$pythonPath = (Get-Command python).Source
$scriptPath = Join-Path $PSScriptRoot "sync.py"
$logPath    = Join-Path $PSScriptRoot "sync.log"
$taskName   = "ProjectSyncUtil"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "`"$scriptPath`" >> `"$logPath`" 2>&1"

$triggers = @(
    $(New-ScheduledTaskTrigger -Daily -At "09:00AM"),
    $(New-ScheduledTaskTrigger -Daily -At "02:00PM"),
    $(New-ScheduledTaskTrigger -Daily -At "08:30PM")
)

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Principal $principal `
    -Description "Project sync utility" `
    -Force

Write-Host "Task '$taskName' registered. Runs at 09:00, 14:00, 20:30 daily."
Write-Host "Log: $logPath"
