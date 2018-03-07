import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QProgressBar,
                             QPushButton, QMessageBox, QMainWindow, QFileDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit,
                             QCheckBox, QListWidget,
                             QFrame, QStatusBar)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import csv
import webbrowser
import ast
import datetime
import json

from parsefile import ParseFile
from plotfile import PlotFiles


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.form_widget = FormWidget(self)
        self.setCentralWidget(self.form_widget)

        # Window Geometry
        self.setGeometry(300, 300, 800, 800)
        self.setWindowTitle('CoOrdinator Parser')
        self.setWindowIcon(QIcon('999.ico'))
        # making a change for the sake of it.

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are You sure you want to Quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


# noinspection PyUnresolvedReferences,PyArgumentList
class FormWidget(QWidget):

    def __init__(self, parent):
        super(FormWidget, self).__init__(parent)
        self.resultDict = {}
        self.fileStartTime = ""
        self.fileStopTime = ""
        self.openGoogleEarth = True

        self.statusBar = QStatusBar()
        self.statusBar.showMessage('Open a CSV File to begin')

        # Buttons
        self.openFileBtn = QPushButton('Open CSV File', self)
        self.openFileBtn.setToolTip('Open Coordinator formatted CSV files')
        self.openFileBtn.clicked.connect(self.showOpenFile)
        self.startParseBtn = QPushButton('Start Search', self)
        self.startParseBtn.clicked.connect(self.parseFile)
        self.startParseBtn.setDisabled(True)
        self.plotSelectionBtn = QPushButton('Plot Selected ISSI', self)
        self.plotSelectionBtn.clicked.connect(self.onPlotFile)
        self.plotSelectionBtn.setDisabled(True)
        self.saveDataBtn = QPushButton('Save Search Data as json', self)
        self.saveDataBtn.clicked.connect(self.save_data)
        self.saveDataBtn.setDisabled(True)
        self.resetTimeBtn = QPushButton('Reset Times', self)
        self.resetTimeBtn.clicked.connect(self.onResetTimes)
        self.resetTimeBtn.setDisabled(True)
        self.plotAllBtn = QPushButton("Plot all ISSI's (caution)")
        self.plotAllBtn.clicked.connect(self.onPlotFile)
        self.plotAllBtn.setDisabled(True)
        self.stopPlotBtn = QPushButton('Stop Plot')
        self.stopPlotBtn.clicked.connect(self.stopThread)
        self.stopPlotBtn.setDisabled(True)

        # CheckBoxes
        self.areaSearchSwitch = QCheckBox('Search Area', self)
        self.areaSearchSwitch.stateChanged.connect(self.areaSearch)
        self.issiSearchSwitch = QCheckBox('search ISSI', self)
        self.issiSearchSwitch.stateChanged.connect(self.issiSearch)
        self.googleEarthInstalled = QCheckBox('Plot to Google Earth')
        self.googleEarthInstalled.stateChanged.connect(self.googleEarth)
        self.googleEarthInstalled.toggle()

        # List Fields
        self.issiList = QListWidget()
        self.issiList.setToolTip('Single Click to show details\nDouble Click to add to ISSI search')
        self.issiList.currentItemChanged.connect(self.onIssiClick)
        self.issiList.itemDoubleClicked.connect(self.onissidoubleclick)
        self.detailsList = QListWidget()
        self.detailsList.setToolTip('Double Click to plot on Google Maps')
        self.detailsList.itemDoubleClicked.connect(self.onDetailDoubleClick)

        # Labels
        self.latLabel = QLabel('Latitude')
        self.lonLabel = QLabel('Longitude')
        self.distLabel = QLabel('Search Radius')
        self.starttimeLabel = QLabel('Start Time')
        self.stoptimeLabel = QLabel('Stop Time')

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.HLine)
        self.line1.setFrameShadow(QFrame.Sunken)
        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.HLine)
        self.line2.setFrameShadow(QFrame.Sunken)
        self.line3 = QFrame()
        self.line3.setFrameShape(QFrame.HLine)
        self.line3.setFrameShadow(QFrame.Sunken)

        # Text Fields
        self.csvFileName = QLineEdit()
        self.startTime = QLineEdit('Start Time')
        self.stopTime = QLineEdit('Stop Time')
        self.lat = QLineEdit('57.148778')
        self.lat.setDisabled(True)
        self.lon = QLineEdit('-2.095077')
        self.lon.setDisabled(True)
        self.distance = QLineEdit('2.5')
        self.distance.setDisabled(True)
        self.issi = QLineEdit()
        self.issi.setDisabled(True)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.hbox1 = QHBoxLayout()
        self.hbox1.addWidget(self.openFileBtn, 1)
        self.hbox1.addWidget(self.csvFileName, 3)
        self.hbox2 = QHBoxLayout()
        self.hbox2.addWidget(self.starttimeLabel)
        self.hbox2.addWidget(self.startTime)
        self.hbox2.addWidget(self.stoptimeLabel)
        self.hbox2.addWidget(self.stopTime)
        self.hbox2.addWidget(self.resetTimeBtn, 2)
        self.hbox3 = QHBoxLayout()
        self.hbox3.addWidget(self.latLabel)
        self.hbox3.addWidget(self.lonLabel)
        self.hbox3.addWidget(self.distLabel)
        self.hbox4 = QHBoxLayout()
        self.hbox4.addWidget(self.lat)
        self.hbox4.addWidget(self.lon)
        self.hbox4.addWidget(self.distance)
        self.hbox5 = QHBoxLayout()
        self.hbox5.addWidget(self.issiSearchSwitch)
        self.hbox5.addWidget(self.issi, 1)
        self.hbox6 = QHBoxLayout()
        self.hbox6.addStrut(5)
        self.hbox6.addWidget(self.issiList, 1)
        self.hbox6.addWidget(self.detailsList, 5)
        self.hbox7 = QHBoxLayout()
        self.hbox7.addWidget(self.googleEarthInstalled)
        self.hbox7.addWidget(self.plotSelectionBtn)
        self.hbox7.addWidget(self.plotAllBtn)
        self.hbox7.addWidget(self.saveDataBtn)
        self.hbox8 = QHBoxLayout()
        self.hbox8.addWidget(self.stopPlotBtn)
        self.hbox8.addWidget(self.progress)
        self.hbox_area_search = QHBoxLayout()
        self.hbox_area_search.addWidget(self.areaSearchSwitch)
        self.hbox_area_search.addStretch(1)


        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox1)
        self.vbox.addLayout(self.hbox2)
        self.vbox.addWidget(self.line)
        self.vbox.addLayout(self.hbox_area_search)
        self.vbox.addLayout(self.hbox3)
        self.vbox.addLayout(self.hbox4)
        self.vbox.addWidget(self.line1)
        self.vbox.addLayout(self.hbox5)
        self.vbox.addWidget(self.line2)
        self.vbox.addWidget(self.startParseBtn)
        self.vbox.addLayout(self.hbox6, 1)
        self.vbox.addLayout(self.hbox7)
        self.vbox.addLayout(self.hbox8)
        self.vbox.addWidget(self.line3)
        self.vbox.addWidget(self.statusBar)

        self.setLayout(self.vbox)

    def save_data(self):
        print(self.resultDict)
        save_file = QFileDialog.getSaveFileName(self, 'Save CSV File',
                                              "ste1.json", "json Files (*.json)")
        if save_file[0]:
            with open(save_file[0], 'w') as jsonfile:
                json.dump(self.resultDict, jsonfile)

    def showOpenFile(self):
        self.issiList.clear()
        self.detailsList.clear()
        self.plotSelectionBtn.setDisabled(True)
        self.saveDataBtn.setDisabled(True)
        self.plotAllBtn.setDisabled(True)
        fname = QFileDialog.getOpenFileName(self, 'Open Coordinator CSV file',
                                            "", "CSV Files (*.csv)")

        if fname[0]:
            self.csvFileName.setText(fname[0])
            f = open(fname[0], 'r')

            startText = ""
            row_count = 0
            with f:
                reader = csv.reader(f)
                for row in reader:
                    row_count += 1
                    if row[0] != "Node":
                        if startText == "":
                            startText = row[2]
                        else:
                            endText = row[2]

                self.fileStartTime = startText[11:]
                self.fileStopTime = endText[11:]
                self.startTime.setText(self.fileStartTime)
                self.stopTime.setText(self.fileStopTime)

        self.statusBar.showMessage('File Loaded, contains {} lines'.format(row_count))
        self.startParseBtn.setDisabled(False)
        self.resetTimeBtn.setDisabled(False)

    def parseFile(self):
        print("Parsing file")
        self.plotSelectionBtn.setDisabled(True)
        self.saveDataBtn.setDisabled(True)
        self.plotAllBtn.setDisabled(True)
        self.progress.setValue(0)
        self.issiList.clear()
        self.detailsList.clear()
        fname = self.csvFileName.text()
        area_switch = False
        issi_switch = False
        all_route_switch = False

        if self.areaSearchSwitch.checkState() == Qt.Checked:
            area_switch = True
        if self.issiSearchSwitch.checkState() == Qt.Checked:
            issi_switch = True

        distance = 0
        searchlat = 0
        searchlon = 0
        starttime = datetime.datetime.strptime(self.startTime.text(), '%H:%M:%S')
        stoptime = datetime.datetime.strptime(self.stopTime.text(), '%H:%M:%S')
        issilist = []

        if self.areaSearchSwitch.checkState() == Qt.Checked:
            distance = float(self.distance.text())
            searchlat = float(self.lat.text())
            searchlon = float(self.lon.text())

        if self.issiSearchSwitch.checkState() == Qt.Checked:
            issilist = self.issi.text().split(';')

        self.parse_file = ParseFile(fname, starttime, stoptime,
                                    distance, searchlat, searchlon, issilist,
                                    area_switch, issi_switch)
        self.parse_file.parse_message_signal.connect(self.parse_update)
        self.parse_file.parse_progress_signal.connect(self.parse_update)
        self.parse_file.parse_result_dict_signal.connect(self.parse_update)
        self.parse_file.parse_result_list_signal.connect(self.parse_update)
        self.parse_file.start()

    def parse_update(self, value):
        if isinstance(value, int):
            self.progress.setValue(value)
        if isinstance(value, str):
            self.statusBar.showMessage(value)
        if isinstance(value, list):
            for i in value:
                self.issiList.addItem(i)
        if isinstance(value, dict):
            self.resultDict = value

    def onResetTimes(self):
        self.startTime.setText(self.fileStartTime)
        self.stopTime.setText(self.fileStopTime)

    def areaSearch(self, state):

        if state != Qt.Checked:
            self.lat.setDisabled(True)
            self.lon.setDisabled(True)
            self.distance.setDisabled(True)
        else:
            self.lat.setDisabled(False)
            self.lon.setDisabled(False)
            self.distance.setDisabled(False)

    def issiSearch(self, state):
        if state != Qt.Checked:
            self.issi.setDisabled(True)
        else:
            self.issi.setDisabled(False)

    def googleEarth(self, state):
        if state != Qt.Checked:
            self.openGoogleEarth = False
        else:
            self.openGoogleEarth = True

    def onIssiClick(self, current, previous):
        self.detailsList.clear()
        if current != None:
            for x in range(0, len(self.resultDict[current.text()])):
                self.detailsList.addItem('{}'.format(self.resultDict[current.text()][x]))
        self.plotSelectionBtn.setDisabled(False)
        self.saveDataBtn.setDisabled(False)
        self.plotAllBtn.setDisabled(False)

    def onissidoubleclick(self, state):
        currentissi = self.issi.text()
        if currentissi != "":
            currentissi += ";"
        currentissi = currentissi + state.text()
        self.issi.setText(currentissi)

    def onDetailDoubleClick(self, state):
        lat = ast.literal_eval(state.text())[2]
        lon = ast.literal_eval(state.text())[3]
        url = "https://www.google.com/maps/search/?api=1&query={},{}".format(lat, lon)
        webbrowser.open(url)

    def onPlotFile(self):
        self.progress.setValue(0)
        self.stopPlotBtn.setDisabled(False)
        sender = self.sender()
        issilist = []
        gps = [0]
        if self.areaSearchSwitch.checkState() == Qt.Checked:
            gps = [self.lat.text(), self.lon.text(), self.distance.text()]

        if sender.text() == "Plot all ISSI's (caution)":
            for key in sorted(self.resultDict.keys()):
                issilist.append(key)
        else:
            issilist.append(self.issiList.currentItem().text())

        self.plot_thread = PlotFiles(self.resultDict, issilist, self.openGoogleEarth, gps)
        self.plot_thread.progressSignal.connect(self.updateprogress)
        self.plot_thread.threadMessage.connect(self.updateprogress)
        self.plot_thread.start()

    def stopThread(self):
        self.plot_thread.stop()
        self.statusBar.showMessage('Plot stopped')

    def updateprogress(self, value):

        if isinstance(value, str):
            self.statusBar.showMessage(value)
            self.stopPlotBtn.setDisabled(True)
        else:
            self.progress.setValue(value)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
