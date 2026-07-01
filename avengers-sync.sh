#!/usr/bin/env bash
#
# avengers-sync — propagate plugin edits from this portable master to the
# active Claude Code install, and push them to the GitHub repo.
#
#   Usage:  ./avengers-sync.sh ["commit message"]
#
# What it does, in order:
#   1. Commits any working-tree changes in this master repo (message optional).
#   2. Pushes to 'origin' if a remote is configured.
#   3. Mirrors the master into the active plugin dir (rsync, excluding .git).
#   4. Commits in the active plugin so its marketplace-source HEAD is current.
#
# The active plugin dir defaults to ~/.claude/plugins/avengers-dev and can be
# overridden with the AVENGERS_ACTIVE_DIR env var. Paths are derived from the
# script's own location, so this stays portable across machines.
#
set -euo pipefail

MASTER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTIVE="${AVENGERS_ACTIVE_DIR:-$HOME/.claude/plugins/avengers-dev}"
MSG="${1:-chore: update avengers-dev plugin}"

# Explicit content paths (avoids staging stray/untracked junk).
PATHS=(.claude .claude-plugin agents equipment hooks personas references \
       scripts skills CLAUDE.md README.md TESTING.md settings.json \
       LICENSE .gitignore avengers-sync.sh)

echo "master: $MASTER"
echo "active: $ACTIVE"
echo ""

# 1. Commit master changes
cd "$MASTER"
git add "${PATHS[@]}"
if git diff --cached --quiet; then
  echo "• master: nothing to commit"
else
  git commit --no-gpg-sign -m "$MSG"
  echo "✓ master: committed — $MSG"
fi

# 2. Push if a remote exists
if git remote get-url origin >/dev/null 2>&1; then
  git push origin HEAD && echo "✓ pushed to origin"
else
  echo "• no 'origin' remote — skipped push"
fi

# 3. Mirror into the active plugin
if [[ -d "$ACTIVE" ]]; then
  rsync -a --delete --exclude '.git' "$MASTER/" "$ACTIVE/"
  echo "✓ synced master → active plugin"

  # 4. Keep the active plugin's git HEAD current (it's the marketplace source)
  if git -C "$ACTIVE" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$ACTIVE" add "${PATHS[@]}" 2>/dev/null || true
    if ! git -C "$ACTIVE" diff --cached --quiet; then
      git -C "$ACTIVE" commit --no-gpg-sign -m "chore: sync from master" >/dev/null
      echo "✓ active plugin: committed sync"
    fi
  fi
  echo ""
  echo "→ Restart Claude Code to load the updated plugin."
else
  echo "• no active plugin dir at $ACTIVE — skipped local sync"
fi
