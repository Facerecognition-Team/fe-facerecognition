const capturedImage = document.getElementById('captured_image');
const imageModal = document.getElementById('imageModal');
const cancelButton = document.getElementById('cancel-button');
const confirmButton = document.getElementById('confirm-button');
let lastImageTimestamp = '';

// Fungsi untuk memperbarui dan menampilkan gambar yang diambil dalam modal
function updateCapturedImage(imagePath) {
    capturedImage.src = imagePath;
    imageModal.style.display = 'flex'; // Tampilkan modal sebagai flexbox
}

// Event listener untuk tombol batal
cancelButton.addEventListener('click', () => {
    imageModal.style.display = 'none'; // Sembunyikan modal jika batal
    resetLastCapturedImage(); // Reset gambar setelah modal ditutup
    setTimeout(resumeCapture, 5000); // Tunggu 5 detik sebelum melanjutkan pengambilan gambar
});

// Event listener untuk tombol konfirmasi
function dataURLToFile(dataURL, filename) {
    // Check if the dataURL contains the prefix "data:image"
    const regex = /^data:(image\/[a-zA-Z]*);base64,/;
    const match = dataURL.match(regex);

    if (!match) {
        throw new Error('Invalid data URL format');
    }

    const mime = match[1]; // Extract mime type
    const bstr = atob(dataURL.split(',')[1]); // Decode base64 string
    const n = bstr.length;
    const u8arr = new Uint8Array(n);

    // Convert base64 to binary data
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }

    return new File([u8arr], filename, { type: mime });
}

confirmButton.addEventListener('click', () => {
    imageModal.style.display = 'none'; // Sembunyikan modal
    resetLastCapturedImage(); // Reset gambar setelah modal ditutup

    const formData = new FormData();

    // Pastikan capturedImage.src memiliki URL yang valid
    console.log(capturedImage.src);

    fetch(capturedImage.src)
        .then(response => response.blob()) // Konversi ke Blob
        .then(blob => {
            const file = new File([blob], 'employee-photo.jpg', { type: blob.type });
            formData.append('employee-photo', file);

            // Kirim gambar ke Laravel Backend
            fetch('/proses_absen', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Absensi berhasil: ' + data.message);
                } else {
                    alert('Gagal: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Terjadi kesalahan saat mengunggah gambar.');
            });
        })
        .catch(error => {
            console.error('Error fetching image:', error);
            alert('Gagal mengambil gambar.');
        });

    alert('Lanjutkan ke proses berikutnya!');
});

// Fungsi untuk mereset gambar terakhir di server
function resetLastCapturedImage() {
    console.log("Resetting last captured image...");  // Debugging log untuk melihat apakah fungsi dipanggil
    fetch('/reset_last_image', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);  // Log pesan sukses dari server
    })
    .catch(error => console.error('Error resetting last captured image:', error));
}

// Fungsi untuk melanjutkan pengambilan gambar
function resumeCapture() {
    fetch('/resume_capture', { method: 'POST' });
}

// Fungsi untuk mengambil gambar terakhir yang diambil
function fetchLastCapturedImage() {
    fetch('/last_captured_image')
        .then(response => response.json())
        .then(data => {
            // Jika timestamp gambar terakhir berbeda dengan timestamp yang disimpan sebelumnya
            if (data.timestamp !== lastImageTimestamp && data.image_url) {
                lastImageTimestamp = data.timestamp; // Perbarui timestamp terakhir
                updateCapturedImage(data.image_url); // Tampilkan modal dengan gambar terbaru
            }
        })
        .catch(error => console.error('Error fetching last captured image:', error));
}

    

// document.getElementById('startt-camera').addEventListener('click', function() {
//     // Cek apakah browser mendukung akses ke kamera
//     if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
//         // Meminta akses ke kamera
//         navigator.mediaDevices.getUserMedia({ video: true })
//         .then(function(stream) {
//             // Set sumber video ke stream kamera
//             const video = document.getElementById('video');
//             video.srcObject = stream;
//             video.style.display = 'block'; // Menampilkan elemen video
//             document.getElementById('camera-container').style.display = 'block'; // Menampilkan kontainer kamera
//         })
//         .catch(function(err) {
//             console.error("Error accessing the camera:", err);
//             alert("Tidak dapat mengakses kamera. Pastikan kamera Anda terhubung dan izinkan browser untuk mengaksesnya.");
//         });
//     } else {
//         alert("Browser Anda tidak mendukung akses kamera.");
//     }
// });

// let video = document.getElementById('videoo');
// let canvas = document.getElementById('canvas');
// let captureButton = document.getElementById('capture-face');
// let startCameraButton = document.getElementById('startt-camera');
// let statusText = document.getElementById('status');
// let detectedFaces = 0;

// // Pastikan canvas sudah ada di halaman HTML
// let context = canvas.getContext('2d');

// // Start the camera
// startCameraButton.addEventListener('click', function() {
//     navigator.mediaDevices.getUserMedia({ video: true })
//     .then(stream => {
//         video.srcObject = stream;
//         document.getElementById('camera-container').style.display = 'block';
//         statusText.textContent = "Menunggu deteksi wajah...";
//         detectFaces();  // Panggil fungsi deteksi wajah
//     })
//     .catch(err => {
//         console.error("Error accessing the camera", err);
//         alert("Tidak dapat mengakses kamera.");
//     });
// });

// // Capture face image from video
// captureButton.addEventListener('click', function() {
//     if (detectedFaces < 50) {
//         captureFace();
//     } else {
//         alert('50 foto wajah sudah diambil.');
//     }
// });

// // Deteksi wajah dari aliran kamera
// function detectFaces() {
//     // Pastikan face-api.js sudah di-load dengan benar
//     const modelLoaded = () => {
//         statusText.textContent = "Model siap, mulai deteksi wajah...";

//         // Deteksi wajah setiap 100ms
//         setInterval(() => {
//             faceapi.detectAllFaces(video)
//             .withFaceLandmarks()
//             .withFaceDescriptors()
//             .then(detections => {
//                 if (detections.length > 0) {
//                     // Jika wajah terdeteksi, gambar kotak di sekitar wajah
//                     context.clearRect(0, 0, canvas.width, canvas.height); // Bersihkan canvas sebelumnya
//                     faceapi.draw.drawDetections(canvas, detections);
//                     faceapi.draw.drawFaceLandmarks(canvas, detections);
//                     faceapi.draw.drawFaceDescriptors(canvas, detections);
//                 }
//             });
//         }, 100);  // Deteksi wajah setiap 100ms
//     };

//     // Load model face-api.js
//     faceapi.nets.ssdMobilenetv1.loadFromUri('/models').then(modelLoaded);  // Load face-api model dari folder '/models'
// }

// // Capture the face and send to backend
// function captureFace() {
//     // Set canvas width dan height sesuai dengan ukuran video
//     canvas.width = video.videoWidth;
//     canvas.height = video.videoHeight;

//     // Gambar video ke canvas
//     context.drawImage(video, 0, 0, canvas.width, canvas.height);

//     // Ambil data dari canvas dan konversi ke base64
//     let imageData = canvas.toDataURL('image/jpeg');  // Mengubah gambar menjadi format base64

//     // Kirim gambar wajah ke backend
//     fetch('http://localhost:8000/api/upload_face', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({
//             employee_name: document.getElementById('employee-name').value,
//             face_image: imageData,  // Gambar dalam format base64
//         })
//     })
//     .then(response => response.json())
//     .then(data => {
//         if (data.success) {
//             detectedFaces += 1;
//             alert('Wajah berhasil ditangkap! (' + detectedFaces + '/50)');
//         } else {
//             alert(data.message);
//         }
//     })
//     .catch(error => {
//         console.error('Error:', error);
//         alert('Terjadi kesalahan saat mengambil foto.');
//     });
// }

// Mengatur interval untuk memeriksa gambar terakhir setiap 2,5 detik
setInterval(fetchLastCapturedImage, 2500); // Cek setiap 2,5 detik
