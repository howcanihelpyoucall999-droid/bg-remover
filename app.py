from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
import os
import sys
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Try to import rembg - handle if not available
try:
    from rembg import remove
    from PIL import Image
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    print("WARNING: rembg not installed. Install with: pip install rembg")

@app.route('/')
def home():
    """Serve main page"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "index.html not found", 404

@app.route('/how-it-works')
def how_it_works():
    """Serve how-it-works page"""
    try:
        with open('how-it-works.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "how-it-works.html not found", 404

@app.route('/remove-bg', methods=['POST'])
def remove_background():
    """Remove background from uploaded image"""
    try:
        if not REMBG_AVAILABLE:
            return jsonify({'error': 'rembg library not available. Please install dependencies.'}), 500
        
        # Check if image is in request
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file size (max 10MB for Vercel)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:
            return jsonify({'error': 'File too large. Max 10MB'}), 400
        
        # Read image
        try:
            input_image = Image.open(file.stream)
            # Resize if too large (for performance)
            max_dimension = 2000
            if input_image.width > max_dimension or input_image.height > max_dimension:
                ratio = max_dimension / max(input_image.width, input_image.height)
                new_size = (int(input_image.width * ratio), int(input_image.height * ratio))
                input_image = input_image.resize(new_size, Image.Resampling.LANCZOS)
        except Exception as e:
            return jsonify({'error': f'Invalid image file: {str(e)}'}), 400
        
        # Remove background
        try:
            output_image = remove(input_image)
        except Exception as e:
            return jsonify({'error': f'Failed to process image: {str(e)}'}), 500
        
        # Save to bytes
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='no-bg.png')
    
    except Exception as e:
        print(f"Error in remove_background: {str(e)}", file=sys.stderr)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'rembg_available': REMBG_AVAILABLE
    })

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'message': 'Background Remover API is running',
        'endpoints': {
            'GET /': 'Main page',
            'GET /how-it-works': 'How it works page',
            'POST /remove-bg': 'Remove background from image',
            'GET /health': 'Health check',
            'GET /test': 'This endpoint'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
