FROM nixos/nix:2.24.11@sha256:4bfe741027f0bfbef745862cbf3b5f424ee99801c04138146c0000a28759636d

ENV NIX_CONFIG="sandbox = false"
WORKDIR /workspace
COPY firmware.lock.json /opt/firmware.lock.json
# Only the selected revision is fetched; no rolling branches or unrelated builds.
RUN git init /opt/zmk && cd /opt/zmk \
    && git remote add origin https://github.com/darknao/zmk.git \
    && git fetch --depth 1 origin db2ba9fcd3dec4c7afcf171f123585a9f8292595 \
    && git checkout --detach FETCH_HEAD
ENTRYPOINT ["bash", "/workspace/scripts/container-build.sh"]
