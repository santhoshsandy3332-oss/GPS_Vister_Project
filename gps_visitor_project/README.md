# GPS Visitor Information Collection System

A Flask website with a public visitor form, browser-permission-based GPS collection, SQLite storage, a password-protected admin dashboard, a visitor map, and CSV export.

## Requirements

- Python 3.10 or newer
- A modern browser
- HTTPS for public deployment (browser geolocation generally requires a secure context; localhost is allowed for development)

## Run locally

1. Open a terminal in this folder.
2. Create and activate a virtual environment:

   **Windows**
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables. For a quick local PowerShell session:

   ```powershell
   $env:SECRET_KEY = "replace-this-with-a-long-random-value"
   $env:ADMIN_USERNAME = "admin"
   ```

   Generate a password hash:

   ```bash
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Choose-A-Strong-Password'))"
   ```

   Copy the printed hash into `ADMIN_PASSWORD_HASH`. In PowerShell:

   ```powershell
   $env:ADMIN_PASSWORD_HASH = "paste-the-generated-hash-here"
   ```

   On macOS/Linux, use `export NAME="value"` instead of `$env:NAME = "value"`.

5. Start the app:

   ```bash
   python app.py
   ```

6. Open:
   - Public registration: http://127.0.0.1:5000/
   - Admin login: http://127.0.0.1:5000/admin/login

The first run creates `visitors.db` automatically.

## How it works

- Visitors enter a name and email address.
- The form explains why location is requested and asks for consent.
- On submit, the browser requests GPS/device location permission.
- If permission is granted, latitude, longitude and reported accuracy are sent to Flask.
- The server attempts to reverse-geocode coordinates into a readable place using OpenStreetMap Nominatim. If lookup fails, coordinates are still stored and the place is shown as unresolved.
- Admin users can view records, search, inspect map markers and export CSV.

## Deployment checklist

1. Deploy to a Python-capable host (for example, Render or another Flask host).
2. Configure `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD_HASH` as environment variables.
3. Use HTTPS. Browser geolocation will not normally work on an insecure public HTTP origin.
4. Configure a persistent disk/volume and set `DATABASE_PATH` to a file on that disk. Ephemeral hosting filesystems can erase SQLite data on redeploy.
5. Use a strong unique admin password and do not publish `.env` or secrets.
6. Replace the sample Nominatim User-Agent with an identifiable application name and a contact email. Follow the current Nominatim usage policy; for high-volume use, choose a commercial geocoding provider or host your own service.
7. Add a privacy notice, data retention/deletion process, and any consent/legal requirements applicable to your deployment.

## Routes

- `GET /` — public registration page
- `POST /submit` — save a visitor registration
- `GET /admin/login` — admin login
- `GET /admin` — dashboard (login required)
- `GET /admin/export.csv` — download CSV (login required)
- `POST /admin/logout` — log out

## Important limitations and privacy

- GPS accuracy depends on the visitor's device, operating system, browser, signal and environment. It is not guaranteed to identify an exact building or address.
- Visitors can deny permission. This starter project requires permission to complete registration; change that policy only if your stated purpose and privacy notice support it.
- Do not use this system for covert tracking. Tell visitors what is collected, why, how long it is retained, and who can access it.
- The starter uses a single admin account configured through environment variables. For a production multi-admin system, add account management, login throttling, audit logging, backups and stronger operational controls.
- The Nominatim lookup is best-effort and subject to its service policy and availability.
