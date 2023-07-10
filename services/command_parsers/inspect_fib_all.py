import re
def inspect_fib_all(output):
    """
    Parse the output of the 'inspect fib all' command.

    Args:
        output (str): The output of the 'inspect fib all' command.

    Returns:
        dict: Parsed data containing information about paths, prefixes, and VPNs.
    """
    parsed_data = {}
    try:
        lines = re.split(r'[\n,]', output)
        current_path = None

        for line in lines:
            line = line.strip()
            if line.startswith("Path ID:"):
                # Start of a new path
                if current_path is not None:
                    parsed_data[current_path['Path ID']] = current_path
                current_path = {}
                path_id = line.split(': ')[1].strip()
                current_path['Path ID'] = path_id
            elif line.startswith("Path Type:"):
                path_type = line.split(': ')[1].strip()
                current_path['Path Type'] = path_type
            elif line.startswith("Vpn Type:"):
                vpn_type = line.split(': ')[1].strip()
                current_path['Vpn Type'] = vpn_type
            elif line.startswith("Site ID:"):
                site_id = line.split(': ')[1].strip()
                current_path['Site ID'] = site_id
            elif line.startswith("Site Name:"):
                site_name = line.split(': ')[1].strip()
                current_path['Site Name'] = site_name
            elif line.startswith("Status:"):
                status = line.split(': ')[1].strip()
                current_path['Status'] = status.lower() == 'true'
            elif line.startswith("Path Info:"):
                path_info = line.split(': ')[1].strip()
                current_path['Path Info'] = path_info
            elif line.startswith("Prefixes:") or line.startswith("V6 Prefixes:"):
                # Skip the header for prefixes and v6 prefixes
                continue
            elif line.startswith("Prefix:"):
                if 'Prefixes' not in current_path:
                    current_path['Prefixes'] = []
                prefix = line.split(': ')[1].strip()
                current_path['Prefixes'].append(prefix)
            elif line.startswith("V6 Prefix:"):
                if 'V6 Prefixes' not in current_path:
                    current_path['V6 Prefixes'] = []
                v6_prefix = line.split(': ')[1].strip()
                current_path['V6 Prefixes'].append(v6_prefix)

        # Add the last path to the parsed data
        if current_path is not None:
            parsed_data[current_path['Path ID']] = current_path
    except Exception as e:
        print(f"Error occurred while parsing 'inspect fib all' output: {str(e)}")

    return parsed_data
