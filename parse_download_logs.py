#!/usr/bin/env python3
"""
Parse download logs and extract table data to CSV.
Extracts the second/last table from each download log file.
"""

import os
import re
import csv
from pathlib import Path
from datetime import datetime

def parse_timestamp_from_filename(filename):
    """Extract timestamp from filename like: 20250701_013729_autorino_MGL000GLP_download.log"""
    match = re.match(r'(\d{8})_(\d{6})_', filename)
    if match:
        date_part = match.group(1)
        time_part = match.group(2)
        # Format: YYYYMMDD_HHMMSS
        timestamp_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
        return timestamp_str
    return None

def parse_timestamp_from_log_line(line):
    """Extract timestamp from first log line like: 250701T01:37:29.927|I|download"""
    match = re.match(r'(\d{6})T(\d{2}):(\d{2}):(\d{2})\.\d+', line)
    if match:
        date_part = match.group(1)
        hour = match.group(2)
        minute = match.group(3)
        second = match.group(4)
        # Format: YYMMDD -> 20YY-MM-DD
        timestamp_str = f"20{date_part[:2]}-{date_part[2:4]}-{date_part[4:6]} {hour}:{minute}:{second}"
        return timestamp_str
    return None

def calculate_execution_time(first_timestamp, last_timestamp):
    """Calculate execution time in seconds between two timestamps"""
    try:
        # Parse timestamps like: 250701T01:37:29.927
        def parse_ts(ts):
            match = re.match(r'(\d{6})T(\d{2}):(\d{2}):(\d{2})\.(\d+)', ts)
            if match:
                date_part = match.group(1)
                hour = match.group(2)
                minute = match.group(3)
                second = match.group(4)
                millisec = match.group(5)
                # Format: YYMMDD
                dt_str = f"20{date_part[:2]}-{date_part[2:4]}-{date_part[4:6]} {hour}:{minute}:{second}.{millisec}"
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
            return None

        dt1 = parse_ts(first_timestamp)
        dt2 = parse_ts(last_timestamp)

        if dt1 and dt2:
            delta = dt2 - dt1
            return delta.total_seconds()
    except:
        pass
    return None

def parse_download_log(log_file_path):
    """Parse a download log file and extract the last table data"""

    results = []

    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    if not lines:
        return results

    # Get filename for timestamp extraction
    filename = os.path.basename(log_file_path)
    execution_timestamp = parse_timestamp_from_filename(filename)

    # Alternative: get timestamp from first line
    if not execution_timestamp and lines:
        execution_timestamp = parse_timestamp_from_log_line(lines[0])

    # Get first and last timestamps for execution time
    first_ts = None
    last_ts = None
    for line in lines:
        ts_match = re.match(r'(\d{6}T\d{2}:\d{2}:\d{2}\.\d+)', line)
        if ts_match:
            if not first_ts:
                first_ts = ts_match.group(1)
            last_ts = ts_match.group(1)

    execution_time = calculate_execution_time(first_ts, last_ts) if first_ts and last_ts else None

    # Find all tables (marked by "print_table" lines)
    table_starts = []
    for i, line in enumerate(lines):
        if 'print_table' in line and 'DownloadGnss' in line:
            table_starts.append(i)

    if not table_starts:
        return results

    # We want the last table (second table if there are 2)
    last_table_start = table_starts[-1]

    # Parse the table
    # The table starts after the "print_table" line
    # Format:
    # Line with header columns
    # Lines with data rows starting with index number

    table_lines = []
    for i in range(last_table_start + 1, len(lines)):
        line = lines[i]
        # Stop if we hit another log line (starts with timestamp)
        if re.match(r'\d{6}T\d{2}:\d{2}:\d{2}', line):
            break
        table_lines.append(line)

    if not table_lines:
        return results

    # Find the header line (contains column names)
    header_line_idx = None
    for i, line in enumerate(table_lines):
        if 'fname' in line and 'site' in line and 'epoch_srt' in line:
            header_line_idx = i
            break

    if header_line_idx is None:
        return results

    # Parse header to get column positions
    header_line = table_lines[header_line_idx]

    # Parse data rows (they start with a number)
    for i in range(header_line_idx + 1, len(table_lines)):
        line = table_lines[i]
        # Data rows start with a number followed by whitespace
        if re.match(r'^\s*\d+\s+', line):
            # Split by multiple spaces to get columns
            parts = re.split(r'\s{2,}', line.strip())

            if len(parts) >= 6:
                # Extract required columns
                # The columns are: index, fname, site, epoch_srt, epoch_end, ok_inp, ok_out, fpath_inp, fpath_out, size_inp, size_out, note
                # We need: site (index 2), epoch_srt (3), epoch_end (4), ok_inp (5), ok_out (6)
                # But epoch_srt and epoch_end each have date and time separated by space
                # So we need to handle this differently

                # Try to parse the line more carefully
                # Example: "0  MGL0______202506210000A.T02  MGL000GLP 25-06-21 00:00:00 25-06-21 23:59:59   False    True  ..."
                # After splitting by 2+ spaces: ['0', 'MGL0______202506210000A.T02', 'MGL000GLP 25-06-21 00:00:00 25-06-21 23:59:59', 'False', 'True', ...]

                # The site column contains: site epoch_srt epoch_end
                if len(parts) >= 5:
                    site_and_epochs = parts[2]  # "MGL000GLP 25-06-21 00:00:00 25-06-21 23:59:59"
                    site_parts = site_and_epochs.split()

                    if len(site_parts) >= 5:
                        site = site_parts[0]
                        # Convert YY-MM-DD to YYYY-MM-DD
                        date_srt = site_parts[1]  # e.g., "25-06-21"
                        time_srt = site_parts[2]  # e.g., "00:00:00"
                        date_end = site_parts[3]  # e.g., "25-06-21"
                        time_end = site_parts[4]  # e.g., "23:59:59"

                        # Convert 2-digit year to 4-digit year (YY -> 20YY)
                        if date_srt.startswith(('2', '3', '4', '5', '6', '7', '8', '9')):
                            date_srt = '20' + date_srt
                        if date_end.startswith(('2', '3', '4', '5', '6', '7', '8', '9')):
                            date_end = '20' + date_end

                        epoch_srt = f"{date_srt} {time_srt}"
                        epoch_end = f"{date_end} {time_end}"
                        ok_inp = parts[3]
                        ok_out = parts[4]

                        row_data = {
                            'epoch_exec': execution_timestamp,
                            'exec_time': execution_time if execution_time else '',
                            'site': site,
                            'epoch_srt': epoch_srt,
                            'epoch_end': epoch_end,
                            'ok_inp': ok_inp,
                            'ok_out': ok_out,
                        }
                        results.append(row_data)

    return results

def main():
    """Main function to process all download logs"""

    logs_dir = Path('/home/sakic/CODES/IPGP/autorino/logs_ovpf')
    output_csv = logs_dir.parent / 'download_logs_analysis.csv'

    # Find all download log files
    download_logs = sorted(logs_dir.glob('*_download.log'))

    print(f"Found {len(download_logs)} download log files")

    all_results = []

    for log_file in download_logs:
        print(f"Processing: {log_file.name}")
        results = parse_download_log(log_file)
        all_results.extend(results)

    print(f"\nTotal rows extracted: {len(all_results)}")

    # Write to CSV
    if all_results:
        fieldnames = ['epoch_exec', 'exec_time', 'site', 'epoch_srt', 'epoch_end', 'ok_inp', 'ok_out']

        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)

        print(f"\nCSV file created: {output_csv}")
    else:
        print("\nNo data extracted!")

if __name__ == '__main__':
    main()
