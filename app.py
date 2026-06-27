from __future__ import annotations

import base64
import io
import os
import traceback
from typing import Tuple

from flask import Flask, jsonify, render_template_string, request, send_file
from flask_cors import CORS
from PIL import Image, ImageOps

# rembg is required at runtime. If it is missing, the app will still start
# and show a helpful error from the /remove-bg endpoint.
try:
    from rembg import remove, new_session
except Exception:  # pragma: no cover
    remove = None
    new_session = None


app = Flask(__name__)
CORS(app)

MAX_UPLOAD_MB = 10
MAX_EDGE_PX = 2000
DEFAULT_MODEL = os.environ.get("REMBG_MODEL", "u2net")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Background Remover</title>
    <style>
        :root {
            --bg1: #667eea;
            --bg2: #764ba2;
            --card: #ffffff;
            --text: #1f2937;
            --muted: #6b7280;
            --danger: #b91c1c;
            --danger-bg: #fef2f2;
            --success: #166534;
            --success-bg: #f0fdf4;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            font-family: Arial, Helvetica, sans-serif;
            background: linear-gradient(135deg, var(--bg1), var(--bg2));
            display: grid;
            place-items: center;
            padding: 20px;
            color: var(--text);
        }
        .container {
            width: min(920px, 100%);
            background: var(--card);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,.28);
            padding: 28px;
        }
        h1 { margin: 0 0 8px; text-align: center; }
        p.subtitle { margin: 0 0 24px; text-align: center; color: var(--muted); }
        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
        }
        .upload-area {
            border: 2px dashed #9ca3af;
            border-radius: 18px;
            padding: 28px;
            text-align: center;
            cursor: pointer;
            transition: .2s ease;
            background: #fafafa;
        }
        .upload-area:hover, .upload-area.dragover {
            border-color: var(--bg1);
            background: #f7f7ff;
            transform: translateY(-1px);
        }
        input[type=file] { display:none; }
        .actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        button, .button {
            appearance: none;
            border: 0;
            border-radius: 12px;
            padding: 12px 16px;
            font-weight: 700;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .primary { background: linear-gradient(135deg, var(--bg1), var(--bg2)); color: #fff; }
        .secondary { background: #e5e7eb; color: #111827; }
        .hidden { display:none; }
        .message {
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 16px;
            display: none;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .error { background: var(--danger-bg); color: var(--danger); }
        .success { background: var(--success-bg); color: var(--success); }
        .loading { text-align:center; display:none; padding: 12px 0; color: var(--muted); }
        .spinner {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            border: 3px solid #e5e7eb;
            border-top-color: var(--bg1);
            margin: 0 auto 10px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .preview {
            display:none;
            gap: 16px;
            margin-top: 8px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .panel {
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            overflow: hidden;
            background: #fff;
        }
        .panel h3 {
            margin: 0;
            padding: 12px 14px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 14px;
            color: #374151;
        }
        .panel img {
            width: 100%;
            display: block;
            background: repeating-conic-gradient(#f3f4f6 0% 25%, #ffffff 0% 50%) 50% / 18px 18px;
        }
        .footer {
            margin-top: 14px;
            font-size: 12px;
            color: var(--muted);
            text-align: center;
        }
        @media (max-width: 700px) {
            .preview { grid-template-columns: 1fr; }
            .container { padding: 18px; border-radius: 18px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Background Remover</h1>
        <p class="subtitle">Upload an image and get a PNG with transparent background.</p>

        <div id="error" class="message error"></div>
        <div id="success" class="message success"></div>

        <div id="uploadArea" class="upload-area">
            <div style="font-size:42px;">📁</div>
            <div style="font-size:18px;font-weight:700;margin-top:6px;">Tap to upload or drag & drop</div>
            <div style="margin-top:6px;color:#6b7280;">JPG, PNG, WEBP, BMP, GIF up to 10MB</div>
            <input id="fileInput" type="file" accept="image/*">
        </div>

        <div id="loading" class="loading">
            <div class="spinner"></div>
            Processing your image...
        </div>

        <div id="preview" class="preview">
            <div class="panel">
                <h3>Original</h3>
                <img id="originalImg" alt="Original image">
            </div>
            <div class="panel">
                <h3>Result</h3>
                <img id="resultImg" alt="Background removed result">
            </div>
        </div>

        <div class="actions" style="margin-top:16px;">
            <button id="downloadBtn" class="button primary hidden">Download PNG</button>
            <button id="resetBtn" class="button secondary hidden">Upload Another</button>
        </div>

        <div class="footer">
            Server health: <a href="/health" target="_blank">/health</a>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const errorBox = document.getElementById('error');
        const successBox = document.getElementById('success');
        const loading = document.getElementById('loading');
        const preview = document.getElementById('preview');
        const originalImg = document.getElementById('originalImg');
        const resultImg = document.getElementById('resultImg');
        const downloadBtn = document.getElementById('downloadBtn');
        const resetBtn = document.getElementById('resetBtn');

        let resultObjectUrl = null;
        let currentFileName = 'no-background.png';

        function showError(message) {
            successBox.style.display = 'none';
            errorBox.textContent = message;
            errorBox.style.display = 'block';
        }

        function showSuccess(message) {
            errorBox.style.display = 'none';
            successBox.textContent = message;
            successBox.style.display = 'block';
        }

        function clearMessages() {
            errorBox.style.display = 'none';
            successBox.style.display = 'none';
        }

        function cleanupResultUrl() {
            if (resultObjectUrl) {
                URL.revokeObjectURL(resultObjectUrl);
                resultObjectUrl = null;
            }
        }

        uploadArea.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files && e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFile();
            }
        });

        fileInput.addEventListener('change', handleFile);

        resetBtn.addEventListener('click', () => location.reload());

        downloadBtn.addEventListener('click', () => {
            if (!resultObjectUrl) return;
            const a = document.createElement('a');
            a.href = resultObjectUrl;
            a.download = currentFileName;
            document.body.appendChild(a);
            a.click();
            a.remove();
        });

        async function handleFile() {
            clearMessages();
            cleanupResultUrl();

            const file = fileInput.files[0];
            if (!file) return;

            if (!file.type.startsWith('image/')) {
                showError('Please upload an image file.');
                return;
            }

            if (file.size > 10 * 1024 * 1024) {
                showError('File too large. Maximum 10MB.');
                return;
            }

            currentFileName = 'no-background.png';

            const reader = new FileReader();
            reader.onload = () => {
                originalImg.src = reader.result;
                preview.style.display = 'grid';
            };
            reader.readAsDataURL(file);

            loading.style.display = 'block';
            downloadBtn.classList.add('hidden');
            resetBtn.classList.add('hidden');

            try {
                const formData = new FormData();
                formData.append('image', file);

                const response = await fetch('/remove-bg', {
                    method: 'POST',
                    body: formData
                });

                const contentType = response.headers.get('content-type') || '';

                if (!response.ok) {
                    let detail = 'Unknown error';
                    if (contentType.includes('application/json')) {
                        const data = await response.json();
                        detail = data.error || JSON.stringify(data);
                    } else {
                        detail = await response.text();
                    }
                    throw new Error(detail);
                }

                if (!contentType.includes('image/')) {
                    throw new Error('Server did not return an image.');
                }

                const blob = await response.blob();
                resultObjectUrl = URL.createObjectURL(blob);
                resultImg.src = resultObjectUrl;

                showSuccess('Background removed successfully.');
                downloadBtn.classList.remove('hidden');
                resetBtn.classList.remove('hidden');
            } catch (err) {
                showError('Error: ' + err.message);
                preview.style.display = 'none';
            } finally {
                loading.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""


def load_rembg_session():
    if remove is None:
        raise RuntimeError(
            "rembg is not installed. Add 'rembg' and 'onnxruntime' to requirements.txt and redeploy."
        )
    # Session is created once for performance; model name can be changed via env var.
    return new_session(DEFAULT_MODEL)


SESSION = None


def get_session():
    global SESSION
    if SESSION is None:
        SESSION = load_rembg_session()
    return SESSION


def normalize_image(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")
    if image.width > MAX_EDGE_PX or image.height > MAX_EDGE_PX:
        ratio = MAX_EDGE_PX / max(image.width, image.height)
        new_size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    return image


def image_to_png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "rembg_loaded": remove is not None, "model": DEFAULT_MODEL})


@app.route("/remove-bg", methods=["POST"])
def remove_background():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image provided."}), 400

        file = request.files["image"]
        if not file.filename:
            return jsonify({"error": "No file selected."}), 400

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if size > MAX_UPLOAD_MB * 1024 * 1024:
            return jsonify({"error": f"File too large. Max {MAX_UPLOAD_MB}MB."}), 400

        try:
            image = Image.open(file.stream)
            image = normalize_image(image)
        except Exception as exc:
            return jsonify({"error": f"Invalid image: {exc}"}), 400

        original_png = image_to_png_bytes(image)

        if remove is None:
            return jsonify({
                "error": "rembg is not installed on the server. Update requirements.txt with rembg and onnxruntime, then redeploy."
            }), 500

        try:
            session = get_session()
            output = remove(original_png, session=session)
        except Exception as exc:
            traceback.print_exc()
            return jsonify({
                "error": f"Background removal failed: {exc}"
            }), 500

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
