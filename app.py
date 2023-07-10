import importlib
from fastapi import FastAPI, File, UploadFile, Response, Body
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from services.network_manager import NetworkManager
from services.command_parser_manager import CommandParserManager
from pymongo import MongoClient
from pathlib import Path
import pprint
from ruamel.yaml import YAML
from starlette.responses import FileResponse
from typing import List
import os

import json

# Create an instance of the FastAPI app
app = FastAPI()

# MongoDB connection settings
MONGO_HOST = "localhost"
MONGO_PORT = 27017

try:
    client = MongoClient(MONGO_HOST, MONGO_PORT)
    db = client["network-manager"]
    db.command("ping")  # Test the connection
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Failed to connect to MongoDB: {str(e)}")

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create an instance of the NetworkManager class
network_manager = NetworkManager({})

# Define the commands to execute on each element
def write_commands_to_file(commands):
    commands_file = "static/commands.txt"
    with open(commands_file, "w") as f:
        f.write("\n".join(commands))

def get_commands_list():
    commands_file = "static/commands.txt"
    if os.path.isfile(commands_file):
        with open(commands_file, "r") as f:
            commands = f.read().splitlines()
    else:
        parsers_dir = "services/command_parsers"
        files = os.listdir(parsers_dir)
        commands = [filename.replace("_", " ").split(".")[0] for filename in files if filename.endswith(".py")]
        write_commands_to_file(commands)
    return commands

# Retrieve the initial commands list
commands = get_commands_list()

def execute_commands_on_network(network_manager):
    """
    Execute commands on each network element and parse the output.

    Args:
        network_manager (NetworkManager): Instance of NetworkManager.

    Returns:
        bool: True if commands executed successfully, False otherwise.
    """
    execution_status = {}
    parsed_data = {}
    # load the elements from yaml
    file = "data/network_elements.yaml"
    file_path = Path(__file__).resolve().parent / file
    network_manager.load_elements(file_path)
    # Connect to network elements
    connection_status = network_manager.connect_elements()
    commands = get_commands_list()
    try:
        for hostname,status in network_manager.connections.items():
            if status:
                print(f"\nExecuting commands on {hostname}:")
                command_results = network_manager.execute_commands(hostname, commands)
                for command, result in zip(commands, command_results):
                    parsed_data.setdefault(hostname, {})[command] = CommandParserManager.parse_output(command, result)
            else:
                print(f"\nSkipping commands on {hostname}. Failed to connect.")
            
            # parsed_data[hostname] = parsed_data
        # Store parsed data in MongoDB
        network_manager.previous_snapshot = network_manager.current_snapshot
        network_manager.current_snapshot = parsed_data
        pprint.pprint(parsed_data)        
        network_manager.disconnect_elements()
        execution_status["status"] = True
    except Exception as e:
        execution_status["status"] = False
        execution_status["error"] = str(e)
    return execution_status

# Generate custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Your API Documentation",
        version="1.0.0",
        description="API documentation for Your Application",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Define the root endpoint
@app.get("/")
async def root():
    """Root endpoint to welcome users."""
    return {"message": "Welcome to Your Application"}


# Route to serve custom Swagger UI HTML
@app.get("/docs", include_in_schema=False)
async def swagger_ui_html():
    """Endpoint to serve custom Swagger UI HTML."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Your API Documentation",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


# Route to serve OpenAPI schema
@app.get("/openapi.json", include_in_schema=False)
async def openapi_endpoint():
    """Endpoint to serve OpenAPI schema."""
    return custom_openapi()


# Route to upload YAML file
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to upload a YAML file.
    """
    file_path = Path(__file__).resolve().parent / "data/network_elements.yaml"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"message": "File uploaded successfully"}


# Service endpoint to execute commands (renamed to take-snapshot)
@app.post("/take-snapshot")
async def take_snapshot():
    """Endpoint to execute commands on network elements."""
    try:
        execute_commands_on_network(network_manager)
        return {"message": "Snapshot taken successfully"}
    except Exception as e:
        return {"message": "Failed to take snapshot", "error": str(e)}


# Service endpoint to retrieve parsed data (renamed to get-current-snapshot)
@app.get("/get-current-snapshot")
async def get_current_snapshot():
    """Endpoint to retrieve parsed data from MongoDB."""
    try:
        response_data = jsonable_encoder(network_manager.current_snapshot)
        if response_data:
            return JSONResponse(content=response_data, media_type="application/json")
        else:
            return {"message": "Parsed data not found"}
    except Exception as e:
        return {"message": "Failed to retrieve parsed data", "error": str(e)}

@app.get("/get-previous-snapshot")
async def get_previous_snapshot():
    """Endpoint to retrieve the previous snapshot."""
    try:
        response_data = jsonable_encoder(network_manager.previous_snapshot)
        if response_data:
            return JSONResponse(content=response_data, media_type="application/json")
        else:
            return {"message": "Previous snapshot not found"}
    except Exception as e:
        return {"message": "Failed to retrieve the previous snapshot", "error": str(e)}


@app.post("/save-reference-snapshot")
async def save_reference_snapshot():
    """Endpoint to save the current snapshot as a reference snapshot."""
    try:
        network_manager.reference_snapshot = network_manager.current_snapshot
        file_path = Path(__file__).resolve().parent / "static/reference_snapshot.json"
        with open(file_path, "w") as f:
            json.dump(network_manager.reference_snapshot, f, indent=4)
        return {"message": "Reference snapshot saved successfully"}
    except Exception as e:
        return {"message": "Failed to save reference snapshot", "error": str(e)}


@app.get("/compare-snapshots")
async def compare_with_snapshots(use_reference: bool = False):
    """
    Endpoint to compare snapshots and provide link to HTML file.
    By default, compares with the previous snapshot. If use_reference=True, compares with the reference snapshot.
    """

    network_manager.compare_snapshots(use_reference = use_reference)
    file_path = Path(__file__).resolve().parent / "static/diff.html"
    return FileResponse(file_path, media_type="text/html")

# Service endpoint to convert JSON input to YAML and save it
@app.post("/convert-json-to-yaml")
async def convert_json_to_yaml(data: dict = Body(...)):
    """Endpoint to convert JSON input to YAML and save it."""
    try:
        file_path = Path(__file__).resolve().parent / "data/network_elements.yaml"
        yaml = YAML()
        yaml.dump(data, file_path)
        return {"message": "JSON converted to YAML and saved successfully"}
    except Exception as e:
        return {"message": "Failed to convert JSON to YAML", "error": str(e)}

import sys
import importlib.util
from services.command_parser_manager import CommandParserManager

@app.post("/update-parser")
async def update_parser(command_name: str, parser_file: UploadFile = File(...)):
    """
    Endpoint to update the parser file.
    """
    # Format the command name to replace spaces with underscores
    command_func_name = command_name.replace(" ", "_")

    # Save the parser file with the formatted command name
    parser_file_path = Path(__file__).resolve().parent / "services" / "command_parsers" / f"{command_func_name}.py"

    # Save the new parser file
    with open(parser_file_path, "wb") as f:
        f.write(await parser_file.read())

    # Restart the server
    os.execv(sys.executable, [sys.executable] + sys.argv)

@app.get("/commands")
def get_commands():
    commands = get_commands_list()
    return {"commands": commands}

@app.post("/update-commands")
async def update_commands(new_commands: List[str]):
    """
    Endpoint to update the commands list.
    """
    write_commands_to_file(new_commands)  # Update the commands.txt file
    return {"message": "Commands list updated successfully"}

@app.post("/reset-commands")
async def reset_commands():
    """
    Endpoint to reset the commands list to the original list derived from parser files.
    """
    parsers_dir = "services/command_parsers"
    files = os.listdir(parsers_dir)
    commands = [filename.replace("_", " ").split(".")[0] for filename in files if filename.endswith(".py")]
    write_commands_to_file(commands)
    return {"message": "Commands list reset successfully"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
