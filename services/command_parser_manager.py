import importlib
import pkgutil
import re

class CommandParserManager:
    @staticmethod
    def parse_output(command, output):
        """
        Parse the output of a command.

        Args:
            command (str): The command that produced the output.
            output (str): The output of the command.

        Returns:
            dict: The parsed data.
        """
        parsed_data = {}

        command_name = command.lower().replace(' ', '_')
        try:
            module = importlib.import_module(f"services.command_parsers.{command_name}")

            parse_func = getattr(module, command_name)

            # Split the output into lines
            lines = output.strip().split('\n')

            # Remove the lines that contain the command string
            lines = [line for line in lines if command.lower() not in line.lower()]

            # Join the remaining lines back into a single string
            modified_output = '\n'.join(lines)

            # Remove special characters from the output
            modified_output = re.sub(r'\x1b\[.*?m', '', modified_output)

            parsed_data = parse_func(modified_output)
        except (ImportError, AttributeError):
            print(f"No parser available for command: {command}")
            parsed_data = {"command_output": output}

        return parsed_data
