#!/bin/sh
set -eu
exec python3 "$(dirname "$0")/agent_base.py" "$@"
