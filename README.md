# File Integrity Monitor

File Integrity Monitor (FIM) is a local web application for tracking changes in files under one or more monitored directories. The backend creates a signed baseline of SHA-256 checksums and compares later scans against it. The React dashboard manages monitored directories, runs scans, displays events and logs, and keeps scan history in the browser.

## Features

- Add and remove monitored directories from the dashboard.
- Create a baseline containing a SHA-256 checksum for every readable file.
- Detect modified, deleted, and newly added files.
- Sign the baseline and verify its signature before an integrity scan.
- View scan events and backend logs in the dashboard.
- Export displayed logs with the built-in Caesar cipher and decrypt text with the matching shift.
- Persist recent scan history in browser `localStorage` for charting and review.

## Architecture

```text
React + Vite frontend (localhost:5173)
                |
                | HTTP JSON requests to /api
                v
Flask backend (localhost:5000)
                |
                +-- baseline.txt       monitored paths and file hashes
                +-- baseline.txt.sig   signature for the baseline
                +-- public_key.txt     RSA public key
                +-- private_key.txt    RSA private key
                +-- fim.log            backend log file
```

The frontend calls the backend directly through the fixed URL `http://localhost:5000/api` in [frontend/src/api.js](frontend/src/api.js). CORS is enabled by the Flask application for local development.

## Requirements

- Python 3.9 or newer
- Node.js 18 or newer and npm

## Run Locally

Open two terminals from the repository root.

### 1. Start the backend

Run the backend from `server/`. Its working directory matters because the baseline, signature, keys, and log file are read and written there.

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

The API is available at `http://localhost:5000`. The first baseline creation generates `public_key.txt` and `private_key.txt` if they do not already exist.

### 2. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

## Typical Workflow

1. Start the backend and frontend.
2. Enter an existing directory path in **Target Directories** and add it.
3. Adding a directory creates or replaces the baseline for all currently monitored directories.
4. Run an integrity scan after files have been added, changed, or deleted.
5. Review the event type and baseline/current checksums in the scan result.
6. Export the displayed scan logs if needed. The export response is downloaded as a text file encrypted with the selected Caesar shift.

Paths are normalized to absolute paths by the backend. A directory must exist before it can be monitored. Removing the final monitored directory deletes the baseline file.

## API Reference

All endpoints are relative to `http://localhost:5000/api`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/status` | Check that the backend is running. |
| `GET` | `/directories` | Return the directories stored in the baseline. |
| `POST` | `/directories` | Add a directory. Body: `{ "path": "..." }`. |
| `DELETE` | `/directories` | Remove a directory. Body: `{ "path": "..." }`. |
| `POST` | `/check` | Verify the baseline and scan for file changes. |
| `GET` | `/logs` | Return the last 100 backend log lines, newest first. |
| `POST` | `/logs/export` | Encrypt logs. Body: `{ "logs": [], "shift": 3 }`. |
| `POST` | `/decrypt` | Decrypt text. Body: `{ "text": "...", "shift": 3 }`. |

An integrity scan returns `clean` when no changes are found, `changed` when events are detected, or `error` when the baseline cannot be read or its signature verification fails. Each event includes its type, path, message, and available baseline/current checksum.

## Command-Line Backend

The monitoring logic can also be used without the web dashboard. From `server/` with the virtual environment active:

```bash
# Create a baseline for one or more directories
python fim.py --baseline /absolute/path/to/folder
python fim.py --baseline /absolute/path/one /absolute/path/two

# Check an existing baseline
python fim.py --check
python fim.py --check /absolute/path/to/baseline.txt

# Open the interactive menu
python fim.py
```

## Project Layout

```text
frontend/
  src/App.jsx          Dashboard UI and scan state
  src/api.js           Backend API client
  src/index.css        Global styles and Tailwind entry point
  package.json         Frontend scripts and dependencies

server/
  app.py               Flask API and CORS setup
  fim.py               Baseline creation and integrity scanning
  rsa_manual.py        Baseline signing and verification
  cipher_manual.py     Caesar log encryption/decryption
  utils.py              Logging and recursive directory traversal
  requirements.txt      Python runtime dependencies

demoFiles/              Sample directories for local testing
```

## Development Commands

From `frontend/`:

```bash
npm run lint
npm run build
npm run preview
```

The repository currently does not include an automated Python test suite. A quick backend syntax check is:

```bash
python -m py_compile server/*.py
```

## Security Notes

This project is intended for local demonstration and development. The baseline is hashed with SHA-256 and signed with the custom RSA implementation in `rsa_manual.py`. Log export uses a Caesar cipher, which is obfuscation rather than secure encryption. The Flask server runs with debug mode enabled, the API has no authentication, and the private key is stored as a local text file; do not expose this setup directly to an untrusted network or use it as a production security control without replacing those parts.

Keep `private_key.txt`, `baseline.txt`, `baseline.txt.sig`, and `fim.log` protected. Generated baseline and log files are ignored by Git; key files are not currently ignored, so review repository status before committing changes.