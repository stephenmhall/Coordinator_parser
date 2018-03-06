import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QProgressBar,
                             QPushButton, QMessageBox, QMainWindow, QFileDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit,
                             QCheckBox, QListWidget, QToolTip,
                             QFrame, QStatusBar)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import csv
from math import radians, cos, sin, asin, sqrt
import webbrowser
import ast
from simplekml import Kml, Snippet, Types
import datetime
import json


class PlotFiles(QThread):
    progressSignal = pyqtSignal(int)
    threadMessage = pyqtSignal(str)

    def __init__(self, results, issilist, google):
        QThread.__init__(self)
        self.results = results
        self.issilist = issilist
        self.google = google
        self.maxRange = len(self.issilist)
        self.stopped = 0

    def __del__(self):
        self.wait()

    def plot_the_files(self, results, issi, google):
        """
        Receives the results and an issi's to plot
        :param google:
        :param results:
        :param issi:
        :return:
        """

        when = []
        coord = []
        speeds = []
        headings = []
        times = []
        for x in range(0, len(results[issi])):
            tup = (results[issi][x][3], results[issi][x][2])
            year = results[issi][x][1][6:10]
            month = results[issi][x][1][3:5]
            day = results[issi][x][1][0:2]
            theTime = results[issi][x][1][11:]
            when.append("{}-{}-{}T{}Z".format(year, month, day, theTime))
            coord.append(tup)
            speeds.append(int(results[issi][x][4]))
            headings.append(int(results[issi][x][5]))
            times.append(results[issi][x][1])

        kml = Kml(name="{}_{}-{}-{}".format(issi, year, month, day), open=1)
        doc = kml.newdocument(name="{}".format(issi),
                              snippet=Snippet('Created {}-{}-{}'.format(year, month, day)))

        # Folder
        fol = doc.newfolder(name='Tracks')

        # schema for extra data
        schema = kml.newschema()
        schema.newgxsimplearrayfield(name='speed', type=Types.int, displayname='Speed')
        schema.newgxsimplearrayfield(name='heading', type=Types.int, displayname='Heading')
        schema.newgxsimplearrayfield(name='time', type=Types.string, displayname='Time')

        # New Track
        trk = fol.newgxtrack(name=issi)

        # Apply Schema
        trk.extendeddata.schemadata.schemaurl = schema.id

        # add all info to track
        trk.newwhen(when)
        trk.newgxcoord(coord)
        trk.extendeddata.schemadata.newgxsimplearraydata('time', times)
        trk.extendeddata.schemadata.newgxsimplearraydata('speed', speeds)
        trk.extendeddata.schemadata.newgxsimplearraydata('heading', headings)

        # Styling
        trk.stylemap.normalstyle.iconstyle.icon.href = 'http://earth.google.com/images/kml-icons/track-directional/track-0.png'
        trk.stylemap.normalstyle.linestyle.color = '99ffac59'
        trk.stylemap.normalstyle.linestyle.width = 6
        trk.stylemap.highlightstyle.iconstyle.icon.href = 'http://earth.google.com/images/kml - icons / track - directional / track - 0.png'
        trk.stylemap.highlightstyle.iconstyle.scale = 1.2
        trk.stylemap.highlightstyle.linestyle.color = '99ffac59'
        trk.stylemap.highlightstyle.linestyle.width = 8
        kml.save("results/{}_{}-{}-{}.kml".format(issi, year, month, day))

        if google:
            try:
                os.system("start " + "results/{}_{}-{}-{}.kml".format(issi, year, month, day))
            except:
                pass

    def run(self):
        firstplot = 1
        maxPercent = len(self.issilist)

        for i in range(len(self.issilist)):
            if not self.stopped:
                self.plot_the_files(self.results, self.issilist[i], self.google)
                update = ((i + 1) / maxPercent) * 100
                self.progressSignal.emit(update)

                if firstplot:
                    self.sleep(4)
                    firstplot = 0
            else:
                break
        self.threadMessage.emit('Plotting completed')

    def stop(self):
        self.stopped = 1
        self.threadMessage.emit('Plotting stopped')


def is_in_range(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers is 6371
    km = round(6371 * c, 4)
    # print(km)
    return km


class ParseFile(QThread):
    parse_progress_signal = pyqtSignal(int)
    parse_message_signal = pyqtSignal(str)
    parse_result_list_signal = pyqtSignal(object)
    parse_result_dict_signal = pyqtSignal(object)

    def __init__(self, filename, start_time, stop_time, distance,
                 search_lat, search_lon, issi_list, area_switch, issi_switch, file_size, all_route):
        QThread.__init__(self)
        self.all_route = all_route
        self.file_size = file_size
        self.issi_switch = issi_switch
        self.area_switch = area_switch
        self.issi_list = issi_list
        self.search_lon = search_lon
        self.search_lat = search_lat
        self.distance = distance
        self.stop_time = stop_time
        self.start_time = start_time
        self.filename = filename
        self.stopped = 0

    def __del__(self):
        self.wait()

    def parse_file(self, file):
        with file:
            reader = csv.reader(file)
            result_dictionary = {}
            number_of_rows = 0
            update = 0
            #area_search_change
            for row in reader:
                if row[0] != "Node":
                    number_of_rows += 1
                    update = ((number_of_rows + 1) / self.file_size) * 100
                    issi = row[0]
                    timestamp = row[2]
                    update_time = datetime.datetime.strptime(timestamp.split(' ')[1], '%H:%M:%S')
                    lat = float("{0:.6f}".format(float(row[7][0:2]) + (float(row[7][2:9])) / 60))
                    lon = -(float(row[8][:3]) + round(float(row[8][3:9]) / 60, 6))
                    speed = row[9]
                    bearing = row[10]
                    search_distance = 0.0

                    if self.area_switch:
                        search_distance = is_in_range(self.search_lon, self.search_lat, lon, lat)

                    if self.start_time <= update_time <= self.stop_time:
                        if not self.issi_switch or issi in self.issi_list:
                            if not self.area_switch or search_distance <= self.distance:
                                result_list = [[issi, timestamp, lat, lon, speed, bearing, search_distance]]

                                if issi not in result_dictionary:
                                    result_dictionary[issi] = result_list
                                else:
                                    result_list = result_dictionary[issi]
                                    result_list.append([issi, timestamp, lat, lon, speed, bearing, search_distance])
                                    result_dictionary[issi] = result_list
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
                self.parse_progress_signal.emit(update)
            new_issi_list = []
            for key in sorted(result_dictionary.keys()):
                new_issi_list.append(key)

            self.parse_result_list_signal.emit(new_issi_list)
            self.parse_result_dict_signal.emit(result_dictionary)
            self.parse_progress_signal.emit(100)
            self.parse_message_signal.emit('Searched {} lines and found {} Units'.format(number_of_rows,
                                                                                         len(result_dictionary.keys())))

    def run(self):
        f = open(self.filename, 'r')
        self.parse_file(f)

    def stop(self):
        self.stopped = 1


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.form_widget = FormWidget(self)
        self.setCentralWidget(self.form_widget)

        # Window Geometry
        self.setGeometry(300, 300, 600, 800)
        self.setWindowTitle('CoOrdinator Parser')
        self.setWindowIcon(QIcon('999.ico'))

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are You sure you want to Quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class FormWidget(QWidget):

    def __init__(self, parent):
        super(FormWidget, self).__init__(parent)
        self.resultDict = {}
        self.fileStartTime = ""
        self.fileStopTime = ""
        self.file_size = 0
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
        self.showCompleteRoutes = QCheckBox('Show Complete Routes')

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
        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.HLine)
        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.HLine)

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
        self.hbox_area_search.addWidget(self.showCompleteRoutes)
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
        self.vbox.addWidget(self.statusBar)

        self.setLayout(self.vbox)

    def save_data(self):
        print(self.resultDict)
        save_file = QFileDialog.getSaveFileName(self, 'Save CSV File',
                                              "ste1.json", "json Files (*.json)")
        if save_file[0]:
            with open(save_file[0], 'w') as jsonfile:
                json.dump(self.resultDict, jsonfile)
            #     fieldnames = ['issi', 'time', 'lat', 'lon', 'speed', 'heading', 'range']
            #     writer = csv.DictWriter(csvfile, self.resultDict.keys(), fieldnames=fieldnames)
            #     writer.writeheader()
            #     writer.writerow(self.resultDict)

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
            with f:
                reader = csv.reader(f)
                num_rows = 0
                for row in reader:
                    num_rows += 1
                    if row[0] != "Node":
                        if startText == "":
                            startText = row[2]
                        else:
                            endText = row[2]

                self.fileStartTime = startText[11:]
                self.fileStopTime = endText[11:]
                self.startTime.setText(self.fileStartTime)
                self.stopTime.setText(self.fileStopTime)
        self.file_size = num_rows
        self.statusBar.showMessage('File Loaded, contains {} lines'.format(self.file_size))
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
        if self.showCompleteRoutes.checkState() == Qt.Checked:
            all_route_switch = True

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
            print(issilist)

        self.parse_file = ParseFile(fname, starttime, stoptime,
                                    distance, searchlat, searchlon, issilist,
                                    area_switch, issi_switch, self.file_size, all_route_switch)
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

        if sender.text() == "Plot all ISSI's (caution)":
            for key in sorted(self.resultDict.keys()):
                issilist.append(key)
        else:
            issilist.append(self.issiList.currentItem().text())

        self.plot_thread = PlotFiles(self.resultDict, issilist, self.openGoogleEarth)
        self.plot_thread.progressSignal.connect(self.updateProgress)
        self.plot_thread.threadMessage.connect(self.updateProgress)
        self.plot_thread.start()

    def stopThread(self):
        self.plot_thread.stop()
        self.statusBar.showMessage('Plot stopped')

    def updateProgress(self, value):

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
