import os
from bs4 import BeautifulSoup
#Bs4 and beautifulsoup are used to extract data from HTML files

def find_html_files(directory):
    """Find all HTML files in the specified directory and its subdirectories."""
    html_files = []
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith('.html'):
                html_files.append(os.path.join(dirpath, f))
    return html_files

def extract_cpu_usage(file_path):
    """Extracts CPU usage data from an HTML file."""
    # Try reading with utf-8, and if it fails, try with 'latin-1'
    # The reports were created with utf-8 which was being a bit funky, so i read online and this should work.
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as file:
            soup = BeautifulSoup(file, 'html.parser')
        
    cpu_data = []
    
    for tag in soup.find_all("tag_containing_cpu_data"):
        try:
            cpu_usage = float(tag.get_text().replace('%', ''))
            cpu_data.append(cpu_usage)
        except ValueError:
            continue 

    return cpu_data

def compare_reports(file_paths):
    """Compares CPU usage data across reports to detect a 40% or greater increase."""
    previous_data = None
    results = []

    for file_path in file_paths:
        current_data = extract_cpu_usage(file_path)
        
        if previous_data:
            for prev, curr in zip(previous_data, current_data):
                if prev > 0 and (curr - prev) / prev * 100 >= 40:
                    result = f"Significant increase detected: {prev}% to {curr}% in {file_path}"
                    results.append(result)
        
        previous_data = current_data

    # Write results to a text file in the same directory as the script. If there is no increase, there is no file created. Running it for all files does generate a report.
    output_file = 'cpu_usage_report.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(result + '\n')
    
    # Print a message in the console, to let you know that a file was created.
    if results:
        print(f"Report generated successfully: {output_file}")
    else:
        print("No significant CPU usage increases detected.")

# Specify the directory where the HTML reports are stored.
directory = r'C:\PerfLogs\Admin\TEST2'
html_files = find_html_files(directory)
compare_reports(html_files)
