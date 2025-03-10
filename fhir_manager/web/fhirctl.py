import os, sqlite3
from flask import request
from flask import render_template
from flask import Flask
from flask import g

from fhir_manager.dockerctl import (
    get_fhir_container_infos,
    purge_dead_fhir_containers,
    setup_new_fhir_container,
    reset_fhir_container,
    delete_fhir_container,
    is_port_in_use,
    addPortToDatabase,
    getAvailablePortFromDatabase
)

PORT_RANGE = os.environ.get("PORT_RANGE", "8100-9000")
PORT_RANGE = range(*[int(port) for port in PORT_RANGE.split("-")])

dpath = os.path.dirname(__file__)
root_dir = os.path.dirname(os.path.dirname(dpath))
data_dir = os.path.join(root_dir, "data")

app = Flask(
    __name__,
    static_folder=os.path.join(dpath, 'static'),
    template_folder=os.path.join(dpath, 'templates')
)

# SQLite db
DB_PATH = os.path.join(data_dir, "available_ports.db")
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET'])
def view_container_all():
    containers = get_fhir_container_infos()
    return render_template('view_container_all.html', containers=containers)

@app.route('/<int:port>/', methods=['GET'])
def view_container_port(port: int):
    container = [ container for container in get_fhir_container_infos() if container.get("host_port") == port ]
    if not container:
        container = None
    else:
        container = container[0]

    return render_template('view_container_port.html', container=container, port=port)

@app.route('/api/<int:port>', methods=['GET'])
def get_container_info(port: int):
    container = [ container for container in get_fhir_container_infos() if container.get("host_port") == port ]
    if not container:
        container = None
    else:
        container = container[0]

    return {
        "success": True,
        "port": port,
        "container": container,
    }

@app.route('/api/<int:port>/reset', methods=['POST'])
def reset_container(port: int):
    reset_fhir_container(port)
    return {
        "success": True,
        "port": port,
        "message": f"Container reset on port {port}",
    }

@app.route('/api/<int:port>/delete', methods=['POST'])
def delete_container(port: int):
    delete_fhir_container(port, db_conn=get_db())
    return {
        "success": True,
        "port": port,
        "message": f"Container deleted on port {port}",
    }

@app.route('/api/create', methods=['POST'])
def create_container():
    # Get the port from the request (if available)
    try:
        port = int(request.json.get("port"))
        if not port in PORT_RANGE:
            port = None
    except:
        port = None

    # Try to get the port
    port = getAvailablePortFromDatabase(desired_port=port, db_conn=get_db())

    # If no port is available, return an error
    if port is None or is_port_in_use(port):
        return {
            "success": False,
            "message": "No available port",
        }, 500


    print(f"Port {port} is available")
    setup_new_fhir_container(port)

    return {
        "success": True,
        "port": port,
        "message": f"Container created on port {port}",
    }
