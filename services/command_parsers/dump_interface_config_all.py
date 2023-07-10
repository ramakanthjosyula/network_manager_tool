import re

def dump_interface_config_all(output):
    """
    Parse the output of the 'dump interface config all' command.

    Args:
        output (str): The output of the 'dump interface config all' command.

    Returns:
        list: A list of dictionaries containing information about interfaces.
    """
    try:
        interfaces = {}
        lines = output.strip().split('\n\n')

        for block in lines:
            interface = {}
            lines = block.strip().split('\n')
            for line in lines:
                try:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    interface[key] = value
                except ValueError:
                    # Handle the case where there are not enough values to unpack
                    continue
            interfaces.update({interface.get("Interface","unknown"):interface})
        return interfaces
    except Exception as e:
        raise ValueError("Error occurred while parsing 'dump interface config all' output") from e
