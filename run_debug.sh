#!/usr/bin/env bash
export PORT_RANGE="${PORT_RANGE:-8100-9000}"

# Setup DB
PYTHONPATH=. python3 fhir_manager/dockerctl.py --reset_db

# Run Flask app in debug mode
flask --app fhir_manager.web.fhirctl run --debug --port 5000 --host 127.0.0.1