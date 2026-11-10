#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail

if [[ "$(uname -s)" != Linux ]]; then
    printf '%s\n' 'Run this script inside Ubuntu/WSL2.' >&2
    exit 1
fi
if [[ "$EUID" -eq 0 ]]; then
    printf '%s\n' 'Use your regular Ubuntu account. sudo will be requested for package installation.' >&2
    exit 1
fi

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
sudo apt-get update
sudo apt-get install -y ca-certificates curl git rsync python3 build-essential

# On the first run, preserve the Windows Git history and copy the uncommitted
# bootstrap files into a new Linux checkout. Never overwrite an existing checkout.
if [[ "$repo_root" == /mnt/* ]]; then
    linux_workspace="${OPENRFSOC_WORKSPACE:-$HOME/work/OpenRFSoC}"
    if [[ -e "$linux_workspace" ]]; then
        printf 'A Linux checkout already exists: %s\nRun its scripts/bootstrap_linux.sh to continue. No files were overwritten.\n' "$linux_workspace" >&2
        exit 1
    fi
    mkdir -p -- "$(dirname -- "$linux_workspace")"
    git clone --no-hardlinks -- "$repo_root" "$linux_workspace"
    git -C "$linux_workspace" remote set-url origin https://github.com/alexist2623/OpenRFSoC.git
    rsync -a \
        --exclude='.git/' --exclude='.local/' --exclude='.venv/' \
        --exclude='build/' --exclude='runs/' --exclude='pdks/' \
        --exclude='tools/' --exclude='__pycache__/' --exclude='.pytest_cache/' \
        "$repo_root/" "$linux_workspace/"
    printf 'Created Linux working checkout: %s\n' "$linux_workspace"
    exec bash "$linux_workspace/scripts/bootstrap_linux.sh"
fi

if ! command -v nix-shell >/dev/null 2>&1; then
    if [[ -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]]; then
        # shellcheck disable=SC1091
        source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
    fi
fi

if ! command -v nix-shell >/dev/null 2>&1; then
    installer_dir="$(mktemp -d)"
    trap 'rm -f -- "$installer_dir/nix-installer.sh"; rmdir -- "$installer_dir"' EXIT
    curl --proto '=https' --tlsv1.2 -fsSL \
        https://artifacts.nixos.org/nix-installer \
        -o "$installer_dir/nix-installer.sh"
    sh "$installer_dir/nix-installer.sh" install --no-confirm --extra-conf "
extra-substituters = https://nix-cache.fossi-foundation.org
extra-trusted-public-keys = nix-cache.fossi-foundation.org:3+K59iFwXqKsL7BNu6Guy0v+uTlwsxYQxjspXzqLYQs=
extra-experimental-features = nix-command flakes
"
    # shellcheck disable=SC1091
    source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
fi

if ! command -v nix-shell >/dev/null 2>&1; then
    printf '%s\n' 'Nix is not on PATH. Open a new Ubuntu shell and rerun this script.' >&2
    exit 1
fi

# Do not modify an existing global Nix configuration. Required feature flags are
# scoped to this bootstrap and the project wrapper.
export NIX_CONFIG="${NIX_CONFIG:-}
extra-experimental-features = nix-command flakes"

cd -- "$repo_root"
mkdir -p .local
printf '%s\n' 'Loading the pinned digital/analog tool environment. Initial download may take a while.'
bash scripts/eda.sh make check
printf '\nBasic checks passed. To enter the environment:\n  cd %q\n  bash scripts/eda.sh\n\nThen run make smoke and make pnr for the PDK/physical-flow checks.\n' "$repo_root"
