FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# Route package managers through Microsoft proxy feeds so builds work on the
# Microsoft-managed network where the public npm/PyPI URLs are blocked.
ENV NPM_CONFIG_REGISTRY=https://pkgs.dev.azure.com/ms-feed-12/1es-public/_packaging/npm-public/npm/registry/
ENV PIP_INDEX_URL=https://packagefeedproxy.microsoft.io/pypi/simple/

# Remove third-party apt repositories whose GPG keys expire and break
# "apt-get update" during dev container feature installation.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/*yarn* 2>/dev/null || true