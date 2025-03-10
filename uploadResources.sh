#!/usr/bin/env bash
PYTHONPATH=. python3 fhir_manager/resource_init/upload.py 'http://localhost:8080/fhir' \
    "Patient" "Organization" "Encounter"
