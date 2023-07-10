from network_manager import NetworkManager
from command_parser import CommandParser
from pprint import pprint
from pymongo import MongoClient

# Create an instance of the NetworkManager class
network_manager = NetworkManager({})

# Load network elements from YAML file
network_manager.load_elements('../data/network_elements.yaml')

# Connect to network elements
connection_status = network_manager.connect_elements()

# Define the commands to execute on each element
# commands = ["show version", "show interfaces"]
commands = ["dump overview", "inspect fib all", "dump vpn summary"]

# MongoDB connection settings
mongo_host = 'localhost'
mongo_port = 27017
mongo_db_name = 'network_data'
mongo_collection_name = 'parsed_data'

# Connect to MongoDB
mongo_client = MongoClient(mongo_host, mongo_port)
db = mongo_client[mongo_db_name]
collection = db[mongo_collection_name]

# Execute commands on each element and parse the output
for hostname in network_manager.connections:
    if connection_status.get(hostname):
        print(f"\nExecuting commands on {hostname}:")
        command_results = network_manager.execute_commands(hostname, commands)
        for command, result in zip(commands, command_results):
            parsed_data = CommandParser.parse_output(command, result)
            print(f"\nOutput for command '{command}':")
            pprint(parsed_data)

            # Save parsed data to MongoDB
            collection.insert_one(parsed_data)
    else:
        print(f"\nSkipping commands on {hostname}. Failed to connect.")

# Disconnect from network elements
network_manager.disconnect_elements()

# Close MongoDB connection
mongo_client.close()
