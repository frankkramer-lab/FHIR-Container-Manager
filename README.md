# FHIR-Server Container Manager

The project provides a basic API and web interface to dynamically provide freshly initialized FHIR servers on individual ports.

Each FHIR container is loaded with sample data during the initialization.

## How to Use

### Setup
1. [Once] Install Docker (and join the docker group using `sudo usermod -aG docker $USER`), and install the following applications: `curl`,`jq`, `python3`
2. [Once] Install the dependencies using `python3 -m venv env && source env/bin/activate && python3 -m pip install -r requirements.txt && deactivate`
3. [Once] Download the Bootstrap files using `cd fhir_manager/web && ./loadBootstrap.sh && cd ../..`
4. Optional: Open a new tmux session using `tmux new -s fhirmanager`
5. [Once] Enter the virtual env using `source env/bin/activate`
6. Launch the server as follows:
```bash
export PORT_RANGE=8100-9000
# The FHIR Manager runs on port 8000
./run_productive.sh

# OR use the DEBUG mode (runs on port 5000):
./run_debug.sh
```
7. The web page should be available now.

Make sure that no firewall is blocking your access attempts.

**Note:** The FHIR resources from `data/Patient.json`, `data/Organization.json` and `data/Encounter.json`` are uploaded to the spawned container instances as initial data.

### Local scripts

**List all containers**
```bash
./listSpawnedContainers.sh
```

**Removing all dead containers**
```bash
./purgeAllDeadContainers.sh
```

**Removing ALL containers**
```bash
./purgeAllSpawnedContainers.sh
```

The initial FHIR resources were taken from the FHIR server from the FHIR exercise. The resources were downloaded using the script `./dumpResources.sh`.
Since HAPI FHIR does not seem to assign resource *type-specific* ID values, the references from `Encounter` are changed to potential ID values that are expected to be assigned by the newly spawned HAPI FHIR instances.

