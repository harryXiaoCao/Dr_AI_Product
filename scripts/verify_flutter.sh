#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_root/apps/dr_ai_app"
verification_root="$(mktemp -d "${TMPDIR:-/tmp}/dr_ai_flutter_verify.XXXXXX")"
verification_dir="$verification_root/dr_ai_app"

cleanup() {
  rm -rf "$verification_root"
}
trap cleanup EXIT

if command -v flutter >/dev/null 2>&1; then
  flutter_bin="$(command -v flutter)"
elif [[ -x "$HOME/development/flutter/bin/flutter" ]]; then
  flutter_bin="$HOME/development/flutter/bin/flutter"
else
  echo "Flutter was not found on PATH or at ~/development/flutter/bin/flutter." >&2
  exit 127
fi

mkdir -p "$verification_dir"
rsync -a \
  --exclude '.dart_tool/' \
  --exclude '.flutter-plugins' \
  --exclude '.flutter-plugins-dependencies' \
  --exclude '.idea/' \
  --exclude '.gradle/' \
  --exclude 'build/' \
  --exclude 'coverage/' \
  --exclude 'android/.cxx/' \
  --exclude 'android/app/src/main/java/io/flutter/plugins/GeneratedPluginRegistrant.java' \
  --exclude 'android/local.properties' \
  --exclude 'ios/Flutter/ephemeral/' \
  --exclude 'ios/Flutter/Generated.xcconfig' \
  --exclude 'ios/Flutter/flutter_export_environment.sh' \
  --exclude 'ios/Pods/' \
  --exclude 'ios/Runner/GeneratedPluginRegistrant.*' \
  --exclude '*.iml' \
  "$source_dir/" "$verification_dir/"

cd "$verification_dir"
"$flutter_bin" pub get
"$flutter_bin" analyze
"$flutter_bin" test
