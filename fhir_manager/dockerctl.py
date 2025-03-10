import time
import os
import docker
import subprocess
import sqlite3
from typing import Optional

from fhir_manager.resource_init.upload import sendResources

dpath = os.path.dirname(__file__)
root_dir = os.path.dirname(dpath)
data_dir = os.path.join(root_dir, 'data')

client = docker.from_env()

CONTAINER_PREFIX="fhirmanager_managed_"
CONTAINER_HOSTPORT_KEY = "8080/tcp"
CONTAINER_IMAGE = "hapiproject/hapi:v8.0.0"

def __get_db_conn__():
    db_path = os.path.join(data_dir, "available_ports.db")
    return sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES
    )

def get_fhir_container_infos():
    managed_containers = []
    # Try to get the containers
    n_tries = 0
    max_tries = 20
    while n_tries < max_tries:
        try:
            containers = client.containers.list(all=True)
            break
        except Exception as e:
            print(f"An error occurred: {e}. Wait a bit and try again...")
            time.sleep(0.100)
            n_tries += 1
    for container in containers:
        if container.name.startswith(CONTAINER_PREFIX):

            host_ports = container.ports.get(CONTAINER_HOSTPORT_KEY, [])
            try:    host_port = int(host_ports[0]['HostPort'])
            except: host_port = None

            # Modes: created, restarting, running, removing, paused, exited, or dead
            managed_containers.append({
                "name": container.name,
                "id": container.id,
                "host_port": host_port,
                "running": container.status == "running",
                "initializing": os.path.exists(f"{data_dir}/container_initializing_{host_port}.lock")
            })
    return managed_containers

def purge_dead_fhir_containers(db_conn = None):
    if db_conn is None: db_conn = __get_db_conn__()

    containers = get_fhir_container_infos()
    for container in containers:
        if not container["running"]:
            try:    client.containers.get(container["id"]).remove(force=True)
            except: pass
            try:    os.remove(f"{data_dir}/container_initializing_{container['host_port']}.lock")
            except: pass
            # Add port back to the database pool
            try:    addPortToDatabase(container["host_port"], db_conn=db_conn)
            except: pass

# https://stackoverflow.com/a/52872579
def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def setup_new_fhir_container(port: int, waiting: bool = False) -> bool:
    # Check if the port is in use
    if is_port_in_use(port):
        print(f"Port {port} is already in use")
        return False

    # Create the container
    container = client.containers.run(
        CONTAINER_IMAGE,
        remove=True,
        detach=True,
        ports={CONTAINER_HOSTPORT_KEY: port},
        # Disable caching to avoid concurrency issues
        environment={
            "hapi.fhir.reuse_cached_search_results_millis": "0"
        },
        name=f'{CONTAINER_PREFIX}{port}'
    )

    # Wait till the container is visible in the container list
    while True:
        containers = get_fhir_container_infos()
        if any([container.id == existing_container["id"] for existing_container in containers]):
            break
        time.sleep(0.100)

    # Initialize container...
    init_script = os.path.join(dpath, "docker_container_init.sh")
    init_lockfile = f"{data_dir}/container_initializing_{port}.lock"

    sub_env = os.environ.copy()
    sub_env["PORT"] = str(port)
    sub_env["ENDPOINT"] = f"http://localhost:{port}/fhir"
    sub_env["LOCKFILE"] = init_lockfile
    open(init_lockfile, 'a').close()

    initialization_process = subprocess.Popen([
        "bash", init_script],
        env=sub_env,
        preexec_fn=os.setsid
    )
    if waiting:
        initialization_process.communicate()

    return True

def kill_and_remove_all_fhir_containers(db_conn = None):
    if db_conn is None: db_conn = __get_db_conn__()

    containers = get_fhir_container_infos()
    for container in containers:
        if container.get("running"):
            print(f"Trying to kill the container: {container['name']} ({container['id']})")
            try:    client.containers.get(container["id"]).kill()
            except: pass

        print(f"Trying to remove the container: {container['name']} ({container['id']})")
        try:    client.containers.get(container["id"]).remove(force=True)
        except: pass
        try:    os.remove(f"{data_dir}/container_initializing_{container['host_port']}.lock")
        except: pass
        # Add port back to the database pool
        try:    addPortToDatabase(container["host_port"], db_conn=db_conn)
        except: pass

def delete_fhir_container(port: int, db_conn = None, yield_port: bool = True):
    if db_conn is None: db_conn = __get_db_conn__()

    containers = get_fhir_container_infos()
    containers = [container for container in containers if container["host_port"] == port]
    if not containers:
        print(f"Container with ID {id} not found")
        return

    for container in containers:
        print(f"Container found: {container['name']} ({container['id']}) - {port} - {'running' if container['running'] else 'stopped'}")
        if container.get("running"):
            print(f"Trying to kill the container: {container['name']} ({container['id']})")
            try:    client.containers.get(container["id"]).kill()
            except: pass

        print(f"Trying to remove the container: {container['name']} ({container['id']})")
        try:    client.containers.get(container["id"]).remove(force=True)
        except: pass
        try:    os.remove(f"{data_dir}/container_initializing_{container['host_port']}.lock")
        except: pass
        if yield_port:
            # Add port back to the database pool
            try:    addPortToDatabase(container["host_port"], db_conn=db_conn)
            except: pass

def reset_fhir_container(port: int, db_conn = None):
    if db_conn is None: db_conn = __get_db_conn__()

    # Delete the container but keep the port
    delete_fhir_container(port, db_conn=db_conn, yield_port=False)
    print(f"Setting up a new container at port {port}")
    setup_new_fhir_container(port)

def resetDatabasePortTable(port_range, db_conn = None):
    if db_conn is None: db_conn = __get_db_conn__()

    # Search for open ports
    available_ports = []
    for port in port_range:
        if not is_port_in_use(port):
            available_ports.append(port)

    # Create a cursor
    db_cursor = db_conn.cursor()

    # Drop the table if it exists
    db_cursor.execute("DROP TABLE IF EXISTS ports")

    # Create the table again
    db_cursor.execute("CREATE TABLE ports (id INTEGER PRIMARY KEY, port INTEGER UNIQUE)")

    # Add all available ports to the database
    for port in available_ports:
        db_cursor.execute("INSERT INTO ports (port) VALUES (?)", (port,))

    # Commit the changes
    db_conn.commit()

def addPortToDatabase(port, db_conn = None):
    if db_conn is None: db_conn = __get_db_conn__()

    db_cursor = db_conn.cursor()
    db_cursor.execute("INSERT INTO ports (port) VALUES (?)", (port,))
    db_conn.commit()

def getAvailablePortFromDatabase(desired_port: Optional[int] = None, db_conn = None) -> Optional[int]:
    if db_conn is None: db_conn = __get_db_conn__()

    db_cursor = db_conn.cursor()
    n_tries = 0
    max_tries = 20
    while n_tries < max_tries:
        try:
            # Start a transaction
            db_conn.execute('BEGIN TRANSACTION;')

            # Query to check if there are rows in the table
            if desired_port is not None and desired_port > 0:
                db_cursor.execute(f"SELECT id, port FROM ports WHERE port = ? LIMIT 1;", (desired_port,))
            else:
                db_cursor.execute(f"SELECT id, port FROM ports LIMIT 1;")
            row = db_cursor.fetchone()

            if row:
                # If there's a row, remove it and yield the row
                db_cursor.execute(f"DELETE FROM ports WHERE ROWID = ?;", (row[0],))
                db_conn.commit()  # Commit the transaction
                return row[1]
            else:
                # If no rows, yield None
                return None

        except sqlite3.Error as e:
            # In case of an error, rollback the transaction
            db_conn.rollback()
            print(f"An SQLite error occurred: {e}. Wait a bit and try again...")
            time.sleep(0.25)
            n_tries += 1

    return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Manage FHIR containers')
    parser.add_argument('--ls', action='store_true', help='List the managed containers')
    parser.add_argument('--purge_dead', action='store_true', help='Purge dead containers')
    parser.add_argument('--purge_all', action='store_true', help='Purge all containers')

    parser.add_argument('--spawn_at_port', type=int, default=0, help='The port to use for the new container')
    parser.add_argument('--reset_db', action='store_true', help='Reset the database port table')
    parser.add_argument('--add_port', type=int, default=0, help='Add a port to the database')

    args = parser.parse_args()
    if args.ls:
        containers = get_fhir_container_infos()
        for container in containers:
            print(f"{container['name']} ({container['id']}) - {container['host_port']} - {'running' if container['running'] else 'stopped'}")

    if args.purge_dead:
        purge_dead_fhir_containers()

    if args.purge_all:
        kill_and_remove_all_fhir_containers()

    if args.spawn_at_port > 0:
        success = setup_new_fhir_container(args.spawn_at_port)
        if success:
            print(f"Container spawned at port {args.spawn_at_port}")
        else:
            print(f"Failed to spawn container at port {args.spawn_at_port}")

    if args.reset_db:
        PORT_RANGE = os.environ.get("PORT_RANGE", "8100-9000")
        PORT_RANGE = range(*[int(port) for port in PORT_RANGE.split("-")])
        resetDatabasePortTable(PORT_RANGE)
        print("Resetted database port table for port range:", PORT_RANGE)

    if args.add_port > 0:
        addPortToDatabase(args.add_port)
        print(f"Added port {args.add_port} to the database")