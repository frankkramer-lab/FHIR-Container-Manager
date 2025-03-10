#!/usr/bin/env bash
export PORT_RANGE="${PORT_RANGE:-8100-9000}"

# Setup DB
PYTHONPATH=. python3 fhir_manager/dockerctl.py --reset_db

# Run Flask app in production mode
gunicorn 'fhir_manager.web.fhirctl:app' -w 4 --timeout 600 --bind "0.0.0.0:8000" --log-level info --access-logfile -