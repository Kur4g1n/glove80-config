{ firmwareSrc ? /opt/zmk, keymapFile ? ./glove80.keymap }:
let
  pkgs = import (firmwareSrc + "/nix/pinned-nixpkgs.nix") {};
  firmware = import firmwareSrc { inherit pkgs; };
  common = {
    keymap = keymapFile;
    kconfig = ./glove80.conf;
    extraModules = [ ../module ];
  };
  build = board: (firmware.zmk.override (common // { inherit board; })).overrideAttrs (old: {
    patches = (old.patches or []) ++ [ ../patches/rgb-startup-and-reconnect.patch ../patches/rgb-effect-cycle.patch ];
  });
  left = build "glove80_lh";
  right = build "glove80_rh";
in pkgs.runCommandNoCC "personal-glove80" {} ''
  mkdir -p $out
  cp ${left}/zmk.uf2 $out/glove80-left.uf2
  cp ${right}/zmk.uf2 $out/glove80-right.uf2
  cat ${left}/zmk.uf2 ${right}/zmk.uf2 > $out/glove80.uf2
  cp ${left}/zmk.kconfig $out/left.config
  cp ${right}/zmk.kconfig $out/right.config
''
