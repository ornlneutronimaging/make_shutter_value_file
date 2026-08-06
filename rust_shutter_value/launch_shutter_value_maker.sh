#!/usr/bin/env bash
# Launch the Shutter Value Maker GUI, rebuilding first if the sources changed.
#
# Usage: ./launch_shutter_value_maker.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BINARY="$REPO_DIR/target/release/shutter_value_maker"

# GUI apps need a display (e.g. a ThinLinc session).
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo "Error: no display found (DISPLAY/WAYLAND_DISPLAY unset)." >&2
    echo "Run this from a graphical session such as ThinLinc." >&2
    exit 1
fi

# Rebuild if the binary is missing or any source/manifest file is newer.
needs_build=false
if [[ ! -x "$BINARY" ]]; then
    needs_build=true
elif [[ -n "$(find "$REPO_DIR/src" "$REPO_DIR/Cargo.toml" -newer "$BINARY" -print -quit 2>/dev/null)" ]]; then
    needs_build=true
fi

if $needs_build; then
    CARGO="$(command -v cargo || true)"
    [[ -z "$CARGO" && -x "$HOME/.cargo/bin/cargo" ]] && CARGO="$HOME/.cargo/bin/cargo"
    if [[ -z "$CARGO" ]]; then
        echo "Error: binary is out of date and cargo was not found to rebuild it." >&2
        exit 1
    fi
    echo "Building shutter_value_maker (release)..."
    (cd "$REPO_DIR" && "$CARGO" build --release)
fi

exec "$BINARY" "$@"
