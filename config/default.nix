{ firmwareSrc ? /opt/zmk, keymapFile ? ./glove80.keymap }:
let
  pkgs = import (firmwareSrc + "/nix/pinned-nixpkgs.nix") {};
  firmware = import firmwareSrc { inherit pkgs; };
  build = board: firmware.zmk.override { inherit board; keymap = keymapFile; kconfig = ./glove80.conf; };
  left = build "glove80_lh";
  right = build "glove80_rh";
in pkgs.runCommandNoCC "glove80" {} ''
  mkdir -p $out
  cat ${left}/zmk.uf2 ${right}/zmk.uf2 > $out/glove80.uf2
''
