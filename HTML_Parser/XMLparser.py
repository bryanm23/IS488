# While looking through the files, and doing some research, I found that XML files are generally easier to parse.
# The HTML files were thousands of lines of unreadable code, and XML was much more clearly labeled. VSCode also made it very easy to parse XML documents.
import os
import xml.etree.ElementTree as ET
import re

#Built in XML parser to use with Python.

def find_xml_files(directory):
    """Find all XML files in the specified directory and its subdirectories."""
    xml_files = []
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith('.xml'):
                xml_files.append(os.path.join(dirpath, f))
    return xml_files

def extract_cpu_usage(file_path):
    """Extracts CPU usage data from an XML file."""
    cpu_data = []

    # Parse the XML file using the built in tool
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    print(f"\n--- Processing {file_path} ---")
    
    # Iterate over all items and look for the SysHealthCpuComponent (what the XML file labels the data as)
    for item in root.findall(".//Item"):
        component = item.find(".//Data[@name='component']")
        if component is not None and component.text == "SysHealthCpuComponent":
            # Find the data
            utilization = item.find(".//Data[@name='util']")
            if utilization is not None and utilization.text:
                try:
                    cpu_usage = float(utilization.text)
                    cpu_data.append(cpu_usage)
                    print(f"Found CPU usage: {cpu_usage}%")
                except ValueError:
                    print(f"No valid CPU percentage found in: {utilization.text}")
    
    return cpu_data

def compare_reports(file_paths):
    """Compares CPU usage data across reports to detect a 40% or greater increase."""
    previous_cpu_data = None
    results = []

    for file_path in file_paths:
        cpu_data = extract_cpu_usage(file_path)
        
        # Output current CPU usage to the terminal.
        print(f"File: {file_path}")
        print(f"CPU Usage: {cpu_data}")
        
        if previous_cpu_data:
            for prev, curr in zip(previous_cpu_data, cpu_data):
                if prev > 0 and (curr - prev) / prev * 100 >= 40:
                    result = f"Significant CPU increase detected: {prev}% to {curr}% in {file_path}"
                    results.append(result)
                    #Lets you know if a CPU increase is detected.
        
        previous_cpu_data = cpu_data

    # Write results to a text file if any increases are found
    output_file = 'cpu_usage_report.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(result + '\n')
    
    if results:
        print(f"Report generated successfully: {output_file}")
    else:
        print("No significant CPU usage increases detected.")

# Specify the directory where the XML reports are stored.
directory = r'C:\PerfLogs\Admin\TEST2'
xml_files = find_xml_files(directory)
compare_reports(xml_files)



