#!/usr/bin/env bash
# Ask for port number
port=""
while [ -z "$port" ]; do
    echo -n "Enter port number: "
    read port
done

# Spawn a new container at the specified port
echo "Spawning a new FHIR container at port $port"
PYTHONPATH=. python3 fhir_manager/dockerctl.py --spawn_at_port "$port"