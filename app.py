from flask import Flask, render_template, Response, jsonify, send_file, request
import cv2
import os
import time
import pygame
from datetime import datetime, timedelta
import base64
import numpy as np

app = Flask(__name__)

# Menggunakan OpenCV untuk mendeteksi wajah
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Folder untuk menyimpan gambar
if not os.path.exists('detected_faces'):
    os.makedirs('detected_faces')

# Inisialisasi pygame mixer
pygame.mixer.init()
mp3_path = os.path.join(app.static_folder, 'audio', 'camera_shutter.mp3')
camera_sound = pygame.mixer.Sound(mp3_path)

last_captured_image = {'timestamp': '', 'image_url': ''}
next_save_time = datetime.now()

def save_detected_face(frame):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"face_{timestamp}.jpg"
    image_path = os.path.join('detected_faces', filename)  # Simpan di dalam folder detected_faces
    cv2.imwrite(image_path, frame)
    
    global last_captured_image
    last_captured_image = {'timestamp': timestamp, 'image_url': f'/show_image/{filename}'}
    
    return image_path

def detect_faces():
    cap = cv2.VideoCapture(0)
    global next_save_time

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Camera not accessible!")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Selalu lakukan deteksi wajah
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Hanya simpan gambar jika sudah melewati waktu yang ditentukan
                if datetime.now() >= next_save_time:
                    face = frame[y:y+h, x:x+w]
                    image_path = save_detected_face(face)  # Simpan gambar wajah yang terdeteksi
                    print(f"Saved face image: {image_path}")

                    # Mainkan suara hanya setelah gambar disimpan
                    camera_sound.play()

                    # Atur waktu berikutnya untuk menyimpan gambar
                    next_save_time = datetime.now() + timedelta(minutes=1)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(detect_faces(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/show_image/<filename>')
def show_image(filename):
    file_path = os.path.join('detected_faces', filename)
    
    # Pastikan file ada sebelum mengirimkannya
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, mimetype='image/jpeg')

@app.route('/last_captured_image')
def get_last_captured_image():
    return jsonify(last_captured_image)

@app.route('/resume_capture', methods=['POST'])
def resume_capture():
    global next_save_time
    next_save_time = datetime.now()  # Reset waktu untuk mengaktifkan pengambilan gambar lagi
    return '', 204  # Kembali dengan status HTTP 204 (No Content)

@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        # Ambil gambar dari permintaan
        if 'image' not in request.files:
            return jsonify({'error': 'No image part in the request'}), 400

        file = request.files['image']

        # Baca file gambar
        image = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        if image is None or image.size == 0:
            return jsonify({'error': 'Invalid image data'}), 400

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        response = {
            'faces_detected': len(faces),
            'faces': []
        }

        for (x, y, w, h) in faces:
            response['faces'].append({
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h)
            })

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
