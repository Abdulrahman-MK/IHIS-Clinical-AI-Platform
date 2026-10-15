document.getElementById('xrayForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const fileInput = document.getElementById('xrayInput');
    const submitBtn = document.getElementById('submitBtn');
    const viewport = document.getElementById('viewportContainer');
    const originalImg = document.getElementById('originalImage');
    const maskImg = document.getElementById('maskOverlay');

    if (!fileInput.files.length) return;

    // Render client preview of original image
    const file = fileInput.files[0];
    originalImg.src = URL.createObjectURL(file);
    
    const formData = new FormData();
    formData.append('xray', file);

    submitBtn.disabled = true;
    submitBtn.innerText = 'Processing...';

    try {
        const response = await fetch('/dental/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            maskImg.src = `data:image/png;base64,${data.mask}`;
            viewport.style.display = 'inline-block';
        } else {
            alert('Analysis Error: ' + (data.error || 'Failed to process image'));
        }
    } catch (err) {
        alert('Network or Server Error: ' + err.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Run AI Analysis';
    }
});