# Pinned firmware: MoErgo ZMK with per-layer RGB (moergo-sc/zmk PR 36, darknao's branch).
FROM nixos/nix:2.24.11@sha256:4bfe741027f0bfbef745862cbf3b5f424ee99801c04138146c0000a28759636d
ARG ZMK_REPO=https://github.com/darknao/zmk.git
ARG ZMK_REV=db2ba9fcd3dec4c7afcf171f123585a9f8292595
ENV NIX_CONFIG="sandbox = false"
RUN git init -q /opt/zmk && cd /opt/zmk && git fetch -q --depth 1 "$ZMK_REPO" "$ZMK_REV" && git checkout -q --detach FETCH_HEAD
WORKDIR /workspace
ENTRYPOINT ["sh", "-c", "nix-build config --arg keymapFile \"$KEYMAP\" -o /tmp/result && cp /tmp/result/glove80.uf2 build/ && chmod u+w build/glove80.uf2"]
