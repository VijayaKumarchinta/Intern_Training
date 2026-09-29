# Auto-push watcher for Intern_Training
# Watches the repo, commits changes with a generated message, and pushes.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\auto_push.ps1            # foreground
#   powershell -ExecutionPolicy Bypass -File scripts\auto_push.ps1 -Once      # single pass
#   powershell -ExecutionPolicy Bypass -File scripts\auto_push.ps1 -Detached  # start hidden background job and exit
#
# Options:
#   -IntervalSeconds 30   poll interval (default 30)
#   -Once                 run one pass and exit
#   -Detached             launch a hidden background instance (survives this window)

param(
    [int]$IntervalSeconds = 30,
    [switch]$Once,
    [switch]$Detached
)

# Note: do NOT set 'Stop' globally - git writes harmless warnings to stderr
# (e.g. CRLF notices) and Stop would turn those into terminating errors.
$ErrorActionPreference = 'Continue'

if ($Detached) {
    $scriptPath = $MyInvocation.MyCommand.Path
    Start-Process -WindowStyle Hidden -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", "`"$scriptPath`"",
        "-IntervalSeconds", "$IntervalSeconds"
    )
    Write-Host "[auto-push] started detached (interval ${IntervalSeconds}s). Log: $env:TEMP\auto_push.log"
    exit 0
}

# Always operate on the repo this script lives in, regardless of cwd
$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repo

function Write-Log {
    param([string]$Message)
    $line = "[auto-push $(Get-Date -Format 'HH:mm:ss')] $Message"
    Write-Host $line
    Add-Content -Path "$env:TEMP\auto_push.log" -Value $line -ErrorAction SilentlyContinue
}

function Get-SyncSummary {
    $status = git status --porcelain 2>$null
    if (-not $status) { return $null }

    $modified = 0; $added = 0; $deleted = 0; $renamed = 0
    foreach ($line in $status) {
        $code = $line.Substring(0, 2).Trim()
        switch -Regex ($code) {
            '^(A|\?)' { $added++ }
            '^M'      { $modified++ }
            '^D'      { $deleted++ }
            '^R'      { $renamed++ }
        }
    }
    $parts = @()
    if ($added)    { $parts += "$added added" }
    if ($modified) { $parts += "$modified modified" }
    if ($renamed)  { $parts += "$renamed renamed" }
    if ($deleted)  { $parts += "$deleted deleted" }
    return ($parts -join ', ')
}

function Invoke-AutoPush {
    $summary = Get-SyncSummary
    if (-not $summary) { return }   # nothing to do

    Write-Log "changes detected ($summary) - committing"

    git add -A 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Log "ERROR: git add failed"; return }

    $msg = "Auto-sync: $summary`n`nCommitted automatically by scripts/auto_push.ps1`n`n$([char]0x1F916) Generated with Codebuff`nCo-Authored-By: Codebuff <noreply@codebuff.com>"
    git commit -m $msg 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Log "nothing to commit after add (or commit failed)"; return }

    $branch = git rev-parse --abbrev-ref HEAD
    $pushOutput = git push origin $branch 2>&1
    if ($LASTEXITCODE -eq 0) {
        $count = git rev-list "origin/$branch..HEAD" --count 2>$null
        Write-Log "pushed $count commit(s) to origin/$branch"
    } else {
        # Local commit is safe; push will be retried on a future pass
        Write-Log "push failed (offline?); will retry - $pushOutput"
    }
}

if ($Once) {
    Invoke-AutoPush
    exit 0
}

Write-Log "watching $repo (interval ${IntervalSeconds}s) - Ctrl+C to stop"
while ($true) {
    try { Invoke-AutoPush } catch { Write-Log "ERROR: $_" }
    Start-Sleep -Seconds $IntervalSeconds
}
