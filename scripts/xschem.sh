#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
pdk_cache="${PDK_ROOT:-$HOME/.cache/openrfsoc/pdks}"
pdk_revision="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["digital_smoke_pdk_revision"])' "$repo_root/env/versions.json")"
export PDK_ROOT="$pdk_cache/ciel/sky130/versions/$pdk_revision"
export PDK=sky130A
pdk_rc="$PDK_ROOT/$PDK/libs.tech/xschem/xschemrc"
if [[ ! -f "$pdk_rc" ]]; then
    printf '%s\n' 'SKY130 is not installed at the configured cache. Run bash scripts/eda.sh make smoke first.' >&2
    exit 1
fi
exec bash "$repo_root/scripts/eda.sh" xschem --rcfile "$pdk_rc" "$@"
