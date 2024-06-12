from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(20, 10, 89, 25))
        self.pushButton.setObjectName("pushButton")
        self.closeButton = QtWidgets.QPushButton(self.centralwidget)
        self.closeButton.setGeometry(QtCore.QRect(20, 50, 89, 25))
        self.closeButton.setObjectName("closeButton")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(130, 10, 640, 480))
        self.label.setText("")
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.brightnessSlider = QtWidgets.QSlider(self.centralwidget)
        self.brightnessSlider.setGeometry(QtCore.QRect(20, 90, 89, 22))
        self.brightnessSlider.setOrientation(QtCore.Qt.Horizontal)
        self.brightnessSlider.setObjectName("brightnessSlider")
        self.brightnessLabel = QtWidgets.QLabel(self.centralwidget)
        self.brightnessLabel.setGeometry(QtCore.QRect(20, 120, 91, 16))
        self.brightnessLabel.setObjectName("brightnessLabel")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Car Plate Recognition"))
        self.pushButton.setText(_translate("MainWindow", "Open Camera"))
        self.closeButton.setText(_translate("MainWindow", "Close Camera"))
        self.brightnessLabel.setText(_translate("MainWindow", "Brightness"))