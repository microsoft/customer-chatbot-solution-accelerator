FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# Route package managers through Microsoft proxy feeds so builds work on the
# Microsoft-managed network where the public npm/PyPI URLs are blocked.
ENV NPM_CONFIG_REGISTRY=https://pkgs.dev.azure.com/ms-feed-12/1es-public/_packaging/npm-public/npm/registry/
ENV PIP_INDEX_URL=https://packagefeedproxy.microsoft.io/pypi/simple/

# Remove Yarn repository to avoid GPG key expiration issue
# Yarn v1 is deprecated, and most projects use npm/pnpm/yarn v2+ via corepack now
RUN rm -f /etc/apt/sources.list.d/yarn.list