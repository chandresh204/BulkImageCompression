from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QFileDialog, QRadioButton, QPushButton
from PyQt5.QtCore import QPropertyAnimation, QRect, QObject, pyqtSignal, QThread
from PyQt5 import uic
import sys
import os


class ImageOperations(QObject):
    progressSignal = pyqtSignal(int)
    finishSignal = pyqtSignal()

    def __init__(self, inputDir, outputDir, xDimen, yDimen, compression, rotation):
        super().__init__()
        self.inputDir = inputDir
        self.outputDir = outputDir
        self.compValue = compression
        self.rotation = rotation
        self.xDimen = xDimen
        self.yDimen = yDimen

    def run(self):
        # start conversion here
        self.totalInputs = list(os.scandir(self.inputDir)).__len__()
        completed = 0
        for i in os.scandir(self.inputDir):
            with open(i, 'rb') as file:
                pathIndex = file.name.rindex("/")
                outfile = file.name[(pathIndex + 1):file.name.__len__()]
                # create ffmpeg script
                if self.rotation != 0:
                    if self.rotation == 90:
                        ffmpeg = f"ffmpeg -i {file.name} -qscale:v {self.compValue} -vf \"transpose=2,scale={self.xDimen}:{self.yDimen}\" {self.outputDir}/{outfile}"
                        os.system(ffmpeg)
                        completed = completed + 1
                        self.progressSignal.emit(int(completed * 100 / self.totalInputs))
                        continue
                    if self.rotation == -90:
                        ffmpeg = f"ffmpeg -i {file.name} -qscale:v {self.compValue} -vf \"transpose=1,scale={self.xDimen}:{self.yDimen}\" {self.outputDir}/{outfile}"
                        os.system(ffmpeg)
                        completed = completed + 1
                        self.progressSignal.emit(int(completed * 100 / self.totalInputs))
                        continue
                    if self.rotation == 180:
                        ffmpeg = f"ffmpeg -i {file.name} -qscale:v {self.compValue} -vf \"rotate=3.141592654,scale={self.xDimen}:{self.yDimen}\" {self.outputDir}/{outfile}"
                        os.system(ffmpeg)
                        completed = completed + 1
                        self.progressSignal.emit(int(completed * 100 / self.totalInputs))
                        continue
                ffmpeg = f"ffmpeg -i {file.name} -qscale:v {self.compValue} -vf scale={self.xDimen}:{self.yDimen} {self.outputDir}/{outfile}"
                os.system(ffmpeg)
                completed = completed + 1
                self.progressSignal.emit(int(completed * 100 / self.totalInputs))
        self.finishSignal.emit()


class MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('bulkimagecompression.ui', self)

        # initialize variables
        self.inputDir = None
        self.outputDir = None
        self.xDimen = -1
        self.yDimen = -1
        self.compValue = 0
        self.rotation = 0
        self.totalInputs = 0
        self.qThread = None
        self.compressor = None

        # load progressBar Dimensions
        self.progX = self.progressBar.geometry().x()
        self.progY = self.progressBar.geometry().y()
        self.progHeight = self.progressBar.geometry().height()
        self.progLastPoint = 0
        self.progMaxWidth = self.progBackground.geometry().width()

        self.inputFolderBtn.clicked.connect(self.selectInputDir)
        self.outputFolderBtn.clicked.connect(self.selectOutputDir)
        self.startBtn.clicked.connect(self.startConversion)
        #   QRadioButton.toggled.connect()
        self.radioNoRotation.toggled.connect(lambda: self.changeRotation(0))
        self.radioClockwise.toggled.connect(lambda: self.changeRotation(-90))
        self.radioAnticlockwise.toggled.connect(lambda: self.changeRotation(90))
        self.radio180degree.toggled.connect(lambda: self.changeRotation(180))

    def selectInputDir(self):
        self.inputDir = QFileDialog.getExistingDirectory()
        self.iPathLabel.setText(self.inputDir)
        print(self.inputDir)

    def selectOutputDir(self):
        self.outputDir = QFileDialog.getExistingDirectory()
        self.oPathLabel.setText(self.outputDir)

    def changeRotation(self, angle):
        self.progInfo.setText(f"rotation set {angle}")
        self.rotation = angle

    def startConversion(self):

        # check for any error
        if self.inputDir is None or self.outputDir is None:
            self.progInfo.setText("Error: Input or Output Directory not set")
            return
        if self.inputDir == self.outputDir:
            self.progInfo.setText("Error: Input and Output directories are same.")
            return
        xText = self.xEdit.toPlainText()
        yText = self.yEdit.toPlainText()
        compText = self.compEdit.toPlainText()
        try:
            self.xDimen = int(xText)
            self.yDimen = int(yText)
        except ValueError:
            self.progInfo.setText("Error: Resolution value is invalid")
            return
        try:
            self.compValue = int(compText)
        except ValueError:
            self.progInfo.setText("Error: Compression value is invalid")
            return

        # start compressor here
        self.startBtn.setDisabled(True)
        self.qThread = QThread()
        self.compressor = ImageOperations(self.inputDir, self.outputDir, self.xDimen, self.yDimen, self.compValue, self.rotation)
        self.compressor.moveToThread(self.qThread)
        self.qThread.started.connect(self.compressor.run)
        self.compressor.progressSignal.connect(self.updateProgress)
        #   self.compressor.finishSignal.connect(self.qThread.quit)
        #   self.compressor.finishSignal.connect(self.compressor.deleteLater)
        #   self.compressor.finishSignal.connect(self.qThread.deleteLater)
        self.compressor.finishSignal.connect(lambda: self.startBtn.setEnabled(True))
        self.qThread.start()

    def updateProgress(self, completed):
        print(f"{completed} % completed")
        self.progInfo.setText(f"{completed}% completed")
        progWidth = self.progMaxWidth * completed / 100
        self.anim = QPropertyAnimation(self.progressBar, b"geometry")
        self.anim.setDuration(100)
        self.anim.setStartValue(QRect(self.progX, self.progY, self.progLastPoint, self.progHeight))
        self.anim.setEndValue(QRect(self.progX, self.progY, progWidth, self.progHeight))
        self.anim.start()
        self.progLastPoint = progWidth


app = QApplication(sys.argv)
win = MainUI()
win.show()
app.exec()