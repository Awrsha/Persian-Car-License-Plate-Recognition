import sys
import cv2
import numpy as np
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from mainwindow_ui import Ui_MainWindow

import os
os.environ["TF_USE_LEGACY_KERAS"]="1"

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from pathlib import Path
import pytesseract
import os
import datetime

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.cap = None  # Camera capture object
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.brightness = 0  # Brightness value
        self.brightnessSlider.valueChanged.connect(self.change_brightness)
        
        # Connect buttons to functions
        self.pushButton.clicked.connect(self.open_camera)
        self.closeButton.clicked.connect(self.close_camera)
        
        # Load trained model
        self.model = keras.models.load_model('license_plate_model.h5')
        
        # Mapping characters to integers
        characters = sorted(list(set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')))
        self.char_to_num = layers.StringLookup(vocabulary=list(characters), mask_token=None)
        self.num_to_char = layers.StringLookup(vocabulary=self.char_to_num.get_vocabulary(), mask_token=None, invert=True)
        
        # Car plate logging
        self.car_plate_log = []

    def open_camera(self):
        self.cap = cv2.VideoCapture(0)  # Open default camera
        self.timer.start(20)  # Start timer to update frames every 20 ms

    def close_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.label.clear()

    def change_brightness(self, value):
        self.brightness = value

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Adjust brightness
        frame = cv2.convertScaleAbs(frame, alpha=1, beta=self.brightness)

        # Convert to RGB and display
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_image.shape
        bytes_per_line = 3 * width
        q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_img))

        # Car plate detection
        self.detect_car_plate(frame)

    def detect_car_plate(self, frame):
        # Example car plate detection logic (using pytesseract for simplicity)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # You should replace this with your own car plate detection code

        plates = pytesseract.image_to_string(gray_frame, config='--psm 11')

        # If a car plate is detected, log it
        if plates.strip():
            plate_text = plates.strip()
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.car_plate_log.append((plate_text, timestamp))
            with open("car_plate_log.txt", "a") as log_file:
                log_file.write(f"{timestamp}: {plate_text}\n")

    def closeEvent(self, event):
        self.close_camera()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
