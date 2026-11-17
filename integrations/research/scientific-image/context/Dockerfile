# Exact official source base is verified against BASE-ACQUISITION.json before build.
FROM nstack-research-python-base:c61cffc3
ENV DEBIAN_FRONTEND=noninteractive container=docker PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/wheelhouse HOME=/tmp/agent-home
COPY debs/ /opt/offline-debs/
COPY wheelhouse/ /opt/wheelhouse/
COPY requirements-linux.lock bootstrap.lock /opt/
COPY notices/ /opt/research-notices/
COPY policy/policy-rc.d /usr/sbin/policy-rc.d
RUN chmod 755 /usr/sbin/policy-rc.d \
    && dpkg -i /opt/offline-debs/*.deb \
    && rm -rf /opt/offline-debs /var/lib/apt/lists/* \
    && python -m pip --isolated --disable-pip-version-check --no-input --keyring-provider disabled install --no-index --no-deps --find-links=/opt/wheelhouse --require-hashes -r /opt/requirements-linux.lock -r /opt/bootstrap.lock \
    && python -m pip --isolated --disable-pip-version-check check
COPY runtime/ /opt/codex/
COPY policy/requirements.toml /etc/codex/requirements.toml
ENTRYPOINT []
CMD []
