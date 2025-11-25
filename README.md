# Python File Integrity Monitor (FIM)

A robust, lightweight, and interactive File Integrity Monitor built in Python. This tool helps you monitor changes to your files and directories, detecting modifications, deletions, and new file creations.

## Features

*   **Real-time Integrity Checking**: Calculates SHA-256 hashes of files to detect unauthorized changes.
*   **Multiple Directory Support**: Monitor multiple folders simultaneously.
*   **Interactive Menu System**: User-friendly CLI menu for easy navigation.
*   **Smart Baseline Management**:
    *   **Create**: Establish a trusted state for your files.
    *   **Append**: Add new directories to an existing baseline without losing previous data.
    *   **Overwrite**: Completely reset the baseline if needed.
*   **Comprehensive Detection**:
    *   **Modified Files**: Detects content changes.
    *   **Deleted Files**: Alerts when a monitored file is removed.
    *   **New Files**: Detects unauthorized files added to monitored directories.
*   **Audit Logging**: detailed logs of all operations are saved to `fim.log`.

## Prerequisites

*   **Python 3.x** (Pre-installed on most modern systems)
*   No external libraries required! (Uses standard `hashlib`, `os`, `sys`, `argparse`).

## Installation

1.  Clone this repository:
    ```bash
    git clone <repository-url>
    cd File-Integrity-Monitor
    ```

## Usage

Run the script using Python:

```bash
python fim.py
```

### Interactive Menu Options

1.  **Create New Baseline (Add/Monitor New Directory)**:
    *   Enter the path(s) of the folder(s) you want to secure.
    *   If a baseline exists, you can choose to **Append** (add new folders) or **Overwrite** (start fresh).
2.  **Check File Integrity**:
    *   Scans all monitored files and compares them against the stored baseline.
    *   Reports any discrepancies (Modified, Deleted, or New files).
3.  **Show Monitored Directories**:
    *   Lists all folders currently being watched.
4.  **List Available Directories**:
    *   Shows subfolders in the current directory to help you choose what to monitor.
5.  **Remove Monitored Directory**:
    *   Stop monitoring a specific folder.
6.  **Clear All Monitored Directories**:
    *   Deletes the baseline and resets the tool.
7.  **Exit**: Closes the application.

## CLI Mode (Advanced)

You can also run the tool directly with command-line arguments for automation:

*   **Create Baseline**:
    ```bash
    python fim.py -b "path/to/folder1" "path/to/folder2"
    ```
*   **Check Integrity**:
    ```bash
    python fim.py -c
    ```

## Project Structure

*   `fim.py`: Main application script.
*   `utils.py`: Helper functions for logging and directory walking.
*   `baseline.txt`: Stores the trusted file hashes (generated).
*   `fim.log`: Audit log of all activities (generated).

