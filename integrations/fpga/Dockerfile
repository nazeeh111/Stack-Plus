FROM node@sha256:c8c4a7483bb04544293c82a3eecc3081c37ff5dfedcaf819d60e6e4aaad35b12
COPY debs/ /tmp/debs/
RUN --network=none set -eu; \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/libexpat1_2.8.3-1~deb13u1_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/libpython3.13-minimal_3.13.5-2+deb13u5_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/python3.13-minimal_3.13.5-2+deb13u5_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/python3-minimal_3.13.5-1_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/media-types_13.0.0_all.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/netbase_6.5_all.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/libffi8_3.4.8-2_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/libncursesw6_6.5+20250216-2_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/readline-common_8.2-6_all.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/libreadline8t64_8.2-6_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/libpython3.13-stdlib_3.13.5-2+deb13u5_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/python3.13_3.13.5-2+deb13u5_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/libpython3-stdlib_3.13.5-1_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/python3_3.13.5-1_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/iverilog_12.0-2+b1_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/libtcl8.6_8.6.16+dfsg-1_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/python3-click_8.2.0+0.really.8.1.8-1_all.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/yosys-abc_0.52-2_amd64.deb && \
    DEBIAN_FRONTEND=noninteractive dpkg --install /tmp/debs/yosys_0.52-2_amd64.deb && \
    rm -rf /tmp/debs /var/lib/apt/lists/*
ENV HOME=/output/home TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 PATH=/usr/bin:/bin
USER 1000:1000
WORKDIR /output
ENTRYPOINT ["/usr/bin/python3", "-I", "-B", "/fixture/acceptance.py"]
