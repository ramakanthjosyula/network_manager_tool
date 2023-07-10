from netmiko import ConnectHandler
import yaml
from deepdiff import DeepDiff
from pathlib import Path
import json
import html
import json

import json
from deepdiff.model import PrettyOrderedSet

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, PrettyOrderedSet):
            return list(o)
        return super().default(o)
    
class NetworkManager:
    def __init__(self, elements):
        """
        Initialize the NetworkManager with network elements.

        Args:
            elements (dict): Dictionary containing network element details.
        """
        self.elements = elements
        self.connections = {}
        self.parsed_data = {}
        self.previous_snapshot = {}
        self.current_snapshot = {}
        self.reference_snapshot = {}
        self.diff_html_path = None

    def connect_ssh(self, element):
        """
        Connect to a network element using SSH.

        Args:
            element (dict): Dictionary containing network element details.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            print(f"Connecting to {element['host']}...")
            connection = ConnectHandler(
                device_type=element['device_type'],
                ip=element['host'],
                username=element['username'],
                password=element['password'],
            )
            self.connections[element.get('name',element['host'])] = connection
            print(f"Connected to {element.get('name'),element['host']}")
            return True
        except Exception as e:
            print(f"Failed to connect to {element['host']}: {str(e)}")
            return False

    def load_elements(self, filename):
        """
        Load network elements from a YAML file.

        Args:
            filename (str): Path to the YAML file.

        Returns:
            bool: True if loading is successful, False otherwise.
        """
        try:
            print(f"Loading network elements from {filename}...")
            with open(filename, 'r') as file:
                elements = yaml.safe_load(file)
                self.elements = elements
            print("Network elements loaded successfully")
            return True
        except Exception as e:
            print(f"Failed to load elements from {filename}: {str(e)}")
            return False

    def connect_elements(self):
        """
        Connect to all network elements.

        Returns:
            dict: Dictionary containing connection status for each element.
        """
        connection_status = {}
        print("Connecting to network elements...")
        for ele in self.elements:
            element = self.elements.get(ele)
            host = element['host']
            login_type = element['login_type']

            if login_type == 'ssh':
                success = self.connect_ssh(element)
                connection_status[host] = success
            elif login_type == 'rest':
                # Implement REST connection logic
                pass
            else:
                print(f"Invalid login type '{login_type}' for {host}")
                connection_status[host] = False

        print("Connection process completed")
        return connection_status

    def execute_commands(self, hostname, commands):
        """
        Execute commands on a network element.

        Args:
            hostname (str): Hostname or IP address of the network element.
            commands (list): List of commands to execute.

        Returns:
            list: List of command outputs.
        """
        connection = self.connections.get(hostname)
        if connection is None:
            raise ValueError(f"No connection found for hostname '{hostname}'")

        print(f"Executing commands on {hostname}...")
        results = []
        for command in commands:
            try:
                output = connection.send_command(command)
                print(f"Command: {command}")
                print(f"Output: {output}")
                results.append(output)
            except Exception as e:
                results.append(f"An error occurred: {str(e)}")

        print(f"Command execution on {hostname} completed")
        return results

    def disconnect_elements(self):
        """
        Disconnect from all network elements.
        """
        print("Disconnecting from network elements...")
        for hostname, connection in self.connections.items():
            try:
                connection.disconnect()
                print(f"Disconnected from {hostname}")
            except Exception as e:
                print(f"Failed to disconnect from {hostname}: {str(e)}")

        self.connections = {}

        print("Disconnection process completed")

    def compare_snapshots(self, use_reference=False):
        
        # Compare the current and previous snapshots
        if use_reference:
            try : 
                reference_snapshot_file = Path(__file__).resolve().parent / "../static/reference_snapshot.json"
                with open(reference_snapshot_file, "r") as f:
                    reference_snapshot = json.load(f)
            except : 
                print("no Reference snap shot found")
            diff = DeepDiff(reference_snapshot,self.current_snapshot)
        else:
            diff = DeepDiff(self.previous_snapshot, self.current_snapshot)

        # Generate the HTML file content
        html_content = """
        <html>
        <head>
            <link rel="stylesheet" href="/static/bootstrap.min.css">
            <script src="/static/bootstrap.bundle.min.js"></script>
            <style>
                .change-type {
                    font-size: 1.2rem;
                    font-weight: bold;
                    margin-top: 2rem;
                }
                .change-key {
                    font-size: 1.1rem;
                    font-weight: bold;
                    margin-top: 1rem;
                }
                .change-value {
                    font-size: 1rem;
                    margin-top: 0.5rem;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Differences between Current and Previous Snapshots</h1>
        """

        # Add the differences to the HTML content
        for change_type, changes in diff.items():
            html_content += f'<div class="change-type">{change_type}</div>'
            if isinstance(changes, dict):
                for key, value in changes.items():
                    html_content += f'<div class="change-key">{key}</div>'
                    html_content += f'<pre class="change-value">{html.escape(json.dumps(value, indent=4, cls=CustomJSONEncoder))}</pre>'
            elif isinstance(changes, list):
                html_content += '<pre class="change-value">'
                for value in changes:
                    html_content += f'{html.escape(json.dumps(value, indent=4, cls=CustomJSONEncoder))}\n'
                html_content += '</pre>'

        html_content += """
            </div>
        </body>
        </html>
        """

        # Save the HTML content to a file
        file_path = Path(__file__).resolve().parent / "../static/diff.html"
        with open(file_path, "w") as f:
            f.write(html_content)

        # Generate a link to the HTML diff file
        diff_file_link = f"/static/diff.html"
        self.diff_html_path = diff_file_link
        return str(diff_file_link)
