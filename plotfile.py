from PyQt5.QtCore import QThread, pyqtSignal
from simplekml import Kml, Snippet, Types
from math import radians, cos, sin, asin, degrees, atan2
import os


class PlotFiles(QThread):
    progressSignal = pyqtSignal(int)
    threadMessage = pyqtSignal(str)

    def __init__(self, results, issilist, google, gps):
        QThread.__init__(self)
        self.gps = gps
        self.results = results
        self.issilist = issilist
        self.google = google
        self.maxRange = len(self.issilist)
        self.stopped = 0

    def __del__(self):
        self.wait()

    def plot_the_files(self, results, issi, google, gps, firstplot):
        """
        Receives the results and an issi's to plot
        :param firstplot:
        :param gps:
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
        year = results[issi][0][1][6:10]
        month = results[issi][0][1][3:5]
        day = results[issi][0][1][0:2]

        kml = Kml(name="{}_{}-{}-{}".format(issi, year, month, day), open=1)
        doc = kml.newdocument(name="{}".format(issi),
                              snippet=Snippet('Created {}-{}-{}'.format(year, month, day)))

        for x in range(0, len(results[issi])):
            tup = (results[issi][x][3], results[issi][x][2])
            theTime = results[issi][x][1][11:]
            when.append("{}-{}-{}T{}Z".format(year, month, day, theTime))
            coord.append(tup)
            speeds.append(int(results[issi][x][4]))
            headings.append(int(results[issi][x][5]))
            times.append(results[issi][x][1])

        # Create circle track
        if gps[0] != 0 and firstplot:

            R = 6378.1
            d = float(gps[2])  # distance
            circle_coords = []

            lat1 = radians(float(gps[0]))
            lon1 = radians(float(gps[1]))

            for b in range(1, 360):
                brng = radians(b)
                lat2 = asin(sin(lat1) * cos(d / R) + cos(lat1) * sin(d / R) * cos(brng))
                lon2 = lon1 + atan2(sin(brng) * sin(d / R) * cos(lat1), cos(d / R) - sin(lat1) * sin(lat2))
                lat2 = degrees(lat2)
                lon2 = degrees(lon2)
                circle_coords.append((lon2, lat2))

            doc2 = kml.newdocument(name="Search Area",
                                  snippet=Snippet('{}-{}-{}'.format(gps[0], gps[1], gps[2])))
            fol2 = doc2.newfolder(name='Search Area')
            trk2 = fol2.newgxtrack(name='search area')
            trk2.newgxcoord(circle_coords)
            trk2.stylemap.normalstyle.linestyle.color = '641400FF'
            trk2.stylemap.normalstyle.linestyle.width = 6

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
        trk.stylemap.normalstyle.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/track.png'
        trk.stylemap.normalstyle.linestyle.color = '99ffac59'
        trk.stylemap.normalstyle.linestyle.width = 6
        trk.stylemap.highlightstyle.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/track.png'
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
                self.plot_the_files(self.results, self.issilist[i], self.google, self.gps, firstplot)
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