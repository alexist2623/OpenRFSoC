#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if ! command -v nix-shell >/dev/null 2>&1; then
    if [[ -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]]; then
        # shellcheck disable=SC1091
        source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
    fi
fi
if ! command -v nix-shell >/dev/null 2>&1; then
    printf '%s\n' 'Run bash scripts/bootstrap_linux.sh in Ubuntu first.' >&2
    exit 1
fi
export NIX_CONFIG="${NIX_CONFIG:-}
extra-experimental-features = nix-command flakes"
# This flake-based environment needs no global nixpkgs channel. Select the
# launcher explicitly instead of letting nix-shell search for <nixpkgs>.
export NIX_BUILD_SHELL="$(command -v bash)"
cd -- "$repo_root"
if [[ $# -eq 0 ]]; then
    exec nix-shell shell.nix
fi
printf -v command_line '%q ' "$@"
exec nix-shell shell.nix --run "$command_line"
