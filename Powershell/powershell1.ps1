#This code is a powershell script for IS488. The documentation is step-by-step, so it is easy to understand what the script does.
#As of now, it is very bare bones, I just wanted to get a working prototype.
#You can currently input known Process IDs, and the script will check if any are currently running. 


# Set the output file path on the desktop
$desktopPath = [System.Environment]::GetFolderPath("Desktop")
$outputFilePath = Join-Path -Path $desktopPath -ChildPath "ProcessID_Events_Log.txt"

# Define the process IDs you want to log. You can input known process ids, such as an entire list.
$processIdsToMonitor = @(1234, 5678) 

# Start capturing events using Get-WinEvent SysInternal.
$filter = @{
    LogName = 'Security', 'System', 'Application'
    Id = 4688  # Process creation event ID; adjust based on what you are looking for.
}

# Initialize an array to store the log entries
$logEntries = @()

# Loop through each process ID and capture events
foreach ($processId in $processIdsToMonitor) {
    $events = Get-WinEvent -FilterHashtable $filter | Where-Object {
        $_.Properties[0].Value -eq $processId
    }

    # Collect log entries
    foreach ($event in $events) {
        $logEntries += [PSCustomObject]@{
            TimeCreated = $event.TimeCreated
            Id = $event.Id
            Message = $event.Message
            ProcessId = $processId
        }
    }
}

# Check if there are any log entries to write
if ($logEntries.Count -gt 0) {
    # Prepare log entries for output
    $logOutput = $logEntries | ForEach-Object {
        "$($_.TimeCreated),$($_.Id),$($_.Message),$($_.ProcessId)"
    }

    # Write log entries to a .txt file (this is currently not outputting the IDs to a .txt, because there are no inputted process IDs that are running on my machine.
    Set-Content -Path $outputFilePath -Value $logOutput
    Write-Host "Log entries have been exported to $outputFilePath."
} else {
    Write-Host "No events found for the specified process IDs."
}