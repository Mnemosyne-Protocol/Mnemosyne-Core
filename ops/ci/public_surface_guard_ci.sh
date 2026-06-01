#!/usr/bin/env bash
set -euo pipefail

echo "Running public_surface_guard..."

BLOCKED_PATTERNS=(
  '(^|/)\.claude(/|$)'
  '(^|/)\.cursor(/|$)'
  '(^|/)\.codex(/|$)'
  '(^|/)\.zed(/|$)'
  '(^|/)\.agents(/|$)'
  '(^|/)mnemosyne-local(/|$)'
  '(^|/).*_local\.md$'
  '(^|/).*_private\.md$'
  '(^|/)AGENT_LOCAL\.md$'
  '(^|/)TOOL_LOCAL\.md$'
  '(^|/)WORKING-CONTEXT\.local\.md$'
  '(^|/)\.env(\..*)?$'
  '(^|/).*\.pem$'
  '(^|/).*\.key$'
  '(^|/).*\.p12$'
  '(^|/).*\.pfx$'
)

SECRET_PATTERNS=(
  'AKIA[0-9A-Z]{16}'
  'ghp_[A-Za-z0-9]{36,}'
  'github_pat_[A-Za-z0-9_]{20,}'
  'sk-[A-Za-z0-9]{20,}'
  'AIza[0-9A-Za-z_-]{35}'
  '-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----'
)

SECRET_REGEX="$(IFS='|'; echo "${SECRET_PATTERNS[*]}")"

if ! git diff --cached --name-only --diff-filter=ACMR | grep -q .; then
  echo "No staged files."
  exit 0
fi

while IFS= read -r -d '' file; do
  for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if [[ "$file" =~ $pattern ]]; then
      echo "ERROR: blocked file staged for commit: $file"
      exit 1
    fi
  done

  if git diff --cached --no-color --unified=0 --text -- "$file" \
      | grep '^+' \
      | grep -vE '^\+\+\+' \
      | sed 's/^+//' \
      | grep -Eq "$SECRET_REGEX"; then
    echo "ERROR: possible secret detected in newly added content: $file"
    exit 1
  fi

done < <(git diff --cached --name-only --diff-filter=ACMR -z)

echo "public_surface_guard passed."
exit 0