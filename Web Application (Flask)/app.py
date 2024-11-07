from flask import Flask, render_template, Response, jsonify, request, send_from_directory
import cv2
import numpy as np
import os
import sqlite3
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow import keras
from ultralytics import YOLO
import time

app = Flask(__name__)

DATABASE = 'license_plates.db'
UPLOAD_FOLDER = 'statics/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

yolo_model = YOLO('statics/models/best.pt')

ocr_model = keras.models.load_model('statics/models/OCR.keras')

characters = ['&', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
char_to_num = tf.keras.layers.StringLookup(vocabulary=list(characters), mask_token=None)
num_to_char = tf.keras.layers.StringLookup(vocabulary=char_to_num.get_vocabulary(), mask_token=None, invert=True)

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS plates
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plate_number TEXT,
                  plate_type TEXT,
                  province TEXT,
                  entry_date TEXT,
                  entry_time TEXT,
                  exit_date TEXT,
                  exit_time TEXT)''')
    conn.commit()
    conn.close()

init_db()

camera = cv2.VideoCapture(0)

last_entry_times = {}

def get_province(last_two_digits):
    province_map = {
        '15': 'آذربایجان شرقی', '25': 'آذربایجان شرقی', '35': 'آذربایجان شرقی',
        '17': 'آذربایجان غربی', '27': 'آذربایجان غربی', '37': 'آذربایجان غربی',
        '91': 'اردبیل',
        '13': 'اصفهان', '53': 'اصفهان', '67': 'اصفهان', '23': 'اصفهان', '43': 'اصفهان',
        '68': 'البرز', '78': 'البرز', '21': 'البرز',
        '98': 'ایلام',
        '48': 'بوشهر', '58': 'بوشهر',
        '11': 'تهران', '22': 'تهران', '33': 'تهران', '44': 'تهران', '55': 'تهران',
        '66': 'تهران', '77': 'تهران', '88': 'تهران', '99': 'تهران', '10': 'تهران',
        '20': 'تهران', '30': 'تهران', '40': 'تهران', '50': 'تهران', '60': 'تهران',
        '70': 'تهران', '80': 'تهران', '90': 'تهران', '38': 'تهران',
        '71': 'چهارمحال و بختیاری', '81': 'چهارمحال و بختیاری',
        '26': 'خراسان شمالی', '74': 'خراسان شمالی',
        '12': 'خراسان رضوی', '36': 'خراسان رضوی', '32': 'خراسان رضوی', '42': 'خراسان رضوی',
        '52': 'خراسان جنوبی',
        '14': 'خوزستان', '24': 'خوزستان', '34': 'خوزستان',
        '87': 'زنجان', '97': 'زنجان',
        '86': 'سمنان', '96': 'سمنان',
        '85': 'سیستان و بلوچستان', '95': 'سیستان و بلوچستان',
        '63': 'فارس', '93': 'فارس', '73': 'فارس', '83': 'فارس',
        '79': 'قزوین', '89': 'قزوین',
        '16': 'قم',
        '51': 'کردستان', '61': 'کردستان',
        '45': 'کرمان', '65': 'کرمان', '75': 'کرمان',
        '19': 'کرمانشاه', '29': 'کرمانشاه', '39': 'کرمانشاه',
        '49': 'کهگیلویه و بویراحمد',
        '59': 'گلستان', '69': 'گلستان',
        '46': 'گیلان', '76': 'گیلان', '56': 'گیلان',
        '31': 'لرستان', '41': 'لرستان',
        '62': 'مازندران', '82': 'مازندران', '72': 'مازندران', '92': 'مازندران',
        '47': 'مرکزی', '57': 'مرکزی',
        '84': 'هرمزگان', '94': 'هرمزگان',
        '18': 'همدان', '28': 'همدان',
        '54': 'یزد', '64': 'یزد'
    }
    return province_map.get(last_two_digits, 'نامشخص')

def get_plate_type(character):
    plate_type_map = {
        'U': 'ارتش',
        'E': 'عمومی', 'K': 'عمومی', 'T': 'عمومی',
        '-': 'ناشنوایان', 'B': 'شخصی', 'C': 'شخصی', 'D': 'شخصی', 'H': 'شخصی', 'J': 'شخصی',
        'L': 'شخصی', 'M': 'شخصی', 'N': 'شخصی', 'O': 'شخصی', 'Q': 'شخصی', 'R': 'شخصی',
        'S': 'شخصی', 'V': 'شخصی', 'W': 'معلولین', 'X': 'شخصی', 'Y': 'شخصی',
        'Z': 'وزارت دفاع',
        'F': 'نیروهای مسلح',
        'P': 'نیروی انتظامی',
        'I': 'سپاه پاسداران',
        '&': 'سرویس و خدمات',
        '@': 'دیپلمات',
        'A': 'دولتی',
        'G': 'گذر موقت'
    }
    return plate_type_map.get(character, 'نامشخص')

def process_license_plate(frame):
    results = yolo_model(frame)
    
    if len(results) > 0 and len(results[0].boxes) > 0:
        box = results[0].boxes[0]
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        plate_img = frame[y1:y2, x1:x2]
        
        img = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        img = cv2.resize(img, (256, 65))
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=-1)
        img = np.expand_dims(img, axis=0)
        
        pred = ocr_model.predict(img)
        pred = pred.argmax(axis=-1)
        
        plate_number = tf.strings.reduce_join(num_to_char(pred[0])).numpy().decode("utf-8")
        
        province = get_province(plate_number[-2:])
        plate_type = get_plate_type(plate_number[2])
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{plate_number} - {province} - {plate_type}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        return frame, plate_number, province, plate_type
    
    return frame, None, None, None

def generate_frames():
    last_prediction_time = 0
    last_plate_number = None
    last_province = None
    last_plate_type = None
    while True:
        success, frame = camera.read()
        if not success:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + b'Error: Camera not connected\r\n')
        else:
            current_time = time.time()
            if current_time - last_prediction_time >= 1:
                frame, plate_number, province, plate_type = process_license_plate(frame)
                
                if plate_number:
                    add_plate_to_db(plate_number, plate_type, province)
                    last_plate_number = plate_number
                    last_province = province
                    last_plate_type = plate_type
                
                last_prediction_time = current_time
            else:
                if last_plate_number:
                    cv2.putText(frame, f"{last_plate_number} - {last_province} - {last_plate_type}", 
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def add_plate_to_db(plate_number, plate_type, province):
    current_time = datetime.now()
    
    if plate_number in last_entry_times:
        if current_time - last_entry_times[plate_number] < timedelta(seconds=10):
            return
    
    last_entry_times[plate_number] = current_time
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO plates (plate_number, plate_type, province, entry_date, entry_time)
                 VALUES (?, ?, ?, ?, ?)''',
              (plate_number, plate_type, province,
               current_time.strftime('%Y-%m-%d'), current_time.strftime('%H:%M:%S')))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/backup')
def backup():
    return render_template('backup.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/service')
def service():
    return render_template('Service.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_plates', methods=['GET'])
def get_plates():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM plates ORDER BY id DESC LIMIT 100')
    plates = c.fetchall()
    conn.close()
    return jsonify(plates)

@app.route('/search_plate', methods=['POST'])
def search_plate():
    plate_number = request.json['plate_number']
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM plates WHERE plate_number LIKE ?', ('%' + plate_number + '%',))
    results = c.fetchall()
    conn.close()
    return jsonify(results)

@app.route('/get_stats', methods=['GET'])
def get_stats():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM plates')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM plates WHERE entry_date = ?', (datetime.now().strftime('%Y-%m-%d'),))
    today_entry = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM plates WHERE exit_date = ?', (datetime.now().strftime('%Y-%m-%d'),))
    today_exit = c.fetchone()[0]
    conn.close()
    
    camera_connected = camera.isOpened()
    
    return jsonify({
        "total": total,
        "today_entry": today_entry,
        "today_exit": today_exit,
        "alerts": 0 if camera_connected else 1
    })

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('statics/voices', filename)

@app.route('/play_audio/<plate_type>')
def play_audio(plate_type):
    audio_files = {
        "ارتش": "Army.wav",
        "دیپلمات": "Diplomat.wav",
        "گذر موقت": "GozarMovaghat.wav",
        "کشاورزی": "Keshavarzi.wav",
        "نیروهای مسلح": "NiroMosalah.wav",
        "شخصی": "Personal.wav",
        "نیروی انتظامی": "Police.wav",
        "سپاه پاسداران": "Sepah.wav",
        "دولتی": "Dolati.wav",
        "تشریفات": "Tashrifat.wav",
        "خدمات": "service.wav",
        "عمومی": "omumi.wav",
        "تاکسی": "Taxi.wav",
        "وزارت دفاع": "VezaratDefa.wav"
    }
    
    audio_file = audio_files.get(plate_type)
    
    if audio_file:
        return jsonify({"audio_file": audio_file})
    else:
        return jsonify({"error": "No audio file for this plate type"}), 404

if __name__ == '__main__':
    app.run(debug=True)