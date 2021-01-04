#!/usr/bin/env bash
set -euo pipefail


# Give permission to taiga:taiga after mounting volumes
echo Give permission to taiga:taiga
chown -R taiga:taiga /taiga-protected

# Start Taiga processes
echo Starting Taiga Protected

exec gosu taiga gunicorn server:app \
    --name taiga_protected \
    --bind 0.0.0.0:8003 \
    --workers 4 \
    --worker-tmp-dir /dev/shm \
    --max-requests 3600 \
    --max-requests-jitter 360 \
    --timeout 60 \
    --log-level=debug \
    --access-logfile - \
    "$@"
