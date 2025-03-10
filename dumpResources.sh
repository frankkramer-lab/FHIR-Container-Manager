#!/usr/bin/env bash
PYTHONPATH=. python3 fhir_manager/resource_init/download.py 'http://vm21-misit.informatik.uni-augsburg.de:8090/hapi-fhir-jpaserver/fhir' \
    'Patient' 'Encounter' 'Organization' \
    --cleanIdentifiers \
    --cleanMetas \
    --cleanTexts

# Fix IDs
PYTHONPATH=. python3 fhir_manager/resource_init/id_fix.py