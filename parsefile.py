from PyQt5.QtCore import QThread, pyqtSignal
import datetime
from math import radians, cos, sin, asin, sqrt


class ParseFile(QThread):
    parse_progress_signal = pyqtSignal(int)
    parse_message_signal = pyqtSignal(str)
    parse_result_list_signal = pyqtSignal(object)
    parse_result_dict_signal = pyqtSignal(object)

    def __init__(self, file, start_time, stop_time, distance,
                 search_lat, search_lon, issi_list, area_switch, issi_switch,
                 includes, includeslist, excludes, excludeslist):
        QThread.__init__(self)
        self.excludeslist = excludeslist
        self.excludes = excludes
        self.includeslist = includeslist
        self.includes = includes
        self.issi_switch = issi_switch
        self.area_switch = area_switch
        self.issi_list = issi_list
        self.search_lon = search_lon
        self.search_lat = search_lat
        self.distance = distance
        self.stop_time = stop_time
        self.start_time = start_time
        self.file = file
        self.stopped = 0

    def __del__(self):
        self.wait()

    def parse_file(self, file):
        result_dictionary = {}
        number_of_rows = 0
        update = 0
        update_list = []
        file_size = len(file)
        distance_list = []

        for row in file:
            row = row.split(',')
            if row[0] != "Node":
                number_of_rows += 1
                update = ((number_of_rows + 1) / file_size) * 100
                issi = row[0]
                timestamp = row[2]
                update_time = datetime.datetime.strptime(timestamp, '%d/%m/%Y %H:%M:%S')
                lat = float("{0:.6f}".format(float(row[7][0:2]) + (float(row[7][2:9])) / 60))
                lon = -(float(row[8][:3]) + round(float(row[8][3:9]) / 60, 6))
                speed = row[9]
                bearing = row[10]
                location = row[14]
                search_distance = 0.0

                if not self.includes or issi[:3] in self.includeslist or issi[:4] in self.includeslist:
                    if not self.excludes or issi[:3] not in self.excludeslist and issi[:4] not in self.excludeslist:
                        if self.start_time <= update_time <= self.stop_time:
                            if not self.issi_switch or issi in self.issi_list:
                                if self.area_switch:
                                    search_distance = self.is_in_range(self.search_lon, self.search_lat, lon, lat)
                                    if search_distance <= self.distance:
                                        if issi not in distance_list:
                                            distance_list.append(issi)

                                result = [issi, timestamp, lat, lon, speed, bearing, search_distance, location]
                                if issi not in result_dictionary:
                                    result_dictionary[issi] = [result]
                                else:
                                    result_list = result_dictionary[issi]
                                    result_list.append(result)
                                    result_dictionary[issi] = result_list

                            else:
                                continue
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

        if self.area_switch:
            new_result_dict = {}
            for i in distance_list:
                new_result_dict[i] = result_dictionary[i]
            self.parse_result_list_signal.emit(distance_list)
            self.parse_result_dict_signal.emit(new_result_dict)
            units_found = len(distance_list)
        else:
            self.parse_result_list_signal.emit(new_issi_list)
            units_found = len(new_issi_list)
            self.parse_result_dict_signal.emit(result_dictionary)

        self.parse_progress_signal.emit(100)
        self.parse_message_signal.emit('Searched {} lines and found {} Units'.format(number_of_rows,
                                                                                     units_found))

    def run(self):
        self.parse_file(self.file)

    def stop(self):
        self.stopped = 1

    def is_in_range(self, lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        # Radius of earth in kilometers is 6371
        km = round(6371 * c, 4)
        # print(km)
        return km