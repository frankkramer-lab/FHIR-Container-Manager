#!/usr/bin/env bash
export PORT="${PORT:-8100}"
export ENDPOINT="${ENDPOINT:-""}"

if [ -z "$ENDPOINT" ]; then
    export ENDPOINT="http://localhost:$PORT/fhir"
    exit 1
fi

export LOCKFILE="${LOCKFILE:-""}"
if [ -z "$LOCKFILE" ]; then
    export LOCKFILE="../data/container_initializing_$PORT.lock"
fi

# Create lockfile if it doesn't exist
if [ ! -f "$LOCKFILE" ]; then
    echo "Lock file not found. Creating lock file..."
    touch "$LOCKFILE"
fi

# 5*60s = 5 minutes
MAX_WAIT=60
WAIT=0
echo "Waiting for FHIR server to start (for max. 5 min)..."
while ! curl -s "$ENDPOINT/metadata" > /dev/null; do
    sleep 5
    WAIT=$((WAIT + 1))
    if [ $WAIT -ge $MAX_WAIT ]; then
        echo "FHIR server did not start in time. Exiting..."
        exit 1
    fi
done
echo "FHIR server is responsive"

# Check if response[status] is "active"
while [ "$(curl -s "$ENDPOINT/metadata" | jq -r '.status')" != "active" ]; do
    echo "FHIR server is not active"
    sleep 1
done
echo "FHIR server is active"

echo "Importing data..."
python3 "$(dirname $0)/resource_init/upload.py" "$ENDPOINT" \
    "Patient" "Organization" "Encounter" \
    > /dev/null 2>&1

echo "Import done."

# Remove lockfile
rm -f "$LOCKFILE"
