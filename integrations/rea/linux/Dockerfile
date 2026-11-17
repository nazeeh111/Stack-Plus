FROM node@sha256:c8c4a7483bb04544293c82a3eecc3081c37ff5dfedcaf819d60e6e4aaad35b12
COPY debs/ /tmp/debs/
RUN --network=none DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/*.deb && rm -rf /tmp/debs /var/lib/apt/lists/*
COPY rea/ /opt/rea/
COPY ghidra/ /opt/ghidra/
COPY runner.mjs /opt/nstack/runner.mjs
ENV HOME=/output/home XDG_CONFIG_HOME=/output/home/config XDG_CACHE_HOME=/output/home/cache TMPDIR=/tmp CI=1 NO_UPDATE_NOTIFIER=1 JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 GHIDRA_INSTALL_DIR=/opt/ghidra GHIDRA_HEADLESS_MAXMEM=512M REA_ANALYSIS_PROVIDER=ghidra PATH=/usr/local/bin:/usr/lib/jvm/java-21-openjdk-amd64/bin:/usr/bin:/bin
USER 1000:1000
WORKDIR /output
ENTRYPOINT ["/usr/local/bin/node","/opt/nstack/runner.mjs"]
CMD ["mcp"]
