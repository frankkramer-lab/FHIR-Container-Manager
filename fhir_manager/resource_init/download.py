from typing import List
import json
import os
import requests

dpath = os.path.dirname(__file__)
root_dir = os.path.dirname(os.path.dirname(dpath))
data_dir = os.path.join(root_dir, 'data')

# Dump the resources
def getResources(endpoint: str, resourceType: str) -> List:
    resources = []
    url = f'{endpoint}/{resourceType}'
    while True:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        next_urls = [ link_item["url"] for link_item in data.get("link", []) if link_item.get("relation") == "next"]

        # get the resources
        resources.extend([
            res_data["resource"] for res_data in data.get('entry', [])
        ])

        if not next_urls:
            break
        url = next_urls[0]

    return resources

if __name__ == "__main__":
    # Dump the FHIR resources from an endpoint
    import argparse
    parser = argparse.ArgumentParser(description='Dump FHIR resources from an endpoint')
    parser.add_argument('endpoint', type=str, help='The FHIR endpoint')
    parser.add_argument('resourceTypes', type=str, nargs='+', help='The resource types to dump')
    parser.add_argument('--cleanIdentifiers', action='store_true', help='Clean the identifiers')
    parser.add_argument('--cleanMetas', action='store_true', help='Clean the Metas')
    parser.add_argument('--cleanTexts', action='store_true', help='Clean texts')
    args = parser.parse_args()

    for resourceType in args.resourceTypes:
        resources = getResources(args.endpoint, resourceType)

        if args.cleanIdentifiers:
            for res in resources:
                res.pop('identifier', None)
        if args.cleanMetas:
            for res in resources:
                res.pop('meta', None)
        if args.cleanTexts:
            for res in resources:
                res.pop('text', None)

        with open(os.path.join(data_dir, f'{resourceType}.json'), 'w') as f:
            json.dump(resources, f, indent=2)
        print(f'{resourceType} resources ({len(resources)}x) dumped to {resourceType}.json')
