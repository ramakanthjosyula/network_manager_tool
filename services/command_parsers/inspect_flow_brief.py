import re

def inspect_flow_brief(output):
    """
    Parse the output of the 'inspect flow brief' command.

    Args:
        output (str): The output of the 'inspect flow brief' command.

    Returns:
        dict: Parsed data containing information about flows.
    """
    flows = {}
    output = re.sub(r'\x1b\[.*?m', '', output)  # Remove escape sequences from the input

    try:
        lines = output.strip().split('\n')

        # Find the last line that contains the command and stop there
        command_lines = [line for line in lines if 'inspect flow brief' in line]
        if command_lines:
            header_line_index = lines.index(command_lines[-1]) + 1
        else:
            header_line_index = 0
        # Find the header line
        header_line = lines[header_line_index]
        headers = re.split(r"\s{2,}", header_line.strip())
        data_lines = lines[header_line_index + 1:]
        for line in data_lines:
            if not line.strip():
                continue

            flow = {}
            start_indices = [match.start() for match in re.finditer(r"\b[\w-]+\b", header_line)]
            end_indices = []
            for i in range(len(start_indices) - 1):
                end_indices.append(start_indices[i + 1] - 1)   
            end_indices.append(len(line) - 1)
            for start, end, header in zip(start_indices, end_indices, headers):
                value = line[start:end].strip()
                flow[header] = value
            flow_key = f"sip:{flow['SRC']}-dip:{flow['DST']}-sport:{flow['SPORT']}-dport:{flow['DPORT']}-prot:{flow['PROTOCOL']}"
            flows[flow_key] = flow
    except Exception as e:
        print(f"Error occurred while parsing 'inspect flow brief' output: {str(e)}")

    return flows
