import os
import xml.etree.ElementTree as ET
import re
from openpyxl import Workbook
# Import all needed tools. XML etree is an XML parser, and openpyxl is used to parse and export into Excel.

def find_xml_files(directory):
    """Find all XML files in the specified directory and its subdirectories."""
    xml_files = []
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith('.xml'):
                xml_files.append(os.path.join(dirpath, f))
    return xml_files

def extract_cpu_and_ram_usage(file_path):
    """Extracts CPU usage, RAM usage, memory working set, and calculates the mean CPU usage."""
    cpu_data = []
    ram_data_percent = []
    ram_data_mb = []
    memory_working_set_per_process = []
    total_cpu = 0
    total_ram_percent = 0
    count = 0

    # Parse XML file using the imported parser (xml etree)
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    for item in root.findall(".//Item"):
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
                    pass
        
        if component is not None and component.text == "SysHealthMemComponent":
            utilization = item.find(".//Data[@name='util']")
            if utilization is not None and utilization.text:
                try:
                    ram_usage_percent = float(utilization.text)
                    ram_data_percent.append(ram_usage_percent)
                    total_ram_percent += ram_usage_percent
                    
                    # Retrieve the memory in MB
                    detail = item.find(".//Data[@name='detail']")
                    if detail is not None:
                        match = re.search(r'(\d+) MB', detail.text)
                        if match:
                            ram_usage_mb = int(match.group(1))
                            ram_data_mb.append(ram_usage_mb)
                except ValueError:
                    pass

        # Look for "memoryWorkingSet", "pid", and "process" in the XML report
        pid = item.find(".//Data[@name='pid']")
        memory_working_set = item.find(".//Data[@name='memoryWorkingSet']")
        process = item.find(".//Data[@name='process']")
        if pid is not None and memory_working_set is not None and process is not None:
            try:
                pid_value = int(pid.text)
                working_set_kb = int(memory_working_set.text)
                working_set_mb = working_set_kb / 1024  # Convert KB to MB
                process_name = process.text.strip()
                memory_working_set_per_process.append((pid_value, process_name, working_set_mb))
            except ValueError:
                pass

    return cpu_data, ram_data_percent, ram_data_mb, memory_working_set_per_process, total_cpu, total_ram_percent, count

def compare_reports(file_paths):
    """Compares CPU usage data across reports to detect a 40% or greater increase."""
    previous_cpu_data = None
    results = []
    total_cpu_all_reports = 0
    total_ram_percent_all_reports = 0
    report_count = 0
    cpu_usage_list = []
    ram_usage_percent_list = []
    memory_working_set_all_reports = []

    # Create Excel workbook/sheet as requested
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Resource Usage Report"

    # Add headings to Excel sheet
    sheet.append(["Process ID", "Process Name", "Memory Working Set (MB)", "CPU Utilization (%)", "RAM Utilization (%)"])

    total_ram_gb = 16  # Total RAM in GB (16 GB on my machine)
    total_ram_mb = total_ram_gb * 1024  # Convert to MB

    for file_path in file_paths:
        cpu_data, ram_data_percent, ram_data_mb, memory_working_set_per_process, total_cpu, total_ram_percent, count = extract_cpu_and_ram_usage(file_path)
        
        total_cpu_all_reports += total_cpu
        total_ram_percent_all_reports += total_ram_percent
        report_count += count
        
        cpu_usage_list.extend(cpu_data)
        ram_usage_percent_list.extend(ram_data_percent)
        memory_working_set_all_reports.extend(memory_working_set_per_process)        

        print(f"\n--- Processing {file_path} ---")
        print(f"CPU Usage: {cpu_data}")
        print(f"RAM Usage: {ram_data_percent} %")
        print(f"RAM Available: {ram_data_mb} MB")
        print(f"Memory Working Set Per Process (MB): {memory_working_set_per_process}")

        # Write data to the Excel sheet
        for pid, process_name, working_set in memory_working_set_per_process:
            # Calculate RAM utilization percentage based on 16 GB of total RAM on my machine
            ram_utilization_percentage = (working_set / total_ram_mb) * 100  # Convert to percentage
            sheet.append([pid, process_name, f"{working_set:.2f}", ", ".join(map(str, cpu_data)), f"{ram_utilization_percentage:.2f}"])

        if previous_cpu_data:
            for prev, curr in zip(previous_cpu_data, cpu_data):
                if prev > 0 and (curr - prev) / prev * 100 >= 40:
                    result = f"Significant CPU increase detected: {prev}% to {curr}% in {file_path}"
                    results.append(result)

        previous_cpu_data = cpu_data

    # Calculate mean CPU and RAM usage across all reports
    mean_cpu_usage = total_cpu_all_reports / report_count if report_count > 0 else 0
    print(f"\nMean CPU usage across all reports: {mean_cpu_usage}%")
    
    mean_ram_usage_percent = total_ram_percent_all_reports / report_count if report_count > 0 else 0
    print(f"Mean RAM usage across all reports: {mean_ram_usage_percent}%")
    
    # Sort memory working set data in order from highest to lowest (used in the txt file)
    memory_working_set_all_reports.sort(key=lambda x: x[2], reverse=True)

    # Save the Excel file, overwriting the previous
    excel_output_file = "resource_usage_report.xlsx"
    workbook.save(excel_output_file)
    print(f"Excel report generated successfully: {excel_output_file}")

    # Write the results to a text file for CPU usage and Working Set memory
    cpu_output_file = 'cpu_usage_report.txt'
    memory_output_file = 'memory_workingset_report.txt'

    with open(cpu_output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(result + '\n')

    with open(memory_output_file, 'w', encoding='utf-8') as f:
        f.write("Process ID\tProcess Name\tMemory Working Set (MB)\n")
        for pid, process_name, working_set in memory_working_set_all_reports:
            f.write(f"{pid}\t{process_name}\t{working_set:.2f} MB\n")

    if results:
        print(f"Report generated successfully: {cpu_output_file}")
    else:
        print("No significant CPU usage increases detected.")

    print(f"Memory Working Set report generated successfully: {memory_output_file}")

# This specifies the directory where the reports are stored.
directory = r'C:\PerfLogs\Admin\TEST2'
xml_files = find_xml_files(directory)
compare_reports(xml_files)
