from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS
import io
import os
import requests
from PIL import Image
import base64

app = Flask(__name__)
CORS(app)

# Simple HTML interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Background Remover</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 40px; max-width: 600px; width: 100%; }
        h1 { text-align: center; color: #333; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }
        .upload-area { border: 2px dashed #667eea; border-radius: 10px; padding: 40px 20px; text-align: center; cursor: pointer; transition: all 0.3s; margin-bottom: 20px; }
        .upload-area:hover { border-color: #764ba2; background: #f8f9ff; }
        .upload-area.dragover { border-color: #764ba2; background: #f0f0ff; }
        input[type="file"] { display: none; }
        .upload-icon { font-size: 48px; margin-bottom: 10px; }
        .upload-text { color: #333; margin-bottom: 5px; }
        .upload-hint { color: #999; font-size: 12px; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 20px; transition: transform 0.2s; }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .preview { display: none; margin-top: 30px; }
        .preview-title { font-weight: bold; color: #333; margin-bottom: 10px; }
        .preview-images { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .image-container { border-radius: 10px; overflow: hidden; background: #f0f0f0; }
        .image-container img { width: 100%; height: auto; display: block; }
        .download-btn { background: #4CAF50; margin-top: 10px; }
        .download-btn:hover { background: #45a049; }
        .error { color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: none; }
        .success { color: #388e3c; background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: none; }
        .loading { display: none; text-align: center; color: #667eea; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Background Remover</h1>
        <p class="subtitle">Upload an image and we'll remove the background instantly</p>
        
        <div class="error" id="error-msg"></div>
        <div class="success" id="success-msg"></div>
        
        <div class="upload-area" id="upload-area">
            <div class="upload-icon">📁</div>
            <div class="upload-text">Click to upload or drag & drop</div>
            <div class="upload-hint">PNG, JPG, GIF up to 10MB</div>
            <input type="file" id="file-input" accept="image/*">
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Processing your image...</p>
        </div>
        
        <div class="preview" id="preview">
            <div class="preview-title">Original vs Result</div>
            <div class="preview-images">
                <div>
                    <p style="font-size: 12px; color: #666; margin-bottom: 5px;">Original</p>
                    <div class="image-container">
                        <img id="original-img" src="" alt="Original">
                    </div>
                </div>
                <div>
                    <p style="font-size: 12px; color: #666; margin-bottom: 5px;">No Background</p>
                    <div class="image-container">
                        <img id="result-img" src="" alt="Result">
                    </div>
                </div>
            </div>
            <button class="download-btn" id="download-btn">⬇️ Download Result</button>
            <button style="background: #999; margin-top: 10px;" onclick="location.reload()">Upload Another</button>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        const preview = document.getElementById('preview');
        const loading = document.getElementById('loading');
        const errorMsg = document.getElementById('error-msg');
        const successMsg = document.getElementById('success-msg');
        const downloadBtn = document.getElementById('download-btn');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            fileInput.files = e.dataTransfer.files;
            handleFile();
        });
        
        fileInput.addEventListener('change', handleFile);
        
        function handleFile() {
            const file = fileInput.files[0];
            if (!file) return;
            
            errorMsg.style.display = 'none';
            successMsg.style.display = 'none';
            
            if (!file.type.startsWith('image/')) {
                showError('Please upload an image file');
                return;
            }
            
            if (file.size > 10 * 1024 * 1024) {
                showError('File is too large. Max 10MB');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('original-img').src = e.target.result;
                processImage(file);
            };
            reader.readAsDataURL(file);
        }
        
        function processImage(file) {
            loading.style.display = 'block';
            preview.style.display = 'none';
            
            const formData = new FormData();
            formData.append('image', file);
            
            fetch('/remove-bg', {
                method: 'POST',
                body: formData
            })
            .then(res => res.blob())
            .then(blob => {
                loading.style.display = 'none';
                const url = URL.createObjectURL(blob);
                document.getElementById('result-img').src = url;
                preview.style.display = 'block';
                successMsg.style.display = 'block';
                successMsg.textContent = '✓ Background removed successfully!';
                downloadBtn.onclick = () => downloadImage(url);
            })
            .catch(err => {
                loading.style.display = 'none';
                showError('Error processing image: ' + err.message);
            });
        }
        
        function downloadImage(url) {
            const a = document.createElement('a');
            a.href = url;
            a.download = 'no-background.png';
            a.click();
        }
        
        function showError(msg) {
            errorMsg.textContent = '✗ ' + msg;
            errorMsg.style.display = 'block';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/remove-bg', methods=['POST'])
def remove_background():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:
            return jsonify({'error': 'File too large'}), 400
        
        # Read image
        try:
            image = Image.open(file.stream)
            if image.format not in ['JPEG', 'PNG', 'GIF', 'BMP']:
                return jsonify({'error': 'Invalid image format'}), 400
        except Exception as e:
            return jsonify({'error': f'Invalid image: {str(e)}'}), 400
        
        # Resize if too large
        max_size = 2000
        if image.width > max_size or image.height > max_size:
            ratio = max_size / max(image.width, image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Use Clipdrop API (free)
        try:
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Try Clipdrop API first (free, works great)
            response = requests.post(
                'https://clipdrop-api.co/remove-background/v1',
                files={'image_file': img_bytes},
                headers={'x-api-key': 'free'},
                timeout=30
            )
            
            if response.status_code == 200:
                return send_file(
                    io.BytesIO(response.content),
                    mimetype='image/png',
                    as_attachment=True,
                    download_name='no-background.png'
                )
            
            # If Clipdrop fails, use deepai (alternative)
            response = requests.post(
                'https://api.deepai.org/api/remove-background',
                files={'image': img_bytes},
                headers={'api-key': 'quickstart-QUickstart'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'output_url' in result:
                    img_response = requests.get(result['output_url'])
                    return send_file(
                        io.BytesIO(img_response.content),
                        mimetype='image/png',
                        as_attachment=True,
                        download_name='no-background.png'
                    )
            
            return jsonify({'error': 'Processing failed. Please try again.'}), 500
        
        except Exception as e:
            return jsonify({'error': f'Processing error: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
