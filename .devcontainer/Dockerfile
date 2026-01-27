FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Remove Yarn repository to avoid GPG key expiration issue
# Yarn v1 is deprecated, and most projects use npm/pnpm/yarn v2+ via corepack now
RUN rm -f /etc/apt/sources.list.d/yarn.list