import re
def dump_vpn_summary(output):
    """
    Parse the output of the 'dump vpn summary' command.

    Args:
        output (str): The output of the 'dump vpn summary' command.

    Returns:
        dict: Parsed data containing information about VPNs.
    """
    parsed_data = {}
    try:
        lines = output.strip().split("\n")
        header_line = lines[0]
        headers = re.split(r"\s{1,}", header_line.strip())
        data = {}

        for line in lines[1:]:
            values = re.split(r"\s{1,}", line.strip())
            if len(values) == len(headers):
                entry = {}
                for i in range(len(headers)):
                    header = headers[i].strip()
                    if header != "":
                        entry[header] = values[i].strip()
                data[entry.get('VepID')] = entry

        parsed_data = data
    except Exception as e:
        print(f"Error occurred while parsing 'dump vpn summary' output: {str(e)}")

    return parsed_data
