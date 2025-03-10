#!/usr/bin/env python3
import json
import os

dpath = os.path.dirname(__file__)
root_dir = os.path.dirname(os.path.dirname(dpath))
data_dir = os.path.join(root_dir, 'data')

if __name__ == "__main__":
    # Load the resources
    with open(os.path.join(data_dir, "Patient.json"), "r") as f:
        patients = json.load(f)
    with open(os.path.join(data_dir, "Organization.json"), "r") as f:
        organizations = json.load(f)
    with open(os.path.join(data_dir, "Encounter.json"), "r") as f:
        encounters = json.load(f)

    # Collect the IDs of the resources
    global_id = 1
    fhir_ids = {}

    # Hapi FHIR server seems to assign
    # IDs starting from 1, and does not allow coexistence of IDs from different resources
    for i, patient in enumerate(patients):
        fhir_ids[("Patient", patient["id"])] = str(global_id)
        global_id += 1

    for i, organization in enumerate(organizations):
        fhir_ids[("Organization", organization["id"])] = str(global_id)
        global_id += 1

    for i, encounter in enumerate(encounters):
        fhir_ids[("Encounter", encounter["id"])] = str(global_id)
        global_id += 1

    # Dump the IDs
    for res in patients:
        res.pop('id', None)
    for res in organizations:
        res.pop('id', None)
    for res in encounters:
        res.pop('id', None)

    # Patch Encounter
    for encounter in encounters:
        if encounter.get("subject"):
            encounter["subject"]["reference"] = f"Patient/{fhir_ids[('Patient', encounter['subject']['reference'].split("/")[1])]}"
        if encounter.get("serviceProvider"):
            encounter["serviceProvider"]["reference"] = f"Organization/{fhir_ids[('Organization', encounter['serviceProvider']['reference'].split("/")[1])]}"

    # Dump the patched resources again
    with open(os.path.join(data_dir, "Patient.json"), "w") as f:
        json.dump(patients, f, indent=2)
    with open(os.path.join(data_dir, "Organization.json"), "w") as f:
        json.dump(organizations, f, indent=2)
    with open(os.path.join(data_dir, "Encounter.json"), "w") as f:
        json.dump(encounters, f, indent=2)
    print("Resources patched and saved")