const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const message = document.getElementById('message');
const loadingBox = document.getElementById('loadingBox');
const preview = document.getElementById('preview');
const originalImg = document.getElementById('originalImg');
const resultImg = document.getElementById('resultImg');
const downloadBtn = document.getElementById('downloadBtn');
const resetBtn = document.getElementById('resetBtn');
const serverStatus = document.getElementById('serverStatus');
const modelStatus = document.getElementById('modelStatus');

let resultUrl = null;
let currentFileName = 'no-background.png';

function setMessage(text, type) {
  message.className = `message ${type}`;
  message.textContent = text;
  message.classList.remove('hidden');
}

function hideMessage() {
  message.className = 'message hidden';
  message.textContent = '';
}

function setPill(el, text, cls) {
  el.textContent = text;
  el.className = `pill ${cls}`;
}

function revokeResultUrl() {
  if (resultUrl) {
    URL.revokeObjectURL(resultUrl);
    resultUrl = null;
  }
}

function showLoading(show) {
  loadingBox.classList.toggle('hidden', !show);
}

function resetView() {
  hideMessage();
  revokeResultUrl();
  preview.classList.add('hidden');
  downloadBtn.classList.add('hidden');
  resetBtn.classList.add('hidden');
  showLoading(false);
}

async function refreshHealth() {
  try {
    const res = await fetch('/health', { cache: 'no-store' });
    const data = await res.json();

    setPill(serverStatus, 'Server is live', 'ok');

    if (data.model_ready) {
      setPill(modelStatus, `Model ready: ${data.model}`, 'ok');
      return true;
    }

    if (data.model_error) {
      setPill(modelStatus, 'Model load error', 'bad');
      return false;
    }

    setPill(modelStatus, `Loading model: ${data.model}`, 'loading');
    return false;
  } catch (err) {
    setPill(serverStatus, 'Server check failed', 'bad');
    setPill(modelStatus, 'Model status unavailable', 'bad');
    return false;
  }
}

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', async (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files && e.dataTransfer.files.length) {
    fileInput.files = e.dataTransfer.files;
    await processFile();
  }
});

fileInput.addEventListener('change', processFile);

resetBtn.addEventListener('click', () => location.reload());

downloadBtn.addEventListener('click', () => {
  if (!resultUrl) return;
  const a = document.createElement('a');
  a.href = resultUrl;
  a.download = currentFileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
});

async function processFile() {
  resetView();
  const file = fileInput.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    setMessage('Please upload an image file.', 'error');
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    setMessage('File too large. Maximum size is 10MB.', 'error');
    return;
  }

  currentFileName = 'no-background.png';

  const reader = new FileReader();
  reader.onload = () => {
    originalImg.src = reader.result;
    preview.classList.remove('hidden');
  };
  reader.readAsDataURL(file);

  showLoading(true);

  try {
    const formData = new FormData();
    formData.append('image', file);

    const res = await fetch('/remove-bg', {
      method: 'POST',
      body: formData
    });

    const contentType = res.headers.get('content-type') || '';

    if (!res.ok) {
      let detail = 'Unknown error';
      if (contentType.includes('application/json')) {
        const data = await res.json();
        detail = data.error || JSON.stringify(data);
      } else {
        detail = await res.text();
      }
      throw new Error(detail);
    }

    if (!contentType.includes('image/')) {
      throw new Error('Server did not return an image.');
    }

    const blob = await res.blob();
    revokeResultUrl();
    resultUrl = URL.createObjectURL(blob);
    resultImg.src = resultUrl;

    setMessage('Background removed successfully.', 'success');
    downloadBtn.classList.remove('hidden');
    resetBtn.classList.remove('hidden');
  } catch (err) {
    setMessage(`Error: ${err.message}`, 'error');
    preview.classList.add('hidden');
  } finally {
    showLoading(false);
  }
}

refreshHealth();
setInterval(refreshHealth, 8000);
