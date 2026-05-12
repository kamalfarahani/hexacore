#!/bin/bash

# This script sets up the environment for running tests with Podman instead of Docker

systemctl --user enable --now podman.socket
export DOCKER_HOST=unix:///run/user/$(id -u)/podman/podman.sock
export TESTCONTAINERS_RYUK_DISABLED=true  # Ryuk often misbehaves on Podman

uv run pytest --cov=hexacore