import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QProgressBar,
                             QPushButton, QMessageBox, QMainWindow, QFileDialog, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit,
                             QCheckBox, QListWidget,
                             QFrame, QStatusBar)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import webbrowser
import ast
import datetime
import json
import csv
from parsefile import ParseFile
from plotfile import PlotFiles


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.form_widget = FormWidget(self)
        self.setCentralWidget(self.form_widget)

        # Window Geometry
        self.setGeometry(300, 300, 800, 800)
        self.setWindowTitle('CoOrdinator file Searcher By Stephen Hall')
        self.setWindowIcon(QIcon('999.ico'))

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
        self.csvList = []
        self.fileStartTime = ""
        self.fileStopTime = ""
        self.openGoogleEarth = True

        self.statusBar = QStatusBar()
        self.statusBar.showMessage('Open a CSV File to begin')

        # Buttons
        self.openFileBtn = QPushButton('Open CSV Files', self)
        self.openFileBtn.setToolTip('Open Coordinator formatted CSV files')
        self.openFileBtn.clicked.connect(self.showOpenFile)
        self.startParseBtn = QPushButton('Start Search', self)
        self.startParseBtn.clicked.connect(self.parseFile)
        self.startParseBtn.setDisabled(True)
        self.plotSelectionBtn = QPushButton('Plot Selected ISSI', self)
        self.plotSelectionBtn.clicked.connect(self.onPlotFile)
        self.plotSelectionBtn.setDisabled(True)
        self.saveDataBtn = QPushButton('Save ISSI Search Data', self)
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
        self.openResultsFolder = QPushButton('Open Results folder')
        self.openResultsFolder.clicked.connect(self.open_results_folder)
        self.openResultsFolder.setDisabled(True)

        # CheckBoxes
        self.areaSearchSwitch = QCheckBox('Search Area', self)
        self.areaSearchSwitch.stateChanged.connect(self.areaSearch)
        self.issiSearchSwitch = QCheckBox('search for ISSIs', self)
        self.issiSearchSwitch.stateChanged.connect(self.issiSearch)
        self.googleEarthInstalled = QCheckBox('Plot to Google Earth')
        self.googleEarthInstalled.stateChanged.connect(self.googleEarth)
        self.googleEarthInstalled.toggle()
        self.includeissiswitch = QCheckBox('Include Range', self)
        self.includeissiswitch.stateChanged.connect(self.includes)
        self.excludeissiswitch = QCheckBox('Exclude Range', self)
        self.excludeissiswitch.stateChanged.connect(self.excludes)

        # List Fields
        self.issiList = QListWidget()
        self.issiList.setToolTip('Single Click to show details\nDouble Click to add to ISSI search')
        self.issiList.currentItemChanged.connect(self.onIssiClick)
        self.issiList.itemDoubleClicked.connect(self.onissidoubleclick)
        self.detailsList = QListWidget()
        self.detailsList.setToolTip('Double Click to plot on Google Maps')
        self.detailsList.itemDoubleClicked.connect(self.onDetailDoubleClick)

        # Labels
        self.latLabel = QLabel('Latitude: ')
        self.lonLabel = QLabel('Longitude: ')
        self.distLabel = QLabel('Search Radius (km): ')
        self.starttimeLabel = QLabel('Start Time: ')
        self.stoptimeLabel = QLabel('Stop Time: ')
        self.issilabel = QLabel('ISSI Results')
        self.detailslabel = QLabel('Details [ISSI, Time, Latitude, Longitude, Speed, Heading, Distance from search, Location]')

        # Lines
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
        self.csvFileName = QLineEdit('No Files loaded')
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
        self.includeissi = QLineEdit('677;6780;6785')
        self.includeissi.setToolTip('3 or 4 digits separated by ;')
        self.includeissi.setDisabled(True)
        self.excludeissi = QLineEdit('688;666')
        self.excludeissi.setToolTip('3 or 4 digits separated by ;')
        self.excludeissi.setDisabled(True)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.hbox_load_files = QHBoxLayout()
        self.hbox_load_files.addWidget(self.openFileBtn, 1)
        self.hbox_load_files.addWidget(self.csvFileName, 5)
        self.hbox_search_time = QHBoxLayout()
        self.hbox_times = QHBoxLayout()
        self.hbox_search_time.addWidget(self.resetTimeBtn, 1)
        self.hbox_times.addWidget(self.starttimeLabel)
        self.hbox_times.addWidget(self.startTime)
        self.hbox_times.addWidget(self.stoptimeLabel)
        self.hbox_times.addWidget(self.stopTime)
        self.hbox_times.addStretch(1)
        self.hbox_search_time.addLayout(self.hbox_times, 5)

        self.hbox_search_area = QHBoxLayout()
        self.hbox_search_area.addWidget(self.areaSearchSwitch)
        self.hbox_search_area.addStretch(1)
        self.hbox_search_area.addWidget(self.latLabel)
        self.hbox_search_area.addWidget(self.lat)
        self.hbox_search_area.addWidget(self.lonLabel)
        self.hbox_search_area.addWidget(self.lon)
        self.hbox_search_area.addWidget(self.distLabel)
        self.hbox_search_area.addWidget(self.distance)
        self.hbox_serach_issi = QHBoxLayout()
        self.hbox_serach_issi.addWidget(self.issiSearchSwitch)
        self.hbox_serach_issi.addWidget(self.issi, 1)
        self.hbox_detail_labels = QHBoxLayout()
        self.hbox_detail_labels.addWidget(self.issilabel, 1)
        self.hbox_detail_labels.addWidget(self.detailslabel, 5)
        self.hbox_results = QHBoxLayout()
        self.hbox_results.addWidget(self.issiList, 1)
        self.hbox_results.addWidget(self.detailsList, 5)
        self.hbox_plot_results = QHBoxLayout()
        self.hbox_plot_results.addWidget(self.googleEarthInstalled)
        self.hbox_plot_results.addWidget(self.plotSelectionBtn)
        self.hbox_plot_results.addWidget(self.plotAllBtn)
        self.hbox_plot_results.addWidget(self.saveDataBtn)
        self.hbox_plot_results.addWidget(self.openResultsFolder)
        self.hbox_progress_bar = QHBoxLayout()
        self.hbox_progress_bar.addWidget(self.stopPlotBtn)
        self.hbox_progress_bar.addWidget(self.progress)
        self.hbox_filters = QHBoxLayout()
        self.hbox_filters.addWidget(self.includeissiswitch)
        self.hbox_filters.addWidget(self.includeissi)
        self.hbox_filters.addWidget(self.excludeissiswitch)
        self.hbox_filters.addWidget(self.excludeissi)


        # Create Vbox
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox_load_files)
        self.vbox.addLayout(self.hbox_search_time)
        self.vbox.addWidget(self.line)
        self.vbox.addLayout(self.hbox_search_area)
        self.vbox.addWidget(self.line1)
        self.vbox.addLayout(self.hbox_filters)
        self.vbox.addLayout(self.hbox_serach_issi)
        self.vbox.addWidget(self.line2)
        self.vbox.addWidget(self.startParseBtn)
        self.vbox.addLayout(self.hbox_detail_labels)
        self.vbox.addLayout(self.hbox_results, 1)
        self.vbox.addLayout(self.hbox_plot_results)
        self.vbox.addLayout(self.hbox_progress_bar)
        self.vbox.addWidget(self.line3)
        self.vbox.addWidget(self.statusBar)

        self.setLayout(self.vbox)

    def open_results_folder(self):
        filepath = os.path.abspath(os.path.dirname(sys.argv[0]))
        resultpath = filepath + '\\results\\'
        os.startfile(resultpath)

    def includes(self, state):
        if state == Qt.Checked:
            self.includeissi.setDisabled(False)
        else:
            self.includeissi.setDisabled(True)

    def excludes(self, state):
        if state == Qt.Checked:
            self.excludeissi.setDisabled(False)
        else:
            self.excludeissi.setDisabled(True)

    def save_data(self):
        current = self.issiList.selectedItems()
        print(current[0].text())
        save_file = QFileDialog.getSaveFileName(self, 'Save ISSI File',
                                                "results\\{}".format(current[0].text()),
                                                "Text Files (*.txt);;json Files (*.json);;csv Files (*.csv)")

        print(save_file)
        if save_file[1] == 'json Files (*.json)':
            with open(save_file[0], 'w') as jsonfile:
                json.dump(self.resultDict[current[0].text()], jsonfile)

        if save_file[1] == 'Text Files (*.txt)':
            with open(save_file[0], 'w') as txtfile:
                result_list = []
                for line in self.resultDict[current[0].text()]:
                    result_list.append('{}\n'.format(line))
                txtfile.writelines(result_list)

        if save_file[1] == 'csv Files (*.csv)':
            with open(save_file[0], 'w') as csvfile:
                fieldnames = ['ISSI', 'Time', 'Latitude', 'Longitute', 'Speed', 'Heading', 'Distance', 'Location']
                writer = csv.writer(csvfile, lineterminator='\n')
                writer.writerow(fieldnames)
                writer.writerows(self.resultDict[current[0].text()])

    def showOpenFile(self):
        self.csvList = []
        self.issiList.clear()
        self.detailsList.clear()
        self.plotSelectionBtn.setDisabled(True)
        self.saveDataBtn.setDisabled(True)
        self.plotAllBtn.setDisabled(True)
        fname = QFileDialog.getOpenFileNames(self, 'Open Coordinator CSV file',
                                            "", "CSV Files (*.csv)")

        if fname[0]:

            start_time_text = ""
            end_time_text = ""
            files_text = ""
            latest_end_time = datetime.datetime.strptime('01/01/1970 00:00:00', '%d/%m/%Y %H:%M:%S')
            row_count = 0
            line_fail_count = 0
            for file_id in range(len(fname[0])):
                f = open(fname[0][file_id], 'r')
                if files_text != "":
                    files_text += '; '
                files_text += (fname[0][file_id]).split('/')[-1]

                with f:
                    for row in f:
                        row_count += 1
                        self.csvList.append(row)

                row = 0
                for item in self.csvList:
                    row += 1
                    update = (row / row_count) * 100
                    self.progress.setValue(update)
                    item_list = item.split(',')
                    if item_list[0] == "Node":
                        continue
                    else:
                        try:
                            time_text = datetime.datetime.strptime(item_list[2], '%d/%m/%Y %H:%M:%S')
                        except:
                            line_fail_count += 1
                            continue
                        if start_time_text == "":
                            start_time_text = item_list[2]
                        else:
                            if time_text > latest_end_time:
                                latest_end_time = time_text
                                end_time_text = item_list[2]

                self.fileStartTime = start_time_text
                self.fileStopTime = end_time_text
                self.startTime.setText(self.fileStartTime)
                self.stopTime.setText(self.fileStopTime)

                self.csvFileName.setText(files_text)
                self.statusBar.showMessage('File Loaded, contains {} lines, with {} bad row(s)'.format(row_count, line_fail_count))
                self.startParseBtn.setDisabled(False)
                self.resetTimeBtn.setDisabled(False)
                print(line_fail_count)

        else:
            pass

    def parseFile(self):
        self.plotSelectionBtn.setDisabled(True)
        self.saveDataBtn.setDisabled(True)
        self.plotAllBtn.setDisabled(True)
        self.progress.setValue(0)
        self.issiList.clear()
        self.detailsList.clear()
        distance = 0
        searchlat = 0
        searchlon = 0
        starttime = datetime.datetime.strptime(self.startTime.text(), '%d/%m/%Y %H:%M:%S')
        stoptime = datetime.datetime.strptime(self.stopTime.text(), '%d/%m/%Y %H:%M:%S')
        issilist = []
        includeslist = []
        excludeslist = []
        area_switch = False
        issi_switch = False
        includes = False
        excludes = False

        if self.areaSearchSwitch.checkState() == Qt.Checked:
            area_switch = True
            distance = float(self.distance.text())
            searchlat = float(self.lat.text())
            searchlon = float(self.lon.text())
        if self.issiSearchSwitch.checkState() == Qt.Checked:
            issi_switch = True
            issilist = self.issi.text().split(';')
        if self.includeissiswitch.checkState() == Qt.Checked:
            includes = True
            includeslist = self.includeissi.text().split(';')
        if self.excludeissiswitch.checkState() == Qt.Checked:
            excludes = True
            excludeslist = self.excludeissi.text().split(';')

        self.parse_file = ParseFile(self.csvList, starttime, stoptime, distance, searchlat, searchlon, issilist,
                                    area_switch, issi_switch, includes, includeslist, excludes, excludeslist)

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
        self.openResultsFolder.setDisabled(False)

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
