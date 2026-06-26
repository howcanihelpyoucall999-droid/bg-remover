# 🎨 Background Remover

An AI-powered web application to remove backgrounds from images instantly using rembg and Flask.

## Features

✅ **AI-Powered Background Removal** - Uses deep learning model via rembg  
✅ **Drag & Drop Upload** - Easy-to-use interface  
✅ **Side-by-Side Preview** - See before and after  
✅ **Download as PNG** - Transparent background support  
✅ **Mobile Responsive** - Works on phone and desktop  
✅ **One-Click Vercel Deploy** - Deploy in seconds  
✅ **How It Works Page** - Learn the technology  

## Tech Stack

- **Backend**: Flask, rembg, Pillow (PIL)
- **Frontend**: HTML, CSS, JavaScript
- **AI Model**: PyTorch-based U-Net
- **Deployment**: Vercel (Serverless)

## Local Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/howcanihelpyoucall999-droid/bg-remover.git
   cd bg-remover
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

## Deploy to Vercel (From Your Phone! 📱)

### Method: Using Vercel Web UI (Easiest for Phone Users)

1. Go to **[vercel.com](https://vercel.com)** on your phone
2. Sign in with your GitHub account
3. Click **"Add New" → "Project"**
4. Select this repository: **`bg-remover`**
5. Click **"Deploy"**
6. Wait 2-3 minutes for deployment to complete
7. Your app will be live! 🚀

**That's it! Your background remover is now live on the internet!**

## How It Works

1. **Upload Image** → You select an image from your device
2. **Send to Server** → Image is sent to the Flask backend
3. **AI Processing** → rembg analyzes and removes background using deep learning
4. **Convert to PNG** → Result is converted to PNG with transparency
5. **Download** → You download the transparent PNG file

**For detailed explanation, visit the "How It Works" page in the app!**

## API Endpoints

### POST `/remove-bg`
Removes background from an uploaded image

**Request:**
```
Content-Type: multipart/form-data
Body: image file
```

**Response:**
```
Content-Type: image/png
Body: PNG file with transparent background
```

### GET `/`
Serves the main application page

### GET `/how-it-works`
Serves the technical explanation page

### GET `/health`
Health check endpoint

## Usage

1. **Upload**: Click or drag-drop an image
2. **Wait**: AI processes the image (5-10 seconds)
3. **Preview**: See original and result side-by-side
4. **Download**: Click "Download Result" button
5. **Use**: Use the transparent PNG wherever you need!

## File Structure

```
bg-remover/
├── app.py              # Flask backend
├── index.html          # Main app interface
├── how-it-works.html   # Technical explanation
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel configuration
└── README.md          # This file
```

## Browser Support

- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers

## Limitations

- Max file size: 50MB
- Processing time: 5-15 seconds depending on image size
- Best results for images with clear subject/background distinction

## Troubleshooting

### Image processing takes too long
- Large images (4000+ px) may take 15-20 seconds
- The first request may be slower (model loading)

### "No image provided" error
- Make sure you selected an image file
- Check file format (JPG, PNG, WebP supported)

### Vercel deployment fails
- Check that all files are in the repository
- Ensure `requirements.txt` is in the root directory
- Check Vercel logs for specific errors

## Performance Tips

1. **Resize large images** - Smaller images process faster
2. **Use PNG format** - Better compression than JPEG
3. **Clear cache** - Browser cache may slow things down
4. **Close other tabs** - More resources for processing

## License

MIT License - Feel free to use for personal or commercial projects

## Contributing

Contributions welcome! Feel free to submit issues or pull requests.

## Author

Created by @howcanihelpyoucall999-droid

---

**Deploy Now on Vercel!** → Just visit [vercel.com](https://vercel.com) and connect this repository
