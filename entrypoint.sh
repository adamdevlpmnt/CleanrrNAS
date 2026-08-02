#!/bin/bash

# Create group and user with specified PUID/PGID
PUID=${PUID:-568}
PGID=${PGID:-568}

groupadd -g "$PGID" mediacleaner 2>/dev/null || true
useradd -u "$PUID" -g "$PGID" -d /app -s /bin/bash mediacleaner 2>/dev/null || true

# Ensure config directory permissions
chown -R "$PUID:$PGID" /config

# Run as the specified user
exec gosu mediacleaner python -m uvicorn app.main:app --host 0.0.0.0 --port 9876
