from __future__ import annotations

import io
import os
import threading
import traceback
from typing import Optional

from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from PIL import Image, ImageOps

try:
    from rembg import new_session, remove
except Exception:
    new_session = None
    remove = None

app = Flask(__name__)
CORS(app)

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "10"))
MAX_EDGE_PX = int(os.environ.get("MAX_EDGE_PX", "1600"))
REMBG_MODEL = os.environ.get("REMBG_MODEL", "u2netp")

_session_lock = threading.Lock()
_session = None
_session_error: Optional[str] = None
_session_ready = False


def _load_session():
    global _session, _session_error, _session_ready
    if new_session is None:
        _session_error = "rembg is not installed on the server."
        _session_ready = False
        return

    try:
        session = new_session(REMBG_MODEL)
        with _session_lock:
            _session = session
            _session_error = None
            _session_ready = True
    except Exception as exc:
        with _session_lock:
            _session = None
            _session_error = f"Failed to load rembg model '{REMBG_MODEL}': {exc}"
            _session_ready = False
        traceback.print_exc()


def _start_background_warmup():
    t = threading.Thread(target=_load_session, daemon=True)
    t.start()


_start_background_warmup()


def get_session():
    global _session
    with _session_lock:
        if _session_ready and _session is not None:
            return _session
    if _session_error:
        raise RuntimeError(_session_error)
    raise RuntimeError(
        "The AI model is still loading. Please try again in a moment."
    )


def _normalize_image(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    if max(image.width, image.height) > MAX_EDGE_PX:
        ratio = MAX_EDGE_PX / float(max(image.width, image.height))
        new_size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    return image


def _image_to_png_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    with _session_lock:
        return jsonify({
            "status": "ok",
            "rembg_installed": remove is not None,
            "model": REMBG_MODEL,
            "model_ready": _session_ready,
            "model_error": _session_error,
        })


@app.route("/remove-bg", methods=["POST"])
def remove_bg():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded."}), 400

        file = request.files["image"]
        if not file.filename:
            return jsonify({"error": "Please choose an image file."}), 400

        # size check
        file.seek(0, os.SEEK_END)
        size_bytes = file.tell()
        file.seek(0)

        if size_bytes > MAX_UPLOAD_MB * 1024 * 1024:
            return jsonify({"error": f"File too large. Maximum {MAX_UPLOAD_MB}MB."}), 400

        try:
            image = Image.open(file.stream)
            image = _normalize_image(image)
        except Exception as exc:
            return jsonify({"error": f"Invalid image file: {exc}"}), 400

        if remove is None:
            return jsonify({
                "error": "rembg is not installed on the server. Check requirements.txt and redeploy."
            }), 500

        try:
            session = get_session()
        except Exception as exc:
            return jsonify({"error": str(exc)}), 503

        try:
            png_bytes = _image_to_png_bytes(image)
            output = remove(png_bytes, session=session)
        except Exception as exc:
            traceback.print_exc()
            return jsonify({"error": f"Background removal failed: {exc}"}), 500

        if not output:
            return jsonify({"error": "No output was generated."}), 500

        return send_file(
            io.BytesIO(output),
            mimetype="image/png",
            as_attachment=True,
            download_name="no-background.png",
            max_age=0,
        )

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": f"Server error: {exc}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
