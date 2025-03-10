#!/usr/bin/env python3
from typing import List
import json
import os, sys
import requests

dpath = os.path.dirname(__file__)
root_dir = os.path.dirname(os.path.dirname(dpath))
data_dir = os.path.join(root_dir, 'data')

# Upload the resources
def sendResources(endpoint: str, resourceType: str, resources: List):
    url = f'{endpoint}/{resourceType}'
    for res in resources:
        response = requests.post(url, json=res)
        try:
            response.raise_for_status()
        except:
            print(f"Failed to upload resource {res}")
            print(response.text)
            sys.exit(-1)
        data = response.json()
        print(f"Resource {resourceType} uploaded, ID: {data['id']}")

if __name__ == "__main__":
    # Upload the FHIR resources from an endpoint
    import argparse
    parser = argparse.ArgumentParser(description='Dump FHIR resources from an endpoint')
    parser.add_argument('endpoint', type=str, help='The FHIR endpoint')
    parser.add_argument('resourceTypes', type=str, nargs='+', help='The JSON resources to upload')
    args = parser.parse_args()

    for res_type in args.resourceTypes:
        res_path = os.path.join(data_dir, f"{res_type}.json")

        # Load the resources
        print(f'Loading resources from {res_path}')
        with open(res_path, "r") as f:
            resources = json.load(f)

        # Determine resourceType...
        if not resources:
            print(f'No resources in {res_path}')
            sys.exit(-1)

        # Validate that all resources are of the same type
        for res in resources:
            if res["resourceType"] != res_type:
                print(f'All resources in {res_path} must be of the same type')
                sys.exit(-1)

        resources = sendResources(args.endpoint, res_type, resources)
