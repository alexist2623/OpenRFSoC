# The upstream commit includes its own flake.lock, pinning transitive tools.
let
  versions = builtins.fromJSON (builtins.readFile ./env/versions.json);
  upstream = builtins.getFlake "github:librelane/librelane/${versions.librelane.commit}";
  pkgs = upstream.legacyPackages.${builtins.currentSystem};
in
pkgs.librelane-shell.override {
  extra-packages = with pkgs; [
    gnumake
    gcc
    verilator
    ngspice
    xschem
  ];
  extra-python-packages = ps: with ps; [ cocotb pytest numpy matplotlib ];
}
