import pandas as pd
import re
from datetime import datetime
import argparse
import os

# Mapping short interface names to their full counterparts
interface_mapping = {
    "Te": "TenGigE",
    "Gi": "GigabitEthernet",
    "Be": "Bundle-Ether"
}

def convert_interface_name(short_name):
    """Convert short interface names to full names based on the mapping."""
    for short, full in interface_mapping.items():
        if short_name.startswith(short):
            return short_name.replace(short, full, 1)
    return short_name

def read_interfaces_from_excel(file_path): 
    """Read interfaces from the provided Excel file."""
    try:
        df = pd.read_excel(file_path)
        interfaces = df['Interfaces'].dropna().tolist()
        print(f"Read {len(interfaces)} interfaces from Excel file.")
        return interfaces
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def read_config_file(file_path):
    """Read the network configuration from the text file."""
    try:
        with open(file_path, 'r') as file:
            config_data = file.read()
            print(f"Read configuration data from text file. Length: {len(config_data)} characters.")
            return config_data
    except Exception as e:
        print(f"Error reading config file: {e}")
        return ""

def find_interfaces_and_descriptions(config_data, interfaces_list):
    """Find and record interfaces and their descriptions."""
    results = []
    main_interface_pattern = re.compile(r'interface (\S+)\s+description (.+?)\n', re.DOTALL)
    sub_interface_pattern = re.compile(r'interface (\S+\.\d+)(?:\s+description (.+?)\n|(?:\n\s+[^d]))', re.DOTALL)

    main_matches = main_interface_pattern.findall(config_data)
    sub_matches = sub_interface_pattern.findall(config_data)

    print(f"Found {len(main_matches)} main interface matches: {main_matches}")
    print(f"Found {len(sub_matches)} sub-interface matches: {sub_matches}")

    for interface in interfaces_list:
        full_interface_name = convert_interface_name(interface)
        found_main = False
        found_sub = False
        for match in main_matches:
            if full_interface_name in match[0]:
                results.append((match[0], match[1]))
                found_main = True
                
        for match in sub_matches:
            if full_interface_name in match[0]:
                desc = match[1] if match[1] else 'No description'
                results.append((match[0], desc))
                found_sub = True
        
        if not found_main and not found_sub:
            print(f"No match found for interface: {interface} (converted to {full_interface_name})")
    
    print(f"Recorded {len(results)} interface results.")
    return results

def find_bvi_interfaces(config_data, interfaces_list):
    """Find BVI interfaces in the L2VPN section."""
    bvi_results = []
    bvi_details = []
    l2vpn_sections = re.findall(r'(l2vpn .*?)(?=l2vpn|interface|$)', config_data, re.DOTALL)
    
    print(f"Found {len(l2vpn_sections)} L2VPN sections.")
    print(f"L2VPN Sections: {l2vpn_sections}")

    for section in l2vpn_sections:
        print(f"Processing L2VPN section: {section}")
        bvi_pattern = re.compile(r'routed interface (BVI\d+)')
        bvi_interface = bvi_pattern.findall(section)
        if bvi_interface:
            for bvi in bvi_interface:
                print(f"Found BVI interface: {bvi}")
                for interface in interfaces_list:
                    full_interface_name = convert_interface_name(interface)
                    if full_interface_name in section:
                        bvi_results.append((interface, bvi))
                        bvi_interface_detail = re.search(rf'interface {bvi}(.*?)(?=interface|$)', config_data, re.DOTALL)
                        if bvi_interface_detail:
                            desc_pattern = re.search(r'description (.+?)\n', bvi_interface_detail.group(1), re.DOTALL)
                            desc = desc_pattern.group(1) if desc_pattern else 'No description'
                            bridge_domain_pattern = re.search(r'l2vpn bridge-domain (\S+)', section, re.DOTALL)
                            bridge_domain = bridge_domain_pattern.group(1) if bridge_domain_pattern else 'No bridge domain'
                            bvi_details.append((bvi, desc, bridge_domain))
                            print(f"Found BVI details: Interface={bvi}, Description={desc}, Bridge Domain={bridge_domain}")
        else:
            print(f"No BVI interface found in section: {section}")

    print(f"Recorded {len(bvi_results)} BVI results.")
    print(f"Recorded {len(bvi_details)} BVI details.")
    return bvi_results, bvi_details

def write_to_excel(interface_results, bvi_results, bvi_details, output_file):
    """Write results to an Excel file."""
    try:
        df_interfaces = pd.DataFrame(interface_results, columns=['Interface', 'Description'])
        df_bvi = pd.DataFrame(bvi_results, columns=['Interface', 'BVI Interface'])
        df_bvi_details = pd.DataFrame(bvi_details, columns=['BVI Interface', 'Description', 'Bridge Domain'])
        
        with pd.ExcelWriter(output_file) as writer:
            df_interfaces.to_excel(writer, sheet_name='Interfaces', index=False)
            df_bvi.to_excel(writer, sheet_name='BVI Interfaces', index=False)
            df_bvi_details.to_excel(writer, sheet_name='BVI Details', index=False)
        print(f"Results have been written to {output_file}")
    except Exception as e:
        print(f"Error writing to Excel: {e}")

def main():
    parser = argparse.ArgumentParser(description='Automated Network Interface Configuration Analyzer (ANICA)')
    parser.add_argument('--interfaces_file', required=True, help='Path to the Excel file containing interfaces')
    parser.add_argument('--config_file', required=True, help='Path to the network configuration text file')
    
    args = parser.parse_args()
    
    interfaces_list = read_interfaces_from_excel(args.interfaces_file)
    config_data = read_config_file(args.config_file)
    
    if not interfaces_list or not config_data:
        print("Failed to read input files. Exiting.")
        return
    
    interface_results = find_interfaces_and_descriptions(config_data, interfaces_list)
    bvi_results, bvi_details = find_bvi_interfaces(config_data, interfaces_list)
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'output_interfaces_{os.path.basename(args.config_file).replace(".txt", "")}_{current_time}.xlsx'
    
    write_to_excel(interface_results, bvi_results, bvi_details, output_file)

if __name__ == "__main__":
    main()
