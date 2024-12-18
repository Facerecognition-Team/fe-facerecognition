from flask import Flask, render_template, Response, jsonify, send_file, request, redirect, url_for, session, flash, send_from_directory
import cv2
import os
import time
import pygame
from datetime import datetime, timedelta
import numpy as np
import requests  # Pastikan untuk mengimpor requests untuk mengirim data ke Laravel

app = Flask(__name__)
app.secret_key = 'my-very-secure-and-secret-key' 


# Muat model deteksi wajah
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Direktori untuk menyimpan gambar
if not os.path.exists('detected_faces'):
    os.makedirs('detected_faces')

# Inisialisasi pygame mixer
pygame.mixer.init()
mp3_path = os.path.join(app.static_folder, 'audio', 'camera_shutter.mp3')
camera_sound = pygame.mixer.Sound(mp3_path)

# Menyimpan detail gambar terakhir yang ditangkap
last_captured_image = {'timestamp': '', 'image_url': ''}
next_save_time = datetime.now()

# Direktori untuk menyimpan data pegawai
if not os.path.exists('employees'):
    os.makedirs('employees')

def save_detected_face(frame):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"face_{timestamp}.jpg"
    image_path = os.path.join('detected_faces', filename)  # Simpan di folder detected_faces
    cv2.imwrite(image_path, frame)  # Simpan gambar ke disk
    
    global last_captured_image
    last_captured_image = {'timestamp': timestamp, 'image_url': f'/show_image/{filename}'}
    
    return image_path

def detect_faces():
    cap = cv2.VideoCapture(0)  # Membuka akses ke kamera
    global next_save_time

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Camera not accessible!")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Konversi gambar ke grayscale untuk deteksi wajah
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Lakukan deteksi wajah
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Tambahkan kotak di sekitar wajah

                # Simpan gambar jika waktu berikutnya sudah lewat
                if datetime.now() >= next_save_time:
                    face = frame[y:y+h, x:x+w]  # Ekstrak wajah dari frame
                    image_path = save_detected_face(face)  # Simpan gambar wajah
                    print(f"Saved face image: {image_path}")
                    camera_sound.play()  # Mainkan suara kamera
                    next_save_time = datetime.now() + timedelta(seconds=5)  # Set waktu berikutnya (5 detik)

        # Encode frame sebagai JPEG untuk ditampilkan di browser
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()  # Tutup akses kamera
    



@app.route('/haarcascade_frontalface_default.xml')
def serve_cascade():
    return send_from_directory('static/models', 'haarcascade_frontalface_default.xml')


@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Ambil username dan password dari form
        username = request.form['username']
        password = request.form['password']
        
        # Validasi input
        if not username or not password:
            flash('Username dan password wajib diisi!', 'danger')
            return redirect(url_for('login'))

        try:
            # Kirim POST request ke Laravel API untuk verifikasi login
            response = requests.post('http://localhost:8000/api/admin/login', json={
                'username': username,
                'password': password
            })
            
            # Parsing response dari API
            data = response.json()

            # Periksa status dari API Laravel
            if data.get('success'):
                # Jika login berhasil, simpan session admin dan token
                session['admin_logged_in'] = True
                session['admin_token'] = data.get('token')
                session['admin_data'] = data.get('datauser')

                # Beri notifikasi login berhasil
                flash('Login berhasil!', 'success')

                # Redirect ke dashboard admin
                return redirect(url_for('admin_dashboard'))
            else:
                # Jika login gagal, tampilkan pesan error yang dikirimkan dari API
                flash(data.get('message', 'Login gagal'), 'danger')

        except Exception as e:
            flash(f'Terjadi kesalahan: {str(e)}', 'danger')
            return redirect(url_for('login'))
    
    return render_template('admin/login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Anda harus login terlebih dahulu!', 'danger')
        return redirect(url_for('login'))
    
    return render_template('admin/dashboard.html', admin_data=session.get('admin_data'))

# Route untuk logout admin
@app.route('/admin/logout')
def admin_logout():
    token = session.get('admin_token')

    if token:
        print(f"Token: {token}")  # Debugging token
        try:
            response = requests.post(
                'http://localhost:8000/api/admin/logout',
                headers={'Authorization': f'Bearer {token}'}
            )
            print(f"Response: {response.status_code}, {response.text}")  # Debug respons

            data = response.json()
            if response.status_code == 200 and data.get('success'):
                flash('Logout berhasil.', 'success')
            else:
                flash(data.get('message', 'Logout gagal.'), 'danger')

        except Exception as e:
            flash(f'Terjadi kesalahan saat logout: {str(e)}', 'danger')
    else:
        flash('Token tidak ditemukan di sesi.', 'danger')

    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(detect_faces(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/show_image/<filename>')
def show_image(filename):
    file_path = os.path.join('detected_faces', filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File tidak ditemukan'}), 404
    return send_file(file_path, mimetype='image/jpeg')

@app.route('/last_captured_image')
def get_last_captured_image():
    return jsonify(last_captured_image)  # Kembalikan data gambar terakhir dalam bentuk JSON

@app.route('/reset_last_image', methods=['POST'])
def reset_last_image():
    global last_captured_image
    last_captured_image = {'timestamp': '', 'image_url': ''}
    return jsonify({'message': 'Last captured image reset successfully.'}), 200

@app.route('/resume_capture', methods=['POST'])
def resume_capture():
    global next_save_time
    next_save_time = datetime.now()  # Reset waktu untuk pengambilan gambar berikutnya
    return '', 204  # HTTP No Content

@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Tidak ada bagian gambar dalam permintaan'}), 400

        file = request.files['image']
        image = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        if image is None or image.size == 0:
            return jsonify({'error': 'Data gambar tidak valid'}), 400

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        response = {
            'faces_detected': len(faces),
            'faces': [{'x': int(x), 'y': int(y), 'width': int(w), 'height': int(h)} for (x, y, w, h) in faces]
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload_employee', methods=['POST'])
def upload_employee():
    try:
        if 'employee-name' not in request.form or 'employee-photo' not in request.files:
            return jsonify({'success': False, 'message': 'Data pegawai tidak lengkap'}), 400

        employee_name = request.form['employee-name']
        employee_photo = request.files['employee-photo']

        if employee_photo.filename == '':
            return jsonify({'success': False, 'message': 'Tidak ada foto yang dipilih'}), 400

        # Simpan foto pegawai
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        photo_filename = f"{employee_name.replace(' ', '_')}_{timestamp}.jpg"
        photo_path = os.path.join('employees', photo_filename)
        employee_photo.save(photo_path)

        # Kirim data pegawai ke backend Laravel
        laravel_api_url = 'http://localhost:8000/api/upload_employee'  # Ganti dengan URL yang sesuai
        response = requests.post(laravel_api_url, json={
            'name': employee_name,
            'foto': photo_filename  # Anda dapat menyesuaikan ini sesuai kebutuhan
        })

        if response.status_code == 200:
            return jsonify({'success': True, 'employee': {'name': employee_name, 'photo': f'/show_image/{photo_filename}'}})
        else:
            return jsonify({'success': False, 'message': 'Gagal menyimpan ke database di Laravel'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/proses_absen', methods=['POST'])
def proses_absen():
    try:
        # Ambil file dari request
        employee_photo = request.files.get('employee-photo')
        
        if not employee_photo or employee_photo.filename == '':
            return jsonify({'success': False, 'message': 'Foto tidak terdeteksi'}), 400

        # Kirim data pegawai ke backend Laravel
        laravel_api_url = 'http://localhost:8000/api/proses_absen'  # Ganti dengan URL Laravel API
        files = {'foto': (employee_photo.filename, employee_photo.stream, employee_photo.mimetype)}

        response = requests.post(laravel_api_url, files=files)

        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Berhasil melakukan absen', 'data': response.json()})
        else:
            return jsonify({'success': False, 'message': response.json().get('message', 'Gagal menyimpan ke database di Laravel')}), response.status_code

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
