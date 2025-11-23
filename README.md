# Flask Daily Task Tracker

Simple Flask web app to add, edit, delete, and mark daily tasks as completed. Uses SQLite (Flask-SQLAlchemy). Built to satisfy the Python Developer Screening Task.

## Run locally (development)
1. Create virtual env and install:
   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS / Linux
   venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

2. Run:
   ```bash
   python app.py
   ```
   Open http://127.0.0.1:5000

## Deployment (Render / Railway)
1. Push repo to GitHub.
2. Create a new Web service on Render (or Railway).
3. Connect to your GitHub repo.
4. Set build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. Set environment variable `FLASK_SECRET` on the host for production.
