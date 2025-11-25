import os
import datetime

class Logger:
    """
    Custom logger class to handle output with timestamps and levels.
    """
    INFO = "INFO"
    ALERT = "ALERT"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

    def __init__(self, log_file="fim.log"):
        self.log_file = log_file

    def log(self, message, level=INFO):
        """Logs a message to console and file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # Console output with some basic coloring (ANSI escape codes)
        color_code = ""
        reset_code = "\033[0m"
        if level == self.ALERT:
            color_code = "\033[93m" # Yellow
        elif level == self.ERROR:
            color_code = "\033[91m" # Red
        elif level == self.SUCCESS:
            color_code = "\033[92m" # Green
        
        print(f"{color_code}{formatted_message}{reset_code}")

        # File output
        try:
            with open(self.log_file, "a") as f:
                f.write(formatted_message + "\n")
        except Exception as e:
            print(f"[-] Error writing to log file: {e}")

def walk_directory(directory):
    """
    Recursively traverses a directory and yields file paths.
    Replaces os.walk for manual implementation.
    """
    try:
        # Get list of all entries in the directory
        entries = os.listdir(directory)
    except PermissionError:
        return

    for entry in entries:
        full_path = os.path.join(directory, entry)
        
        if os.path.isdir(full_path):
            # Recursively yield files from subdirectories
            yield from walk_directory(full_path)
        elif os.path.isfile(full_path):
            yield full_path
