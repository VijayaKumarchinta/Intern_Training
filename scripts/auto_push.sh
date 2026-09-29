#!/usr/bin/env bash
# Auto-push watcher for Intern_Training (bash / Git Bash version)
# Watches the repo, commits changes with a generated message, and pushes.
#
# Usage:
#   ./scripts/auto_push.sh            # watch forever (30s interval)
#   ./scripts/auto_push.sh 60         # watch with custom interval (seconds)
#   ./scripts/auto_push.sh --once     # single pass and exit

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || { echo "[auto-push] cannot find repo root"; exit 1; }

LOG="${TMPDIR:-/tmp}/auto_push.log"
log() { echo "[auto-push $(date +%H:%M:%S)] $*"; }

sync_once() {
    if [ -z "$(git status --porcelain 2>/dev/null)" ]; then
        return 0   # nothing to do
    fi

    local summary
    summary=$(git status --porcelain | awk '{
        code = substr($0, 1, 2)
        if (code ~ /\?\?|A/)  a++
        else if (code ~ /^M/) m++
        else if (code ~ /^D/) d++
        else if (code ~ /^R/) r++
    } END {
        parts = ""
        if (a) parts = parts a " added, "
        if (m) parts = parts m " modified, "
        if (r) parts = parts r " renamed, "
        if (d) parts = parts d " deleted, "
        sub(/, $/, "", parts)
        print parts
    }')

    log "changes detected (${summary:-unknown}) - committing"

    if ! git add -A >/dev/null 2>&1; then
        log "ERROR: git add failed"
        return 1
    fi

    local msg="Auto-sync: ${summary:-repo changes}

Committed automatically by scripts/auto_push.sh

🤖 Generated with Codebuff
Co-Authored-By: Codebuff <noreply@codebuff.com>"

    if ! git commit -m "$msg" >/dev/null 2>&1; then
        log "nothing to commit after add (or commit failed)"
        return 1
    fi

    local branch
    branch=$(git rev-parse --abbrev-ref HEAD)
    if git push origin "$branch" >/dev/null 2>&1; then
        log "pushed to origin/$branch"
    else
        log "push failed (offline?); will retry - local commit is safe"
    fi
}

if [[ "${1:-}" == "--once" ]]; then
    sync_once
    exit 0
fi

INTERVAL="${1:-30}"
log "watching $REPO (interval ${INTERVAL}s) - Ctrl+C to stop"
while true; do
    sync_once
    sleep "$INTERVAL"
done
