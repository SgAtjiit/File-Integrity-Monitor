import argparse
import os
import sys
import hashlib
from utils import Logger, walk_directory

# Initialize Logger
logger = Logger()

def calculate_file_hash(filepath):
    """Calculates the SHA-256 hash of a file using hashlib."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Read the file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (PermissionError, FileNotFoundError):
        return None

def create_baseline(directories, baseline_file="baseline.txt"):
    """Creates a baseline of file hashes for the given directories."""
    # Ensure directories is a list
    if isinstance(directories, str):
        directories = [directories]
        
    try:
        with open(baseline_file, "w") as f:
            # Write header with monitored directories
            f.write(f"# MONITORED_DIRS:{','.join(directories)}\n")
            
            for directory in directories:
                logger.log(f"Creating baseline for: {directory}", Logger.INFO)
                
                if not os.path.exists(directory):
                    logger.log(f"Directory '{directory}' not found.", Logger.ERROR)
                    continue

                # Use custom directory walker
                for filepath in walk_directory(directory):
                    # Skip the baseline file itself if it's in the target directory
                    if os.path.abspath(filepath) == os.path.abspath(baseline_file):
                        continue
                        
                    file_hash = calculate_file_hash(filepath)
                    
                    if file_hash:
                        f.write(f"{filepath}|{file_hash}\n")
                        logger.log(f"Hashed: {filepath}", Logger.SUCCESS)
                    else:
                        logger.log(f"Could not access: {filepath}", Logger.ERROR)
        
        logger.log(f"Baseline created successfully in '{baseline_file}'.", Logger.SUCCESS)
    except Exception as e:
        logger.log(f"Error writing baseline file: {e}", Logger.ERROR)

def check_integrity(baseline_file="baseline.txt"):
    """Checks file integrity against the baseline."""
    logger.log(f"Checking integrity using baseline: {baseline_file}", Logger.INFO)
    
    if not os.path.exists(baseline_file):
        logger.log(f"Baseline file '{baseline_file}' not found. Please run with -b first.", Logger.ERROR)
        return

    baseline = {}
    monitored_dirs = []
    
    try:
        with open(baseline_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# MONITORED_DIRS:"):
                    monitored_dirs = line.split(":")[1].split(",")
                    continue
                    
                parts = line.split("|")
                if len(parts) == 2:
                    baseline[parts[0]] = parts[1]
    except Exception as e:
        logger.log(f"Error reading baseline file: {e}", Logger.ERROR)
        return

    logger.log(f"Baseline loaded. {len(baseline)} files to check.", Logger.INFO)

    files_checked = set()
    changes_detected = False
    
    # Check for modifications and deletions
    for filepath, original_hash in baseline.items():
        if os.path.exists(filepath):
            current_hash = calculate_file_hash(filepath)
            files_checked.add(os.path.abspath(filepath))
            
            if current_hash is None:
                 logger.log(f"Could not access file -> {filepath}", Logger.ERROR)
                 changes_detected = True
            elif current_hash != original_hash:
                logger.log(f"File MODIFIED -> {filepath}", Logger.ALERT)
                changes_detected = True
            else:
                pass # File is unchanged
        else:
            logger.log(f"File DELETED -> {filepath}", Logger.ALERT)
            changes_detected = True

    # Check for NEW files
    if monitored_dirs:
        for directory in monitored_dirs:
            if not os.path.exists(directory):
                continue
                
            for filepath in walk_directory(directory):
                # Skip baseline file
                if os.path.abspath(filepath) == os.path.abspath(baseline_file):
                    continue
                    
                if os.path.abspath(filepath) not in files_checked:
                    # Check if it was in baseline (deleted files are handled above, but just in case)
                    # We need to compare absolute paths because baseline keys might be relative
                    is_known = False
                    for known_path in baseline.keys():
                        if os.path.abspath(known_path) == os.path.abspath(filepath):
                            is_known = True
                            break
                    
                    if not is_known:
                        logger.log(f"File ADDED (New) -> {filepath}", Logger.ALERT)
                        changes_detected = True

    if not changes_detected:
        logger.log("Files are secure. No changes detected.", Logger.SUCCESS)
    
    logger.log("Integrity check complete.", Logger.INFO)

def get_monitored_directories(baseline_file="baseline.txt"):
    """Retrieves the list of monitored directories from the baseline file."""
    if not os.path.exists(baseline_file):
        return []
        
    try:
        with open(baseline_file, "r") as f:
            first_line = f.readline().strip()
            if first_line.startswith("# MONITORED_DIRS:"):
                return first_line.split(":")[1].split(",")
    except Exception:
        pass
    return []

def show_menu():
    """Displays the interactive menu."""
    while True:
        print("\n" + "="*40)
        print("    FILE INTEGRITY MONITOR (v1.0)")
        print("="*40)
        print("1. Create New Baseline (Add/Monitor New Directory)")
        print("2. Check File Integrity")
        print("3. Show Monitored Directories")
        print("4. List Available Directories")
        print("5. Remove Monitored Directory")
        print("6. Clear All Monitored Directories")
        print("7. Exit")
        print("="*40)
        
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == '1':
            print("\n[?] Tip: You can enter multiple folders separated by spaces.")
            directory_input = input("Enter directory(s) to monitor: ").strip()
            
            if directory_input:
                directories = directory_input.split()
                # Validate directories before passing them
                valid_dirs = []
                for d in directories:
                    if os.path.exists(d):
                        valid_dirs.append(d)
                    else:
                        print(f"[-] Warning: Directory '{d}' not found. Skipping.")
                
                if valid_dirs:
                    # Check if baseline exists and is not empty
                    if os.path.exists("baseline.txt") and os.path.getsize("baseline.txt") > 0:
                        print("\n[!] Baseline already exists.")
                        action = input("Do you want to (O)verwrite it or (A)ppend new folders? [o/A]: ").strip().lower()
                        
                        if action == 'o':
                            create_baseline(valid_dirs)
                        elif action == 'a' or action == '':
                            # Append mode: Get existing dirs, merge, and re-baseline
                            existing_dirs = get_monitored_directories("baseline.txt")
                            # Combine and remove duplicates while preserving order
                            all_dirs = existing_dirs + [d for d in valid_dirs if d not in existing_dirs]
                            create_baseline(all_dirs)
                        else:
                            print("[!] Invalid option. Operation cancelled.")
                    else:
                        create_baseline(valid_dirs)
                else:
                    print("[-] Error: No valid directories provided. Please try again.")
            else:
                print("[-] Error: No directory provided.")
                
        elif choice == '2':
            baseline_file = "baseline.txt"
            
            if os.path.exists(baseline_file):
                check_integrity(baseline_file)
            else:
                print(f"[-] Error: Baseline file '{baseline_file}' not found. Please create one first.")
        
        elif choice == '3':
            baseline_file = "baseline.txt"
                
            dirs = get_monitored_directories(baseline_file)
            if dirs:
                print(f"\n[+] Monitored Directories in '{baseline_file}':")
                for d in dirs:
                    print(f"  - {d}")
            else:
                print(f"[-] No monitored directories found in '{baseline_file}' or file does not exist.")

        elif choice == '4':
            print("\n[+] Available Directories in current location:")
            try:
                # List all subdirectories in the current directory
                subdirs = [d for d in os.listdir('.') if os.path.isdir(d)]
                if subdirs:
                    for d in subdirs:
                        # Skip hidden directories like .git
                        if not d.startswith('.'):
                            print(f"  - {d}")
                else:
                    print("  [-] No subdirectories found.")
            except Exception as e:
                print(f"[-] Error listing directories: {e}")

        elif choice == '5':
            baseline_file = "baseline.txt"
            current_dirs = get_monitored_directories(baseline_file)
            
            if current_dirs:
                print(f"\n[+] Currently Monitored Directories:")
                for i, d in enumerate(current_dirs):
                    print(f"  - {d}")
                
                dir_to_remove = input("\nEnter directory name to remove: ").strip()
                
                if dir_to_remove in current_dirs:
                    confirm = input(f"Are you sure you want to stop monitoring '{dir_to_remove}'? (y/n): ").strip().lower()
                    if confirm == 'y':
                        current_dirs.remove(dir_to_remove)
                        if current_dirs:
                            print("[+] Updating baseline...")
                            create_baseline(current_dirs)
                        else:
                            print("[+] No directories left. Deleting baseline.")
                            if os.path.exists(baseline_file):
                                os.remove(baseline_file)
                    else:
                        print("[!] Operation cancelled.")
                else:
                    print(f"[-] Error: Directory '{dir_to_remove}' is not currently monitored.")
            else:
                print(f"[-] No monitored directories found in '{baseline_file}'.")

        elif choice == '6':
            if os.path.exists("baseline.txt"):
                confirm = input("Are you sure you want to CLEAR ALL monitored directories and delete the baseline? (y/n): ").strip().lower()
                if confirm == 'y':
                    os.remove("baseline.txt")
                    print("[+] Baseline deleted. All directories cleared.")
                else:
                    print("[!] Operation cancelled.")
            else:
                print("[-] No baseline found to clear.")

        elif choice == '7':
            print("Exiting...")
            break
        else:
            print("[-] Invalid choice. Please try again.")

def main():
    parser = argparse.ArgumentParser(description="File Integrity Monitor (FIM) - Enhanced")
    # Make arguments optional to allow for menu mode
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-b", "--baseline", metavar="DIRECTORY", nargs='+', help="Create a baseline for the specified directory or directories")
    group.add_argument("-c", "--check", metavar="BASELINE_FILE", nargs="?", const="baseline.txt", help="Check integrity against a baseline file (default: baseline.txt)")
    
    args = parser.parse_args()

    # If arguments are provided, use CLI mode
    if args.baseline:
        create_baseline(args.baseline)
    elif args.check:
        check_integrity(args.check)
    else:
        # If no arguments, show interactive menu
        show_menu()

if __name__ == "__main__":
    main()
