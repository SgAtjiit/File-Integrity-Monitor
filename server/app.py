from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import fim
import cipher_manual
from utils import Logger

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Use absolute path for baseline to avoid CWD confusion
BASELINE_FILE = os.path.abspath("baseline.txt")
LOG_FILE = "fim.log"

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "running", "message": "FIM Backend is active"})

@app.route('/api/directories', methods=['GET'])
def get_directories():
    dirs = fim.get_monitored_directories(BASELINE_FILE)
    return jsonify({"directories": dirs})

@app.route('/api/directories', methods=['POST'])
def add_directory():
    data = request.json
    paths = data.get('paths')
    if isinstance(paths, str):
        paths = [paths]
    # Support legacy single path
    if not paths:
        path = data.get('path')
        if path:
            paths = [path]
    
    if not paths:
        return jsonify({"error": "Path(s) required"}), 400
        
    # Validate paths and normalize to Absolute Paths
    valid_paths = []
    errors = []
    for p in paths:
        p = p.strip()
        if os.path.exists(p):
            # FIX: Normalize to absolute path to prevent duplicates (e.g., "." vs full path)
            valid_paths.append(os.path.abspath(p))
        else:
            errors.append(f"Directory does not exist: {p}")
            
    if not valid_paths:
        return jsonify({"error": "No valid directories provided", "details": errors}), 404
        
    # Get existing directories
    current_dirs = fim.get_monitored_directories(BASELINE_FILE)
    
    added_count = 0
    for p in valid_paths:
        if p not in current_dirs:
            current_dirs.append(p)
            added_count += 1
            
    if added_count == 0:
        return jsonify({"message": "All directories already monitored", "directories": current_dirs})
        
    # Update baseline
    success, message = fim.create_baseline(current_dirs, BASELINE_FILE)
    
    if success:
        return jsonify({
            "message": f"Added {added_count} new directories", 
            "directories": current_dirs,
            "errors": errors if errors else None
        })
    else:
        return jsonify({"error": message}), 500

@app.route('/api/directories', methods=['DELETE'])
def remove_directory():
    data = request.json
    path = data.get('path')
    
    if not path:
        return jsonify({"error": "Path is required"}), 400
        
    current_dirs = fim.get_monitored_directories(BASELINE_FILE)
    
    # FIX: Normalize path to match stored absolute paths
    abs_path = os.path.abspath(path.strip())
    
    if abs_path not in current_dirs:
        return jsonify({"error": "Directory not found in monitored list"}), 404
        
    current_dirs.remove(abs_path)
    
    if not current_dirs:
        # If no directories left, remove baseline
        if os.path.exists(BASELINE_FILE):
            os.remove(BASELINE_FILE)
        return jsonify({"message": "Directory removed. No directories left monitored.", "directories": []})
    
    success, message = fim.create_baseline(current_dirs, BASELINE_FILE)
    
    if success:
        return jsonify({"message": "Directory removed successfully", "directories": current_dirs})
    else:
        return jsonify({"error": message}), 500

@app.route('/api/check', methods=['POST'])
def check_integrity():
    if not os.path.exists(BASELINE_FILE):
        return jsonify({"error": "No baseline found. Please add a directory first."}), 400
        
    result = fim.check_integrity(BASELINE_FILE)
    return jsonify(result)

@app.route('/api/logs', methods=['GET'])
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify({"logs": []})
        
    try:
        with open(LOG_FILE, "r") as f:
            # Read last 100 lines
            lines = f.readlines()
            last_logs = lines[-100:]
            last_logs.reverse() # Newest first
            return jsonify({"logs": [line.strip() for line in last_logs]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/export', methods=['POST'])
def export_logs():
    data = request.json
    shift = data.get('shift', 0)
    logs = data.get('logs', [])
    
    # Combine logs into a single string
    log_text = "\n".join(logs)
    
    # Encrypt using Caesar Cipher
    encrypted_text = cipher_manual.caesar_encrypt(log_text, int(shift))
    
    return jsonify({
        "encrypted_logs": encrypted_text,
        "filename": f"fim_logs_encrypted_shift_{shift}.txt"
    })

@app.route('/api/decrypt', methods=['POST'])
def decrypt_text():
    data = request.json
    text = data.get('text', '')
    shift = data.get('shift', 0)
    
    try:
        shift_val = int(shift)
    except (ValueError, TypeError):
        shift_val = 0
    
    decrypted_text = cipher_manual.caesar_decrypt(text, shift_val)
    
    return jsonify({"decrypted_text": decrypted_text})

if __name__ == '__main__':
    app.run(debug=True, port=5000)