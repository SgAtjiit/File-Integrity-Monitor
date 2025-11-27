import os
import hashlib
import argparse
import json
from utils import Logger, walk_directory
import rsa_manual

logger = Logger()

def calculate_file_hash(filepath):
    """Calculates the SHA-256 hash of a file using hashlib."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (PermissionError, FileNotFoundError):
        return None

def create_baseline(directories, baseline_file="baseline.txt"):
    """Creates a baseline of file hashes for the given directories."""
    if isinstance(directories, str):
        directories = [directories]
    
    # Ensure keys exist
    if not os.path.exists("public_key.txt") or not os.path.exists("private_key.txt"):
        logger.log("RSA Keys not found. Generating new keypair...", Logger.WARNING)
        # Note: Make sure rsa_manual saves as .txt or update this check to .pem
        pub, priv = rsa_manual.generate_keypair()
        rsa_manual.save_keys(pub, priv)
        logger.log("RSA Keys generated and saved.", Logger.SUCCESS)

    try:
        with open(baseline_file, "w") as f:
            f.write(f"# MONITORED_DIRS:{json.dumps(directories)}\n")
            for directory in directories:
                if not os.path.exists(directory):
                    continue
                for filepath in walk_directory(directory):
                    if os.path.abspath(filepath) == os.path.abspath(baseline_file):
                        continue
                    file_hash = calculate_file_hash(filepath)
                    if file_hash:
                        f.write(f"{filepath}|{file_hash}\n")
        
        logger.log(f"Baseline created successfully in '{baseline_file}'.", Logger.SUCCESS)
        
        # Sign the baseline
        try:
            with open(baseline_file, "r") as f:
                content = f.read()
            
            pub, priv = rsa_manual.load_keys()
            if priv:
                signature = rsa_manual.sign(content, priv)
                with open(baseline_file + ".sig", "w") as f:
                    f.write(signature)
                logger.log("Baseline signed successfully.", Logger.SUCCESS)
            else:
                logger.log("Private key not found. Cannot sign baseline.", Logger.WARNING)
        except Exception as e:
            logger.log(f"Error signing baseline: {e}", Logger.ERROR)

        return True, "Baseline created successfully."
    except Exception as e:
        logger.log(f"Error writing baseline file: {e}", Logger.ERROR)
        return False, str(e)

def check_integrity(baseline_file="baseline.txt"):
    """Checks file integrity against the baseline and returns scan logs."""
    scan_logs = []
    orig_log = logger.log
    
    def scan_log(msg, level=None):
        scan_logs.append(msg)
        orig_log(msg, level)
    
    # FIX: Patch the logger
    logger.log = scan_log

    # FIX: Use try/finally to ensure logger is ALWAYS restored, even if errors occur
    try:
        logger.log(f"Checking integrity using baseline: {baseline_file}", Logger.INFO)
        if not os.path.exists(baseline_file):
            logger.log(f"Baseline file '{baseline_file}' not found. Please run with -b first.", Logger.ERROR)
            return {"status": "error", "message": "Baseline not found", "events": [], "scan_logs": scan_logs}

        # Verify Baseline Signature
        try:
            if os.path.exists(baseline_file + ".sig"):
                with open(baseline_file, "r") as f:
                    content = f.read()
                with open(baseline_file + ".sig", "r") as f:
                    signature = f.read().strip()
                
                pub, priv = rsa_manual.load_keys()
                if pub:
                    if rsa_manual.verify(content, signature, pub):
                        logger.log("Baseline signature verified.", Logger.SUCCESS)
                        scan_logs.append("Baseline signature verified (Integrity OK).")
                    else:
                        msg = "CRITICAL: Baseline signature verification FAILED! The baseline file may have been tampered with."
                        logger.log(msg, Logger.ERROR)
                        scan_logs.append(msg)
                        return {"status": "error", "message": msg, "events": [], "scan_logs": scan_logs}
                else:
                     scan_logs.append("Public key not found. Skipping signature verification.")
            else:
                scan_logs.append("No signature found for baseline. Skipping verification.")
        except Exception as e:
            logger.log(f"Error verifying signature: {e}", Logger.ERROR)
            scan_logs.append(f"Error verifying signature: {e}")

        baseline = {}
        monitored_dirs = []
        try:
            with open(baseline_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        if line.startswith("# MONITORED_DIRS:"):
                            try:
                                monitored_dirs = json.loads(line.split(":", 1)[1])
                            except json.JSONDecodeError:
                                monitored_dirs = line.split(":", 1)[1].split(",")
                        continue
                    if "|" in line:
                        path, file_hash = line.split("|", 1)
                        baseline[path] = file_hash
        except Exception as e:
            logger.log(f"Error reading baseline file: {e}", Logger.ERROR)
            return {"status": "error", "message": str(e), "events": [], "scan_logs": scan_logs}

        logger.log(f"Baseline loaded. {len(baseline)} files to check.", Logger.INFO)

        files_checked = set()
        changes_detected = False
        events = []

        # Check for modifications and deletions
        for filepath, original_hash in baseline.items():
            if os.path.exists(filepath):
                current_hash = calculate_file_hash(filepath)
                files_checked.add(os.path.abspath(filepath))
                if current_hash is None:
                    logger.log(f"Could not access file -> {filepath}", Logger.ERROR)
                    changes_detected = True
                    events.append({
                        "type": "ERROR",
                        "path": filepath,
                        "message": "Could not access file",
                        "baseline_checksum": original_hash,
                        "current_checksum": None
                    })
                elif current_hash != original_hash:
                    logger.log(f"File MODIFIED -> {filepath}", Logger.ALERT)
                    changes_detected = True
                    events.append({
                        "type": "MODIFIED",
                        "path": filepath,
                        "message": "File content changed",
                        "baseline_checksum": original_hash,
                        "current_checksum": current_hash
                    })
                else:
                    pass  # File is unchanged
            else:
                logger.log(f"File DELETED -> {filepath}", Logger.ALERT)
                changes_detected = True
                events.append({
                    "type": "DELETED",
                    "path": filepath,
                    "message": "File deleted",
                    "baseline_checksum": original_hash,
                    "current_checksum": None
                })

        # Check for NEW files
        if monitored_dirs:
            for directory in monitored_dirs:
                if not os.path.exists(directory):
                    continue
                for filepath in walk_directory(directory):
                    if os.path.abspath(filepath) == os.path.abspath(baseline_file):
                        continue
                    if os.path.abspath(filepath) not in files_checked:
                        is_known = False
                        # Backup check using absolute paths to be safe
                        for known_path in baseline.keys():
                            if os.path.abspath(known_path) == os.path.abspath(filepath):
                                is_known = True
                                break
                        if not is_known:
                            current_hash = calculate_file_hash(filepath)
                            logger.log(f"File ADDED (New) -> {filepath}", Logger.ALERT)
                            changes_detected = True
                            events.append({
                                "type": "ADDED",
                                "path": filepath,
                                "message": "New file detected",
                                "baseline_checksum": None,
                                "current_checksum": current_hash
                            })

        if not changes_detected:
            logger.log("Files are secure. No changes detected.", Logger.SUCCESS)

        logger.log("Integrity check complete.", Logger.INFO)

        return {
            "status": "changed" if changes_detected else "clean",
            "message": "Integrity check complete.",
            "events": events,
            "checked_count": len(files_checked),
            "scan_logs": scan_logs
        }
    finally:
        # FIX: Always restore the logger
        logger.log = orig_log

def get_monitored_directories(baseline_file="baseline.txt"):
    """Retrieves the list of monitored directories from the baseline file."""
    if not os.path.exists(baseline_file):
        return []
    try:
        with open(baseline_file, "r") as f:
            for line in f:
                if line.startswith("# MONITORED_DIRS:"):
                    try:
                        return json.loads(line.split(":", 1)[1])
                    except json.JSONDecodeError:
                        return line.split(":", 1)[1].split(",")
    except Exception:
        pass
    return []

# ... (rest of the file: show_menu, main, etc. remains the same)
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
            dirs = input("Enter directory paths (comma separated): ").strip().split(",")
            create_baseline([d.strip() for d in dirs])
        elif choice == '2':
            check_integrity()
        elif choice == '3':
            print("Monitored directories:", get_monitored_directories())
        elif choice == '4':
            print("Available directories:")
            for d in get_monitored_directories():
                print("-", d)
        elif choice == '5':
            dirs = get_monitored_directories()
            print("Currently monitored:", dirs)
            rem = input("Enter directory to remove: ").strip()
            if rem in dirs:
                dirs.remove(rem)
                create_baseline(dirs)
            else:
                print("Directory not found.")
        elif choice == '6':
            if os.path.exists("baseline.txt"):
                os.remove("baseline.txt")
            print("All monitored directories cleared.")
        elif choice == '7':
            print("Exiting.")
            break
        else:
            print("Invalid choice.")

def main():
    parser = argparse.ArgumentParser(description="File Integrity Monitor (FIM) - Enhanced")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-b", "--baseline", metavar="DIRECTORY", nargs='+', help="Create a baseline for the specified directory or directories")
    group.add_argument("-c", "--check", metavar="BASELINE_FILE", nargs="?", const="baseline.txt", help="Check integrity against a baseline file (default: baseline.txt)")
    args = parser.parse_args()
    if args.baseline:
        create_baseline(args.baseline)
    elif args.check:
        check_integrity(args.check)
    else:
        show_menu()

if __name__ == "__main__":
    main()