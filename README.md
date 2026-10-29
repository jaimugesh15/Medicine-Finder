# MedicineFinder

A Flask + SQLite website that helps people find nearby pharmacies and check **reported** medicine availability,
with a private dashboard where pharmacies manage their own inventory. College Design Thinking project.

* **Public site:** home, medicine search, nearby pharmacies (Leaflet / OpenStreetMap), pharmacy details, About / FAQ / Contact.
* **Dashboard (`/dashboard`):** KPIs, Chart.js charts, activity log, inventory CRUD, quick stock updates, low-stock list, pharmacy profile, settings.
* MedicineFinder gives **no medical advice** and never suggests substitutes. Stock labels always show their update time.

## Run it in VS Code

1. Install **Python 3.10+** and open this folder in VS Code (`File > Open Folder`).
2. Open a terminal (`Terminal > New Terminal`) and create a virtual environment:

   ```bash
   python -m venv .venv
   # Windows (PowerShell):  .venv\Scripts\Activate.ps1      (if blocked: Set-ExecutionPolicy -Scope Process Bypass)
   # macOS / Linux:         source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create your settings file: copy `.env.example` to `.env` and put a random `SECRET_KEY` in it
   (`python -c "import secrets; print(secrets.token_hex(32))"`). If you skip this, a key is generated once in `instance/.secret_key`.
4. (Optional) add **clearly labelled sample data** for development only:

   ```bash
   flask --app app seed-demo --password "ChooseAPassword123"
   ```
   Login: `demo@medicinefinder.local` + that password. Sample pharmacies are marked **Sample**, use fake phone numbers and
   approximate locations, and are never real inventory. No default password is stored anywhere in the code.
5. Start the site: `flask --app app run --debug` (or press F5 / run `python app.py`), then open <http://127.0.0.1:5000>.
   Without sample data, click **Register your pharmacy** and create your own account.

Internet is needed for fonts, Font Awesome, Chart.js, Leaflet and map tiles (CDNs).

## Useful commands

| Task | Command |
| --- | --- |
| Run tests | `python -m unittest discover -s tests -v` |
| Reset database (deletes everything) | `flask --app app reset-db --yes` |
| Start fresh with sample data | reset, then `seed-demo` again |

The database is created automatically at `instance/medicinefinder.db`. Normal startup never deletes data.

## Stock status rules (one place: `Medicine.status` in `models.py`)

| Condition | Status |
| --- | --- |
| Stock not marked **verified** | Unknown |
| Verified and quantity = 0 | Out of stock |
| Verified and 0 < quantity <= reorder level | Low stock |
| Verified and quantity > reorder level | Available |

## Project structure

```
app.py            app factory + `seed-demo` / `reset-db` commands
config.py         settings from environment variables      extensions.py   db, login, csrf objects
models.py         User, Pharmacy, Medicine (inventory item), InventoryActivity
forms.py          Flask-WTF forms and validation            services.py     stock summary, activity log, search, distance
routes/           public.py, auth.py, dashboard.py
templates/        public pages, _macros.html, dashboard/*   static/          css/, js/, images/logo.svg (also the favicon)
tests/            unittest suite
```

Differences from the suggested layout (to keep it simple for a student project): models live in one `models.py`,
`Inventory` is stored on the `Medicine` row (each pharmacy owns its medicine records), and inventory routes are inside `routes/dashboard.py`.

## Security notes

Passwords are hashed (Werkzeug); CSRF protection on every form; secrets come from the environment; SQLAlchemy parameterises all queries;
every `/dashboard` route requires login and every medicine lookup is filtered by the logged-in pharmacy (other pharmacies get a 404);
logout is a POST; session cookies are HttpOnly + SameSite=Lax (set `SESSION_COOKIE_SECURE=1` when using HTTPS).
This is a prototype: before real use add rate limiting, email verification, password reset, HTTPS hosting, and legal review of
medicine-sale regulations in India and your state.

## Map notes

Tiles come from the OpenStreetMap standard tile server, with attribution. Your location is requested only when you press
**Use my location**, is used in the browser/for one request, and is not stored. The "type a place" box sends one request to Nominatim
only when you submit it. For heavy or production use, switch to your own tile/geocoding provider per OSM's usage policies.
