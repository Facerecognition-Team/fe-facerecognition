const capturedImage = document.getElementById('captured_image');
const imageModal = document.getElementById('imageModal');
const cancelButton = document.getElementById('cancel-button');
const confirmButton = document.getElementById('confirm-button');
let lastImageTimestamp = '';

function updateCapturedImage(imagePath) {
    capturedImage.src = imagePath;
    imageModal.style.display = 'flex'; // Tampilkan modal sebagai flexbox
}

cancelButton.addEventListener('click', () => {
    imageModal.style.display = 'none'; // Sembunyikan modal jika batal
    setTimeout(resumeCapture, 5000); // Tunggu 5 detik sebelum melanjutkan pengambilan gambar
});

confirmButton.addEventListener('click', () => {
    imageModal.style.display = 'none'; // Sembunyikan modal dan lakukan aksi lanjutkan
    alert('Lanjutkan ke proses berikutnya!');
});

function resumeCapture() {
    fetch('/resume_capture', { method: 'POST' });
}

function fetchLastCapturedImage() {
    fetch('/last_captured_image')
        .then(response => response.json())
        .then(data => {
            if (data.timestamp !== lastImageTimestamp) {
                lastImageTimestamp = data.timestamp;
                updateCapturedImage(data.image_url);
            }
        });
}

setInterval(fetchLastCapturedImage, 2500); // Cek setiap 2,5 detik