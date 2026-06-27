# Background Remover

Deploy on Render with:
- `app.py`
- `requirements.txt`
- `Procfile`
- `render.yaml`
- `.python-version`

## Notes
- The app uses `rembg` with the lightweight `u2netp` model by default.
- First launch may take a moment while the model loads.
- If you want to change the model, set `REMBG_MODEL` in Render environment variables.
