import re

def dump_interface_status_all(output):
    parsed_data = {}
    interface_data = re.findall(r'Interface\s+:\s+(.*?)\n(.*?)(?=\nInterface|$)', output, re.DOTALL)

    for interface_match in interface_data:
        interface_name = interface_match[0].strip()
        interface_id_match = re.search(r'ID\s+:\s+(\d+)', interface_match[1])
        if interface_id_match:
            interface_id = int(interface_id_match.group(1))
            interface_info = re.findall(r'(.*?)\s+:\s+(.*?)\n', interface_match[1])
            interface_params = {param[0].strip(): param[1].strip() for param in interface_info}
            parsed_data[interface_name] = interface_params

    return parsed_data
