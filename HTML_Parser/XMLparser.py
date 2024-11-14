import os
import xml.etree.ElementTree as ET
import re

def find_xml_files(directory):
    """Find all XML files in the specified directory and its subdirectories."""
    xml_files = []
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith('.xml'):
                xml_files.append(os.path.join(dirpath, f))
    return xml_files

def extract_cpu_and_ram_usage(file_path):
    """Extracts CPU usage, RAM usage, and calculates the mean CPU usage from an XML file."""
    cpu_data = []
    ram_data_percent = []
    ram_data_mb = []
    total_cpu = 0
    total_ram_percent = 0
    count = 0

    # Parse XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Iterate over all items and look for the SysHealthCpuComponent and SysHealthMemComponent
    for item in root.findall(".//Item"):
        # CPU component
        component = item.find(".//Data[@name='component']")
        if component is not None and component.text == "SysHealthCpuComponent":
            utilization = item.find(".//Data[@name='util']")
            if utilization is not None and utilization.text:
                try:
                    cpu_usage = float(utilization.text)
                    cpu_data.append(cpu_usage)
                    total_cpu += cpu_usage
                    count += 1
                except ValueError:
                    pass  # Ignore invalid values
        
        # RAM component
        component = item.find(".//Data[@name='component']")
        if component is not None and component.text == "SysHealthMemComponent":
            utilization = item.find(".//Data[@name='util']")
            if utilization is not None and utilization.text:
                try:
                    ram_usage_percent = float(utilization.text)
                    ram_data_percent.append(ram_usage_percent)
                    total_ram_percent += ram_usage_percent
                    
                    # Also retrieve the available memory in MB
                    detail = item.find(".//Data[@name='detail']")
                    if detail is not None:
                        match = re.search(r'(\d+) MB', detail.text)
                        if match:
                            ram_usage_mb = int(match.group(1))
                            ram_data_mb.append(ram_usage_mb)
                except ValueError:
                    pass  # Ignore invalid values
    
    return cpu_data, ram_data_percent, ram_data_mb, total_cpu, total_ram_percent, count

def calculate_variance(data, mean):
    """Calculates the variance of the given data based on the mean."""
    if len(data) > 1:
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance
    else:
        return 0  # Variance is zero if there is only one data point

def compare_reports(file_paths):
    """Compares CPU usage data across reports to detect a 40% or greater increase."""
    previous_cpu_data = None
    results = []
    total_cpu_all_reports = 0
    total_ram_percent_all_reports = 0
    report_count = 0
    cpu_usage_list = []
    ram_usage_percent_list = []
    
    for file_path in file_paths:
        cpu_data, ram_data_percent, ram_data_mb, total_cpu, total_ram_percent, count = extract_cpu_and_ram_usage(file_path)
        
        # Aggregate total usage across all reports for final calculation
        total_cpu_all_reports += total_cpu
        total_ram_percent_all_reports += total_ram_percent
        report_count += count
        
        # Add data to the lists for variance calculation
        cpu_usage_list.extend(cpu_data)
        ram_usage_percent_list.extend(ram_data_percent)
        
        # Print once per file
        print(f"\n--- Processing {file_path} ---")
        print(f"CPU Usage: {cpu_data}")
        print(f"RAM Usage: {ram_data_percent} %")
        print(f"RAM Available: {ram_data_mb} MB")
        
        if previous_cpu_data:
            for prev, curr in zip(previous_cpu_data, cpu_data):
                if prev > 0 and (curr - prev) / prev * 100 >= 40:
                    result = f"Significant CPU increase detected: {prev}% to {curr}% in {file_path}"
                    results.append(result)

        previous_cpu_data = cpu_data

    # Calculate mean CPU usage across all reports
    mean_cpu_usage = total_cpu_all_reports / report_count if report_count > 0 else 0
    print(f"\nMean CPU usage across all reports: {mean_cpu_usage}%")
    
    # Calculate mean RAM usage across all reports
    mean_ram_usage_percent = total_ram_percent_all_reports / report_count if report_count > 0 else 0
    print(f"Mean RAM usage across all reports: {mean_ram_usage_percent}%")
    
    # Calculate the variance of CPU and RAM usage
    cpu_variance = calculate_variance(cpu_usage_list, mean_cpu_usage)
    ram_variance_percent = calculate_variance(ram_usage_percent_list, mean_ram_usage_percent)
    
    print(f"\nVariance of CPU usage across all reports: {cpu_variance}")
    print(f"Variance of RAM usage across all reports: {ram_variance_percent}")
    
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
