# Auto-push watcher for Intern_Training
# Git-autosave mode: reacts the moment a file is saved and commits + pushes instantly.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\auto_push.ps1 -Detached  # start hidden background watcher
#   powershell -ExecutionPolicy Bypass -File scripts\auto_push.ps1 -Stop      # stop the background watcher
#   powershell -ExecutionPolicy Bypass -File scripts\auto_push.ps1 -Once      # single pass, exit
#
# How it works:
#   Watches the filesystem (event-driven, no polling). After a save, waits 1.5s of
#   quiet (so a burst of saves becomes ONE commit), then commits + pushes.
#   Self-healing: every loop it also retries unpushed commits (offline recovery),
#   and a 60s safety sweep catches anything the events missed.

param(
    [switch]$Once,
    [switch]$Detached,
    [switch]$Stop
)

# Note: do NOT set 'Stop' globally - git writes harmless warnings to stderr
# (e.g. CRLF notices) and Stop would turn those into terminating errors.
$ErrorActionPreference = 'Continue'
$env:GIT_TERMINAL_PROMPT = '0'   # never hang waiting for a credential prompt

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

function Invoke-Push {
    $branch = git rev-parse --abbrev-ref HEAD
    $pending = [int](git rev-list "origin/$branch..HEAD" --count 2>$null)
    if ($pending -eq 0) { return $true }

    # Run push in a job with a hard timeout: a stalled connection or a hidden
    # credential prompt would otherwise wedge the whole watcher forever.
    $job = Start-Job -ScriptBlock {
        param($b)
        $env:GIT_TERMINAL_PROMPT = '0'
        git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=20 push origin $b 2>&1
        "PUSH_EXIT:$LASTEXITCODE"
    } -ArgumentList $branch

    if (Wait-Job $job -Timeout 45) {
        $out = Receive-Job $job
        Remove-Job $job -Force
        $exitLine = $out | Where-Object { $_ -like 'PUSH_EXIT:*' } | Select-Object -Last 1
        $code = 1
        if ($exitLine) { $code = [int]($exitLine -replace 'PUSH_EXIT:', '') }
        if ($code -eq 0) {
            Write-Log "pushed $pending commit(s) to origin/$branch"
            return $true
        }
        $rest = @($out | Where-Object { $_ -ne $exitLine }) -join ' '
        # Local commit is safe; retried on the next loop
        Write-Log "push failed; will retry - $rest"
        return $false
    }

    Stop-Job $job
    Remove-Job $job -Force
    Write-Log "push timed out after 45s; will retry"
    return $false
}

function Invoke-AutoPush {
    $summary = Get-SyncSummary
    if ($summary) {
        Write-Log "changes detected ($summary) - committing"
        git add -A 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Log "ERROR: git add failed"; return }

        $msg = "Auto-sync: $summary`n`nCommitted automatically by scripts/auto_push.ps1`n`n$([char]::ConvertFromUtf32(0x1F916)) Generated with Codebuff`nCo-Authored-By: Codebuff <noreply@codebuff.com>"
        git commit -m $msg 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Log "nothing to commit after add (or commit failed)" }
    }
    # Always attempt push - this also retries unpushed commits from earlier failures
    Invoke-Push | Out-Null
}

if ($Stop) {
    $pidFile = "$env:TEMP\auto_push.pid"
    if (Test-Path $pidFile) {
        $watcherPid = Get-Content $pidFile
        try {
            Stop-Process -Id $watcherPid -Force -ErrorAction Stop
            Write-Log "stopped watcher (pid $watcherPid)"
        } catch {
            Write-Log "watcher pid $watcherPid was not running"
        }
        Remove-Item $pidFile -ErrorAction SilentlyContinue
    } else {
        Write-Log "no running watcher found"
    }
    exit 0
}

if ($Once) {
    Invoke-AutoPush
    exit 0
}

if ($Detached) {
    $scriptPath = $MyInvocation.MyCommand.Path
    Start-Process -WindowStyle Hidden -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", "`"$scriptPath`""
    )
    Write-Host "[auto-push] started detached. Log: $env:TEMP\auto_push.log  Stop: auto_push.ps1 -Stop"
    exit 0
}

# ---- Instant mode: event-driven, pushes the moment a file is saved ----
"$PID" | Set-Content "$env:TEMP\auto_push.pid"

$fsw = New-Object System.IO.FileSystemWatcher
$fsw.Path = $repo
$fsw.IncludeSubdirectories = $true
$fsw.InternalBufferSize = 65536
$fsw.EnableRaisingEvents = $true

Write-Log "watching $repo - will commit+push right after each save (stop: auto_push.ps1 -Stop)"

Invoke-AutoPush          # heal anything changed before startup

$DEBOUNCE_MS = 1500       # quiet period after the last save before committing
$SAFETY_SWEEP_MS = 60000  # fallback sweep in case an event is ever missed

while ($true) {
    $result = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::All, $SAFETY_SWEEP_MS)
    if (-not $result.TimedOut) {
        # A save happened. Wait until the filesystem has been quiet for DEBOUNCE_MS,
        # so a burst of quick saves collapses into a single commit.
        do {
            Start-Sleep -Milliseconds $DEBOUNCE_MS
            $quiet = $fsw.WaitForChanged([System.IO.WatcherChangeTypes]::All, $DEBOUNCE_MS)
        } while (-not $quiet.TimedOut)
    }
    try { Invoke-AutoPush } catch { Write-Log "ERROR: $_" }
}
