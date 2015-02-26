#!/usr/bin/python

from xml.dom import minidom
from datetime import datetime, timedelta
import time
import sys
import argparse
import os.path
from pprint import pprint

timefmt_out = '%Y-%m-%dT%H:%M:%SZ'      # output time format
timefmt_ex = '%Y-%m-%d %H:%M:%S.%f'    # Nothing special. Local time.
timefmt_gpx = '%Y-%m-%dT%H:%M:%S.%fZ'   # Note: GPX uses ISO8601 in UTC!
gpxFile = ''
xmlFile = ''
outFile = ''


def str2timedelta(sTime):
    ''' Convert a string to a timedelta object.
        Correct format if necessary.
    '''
    if '.' not in sTime:
        if sTime.count(':') == 1:
            dTime = datetime.strptime(sTime, '%H:%M')
        else:
            dTime = datetime.strptime(sTime.replace(':.', ':00.'), '%H:%M:%S')
    else:
        dTime = datetime.strptime(sTime.replace(':.', ':00.'), '%H:%M:%S.%f')

    return timedelta(hours=dTime.hour, minutes=dTime.minute,
                     seconds=dTime.second, microseconds=dTime.microsecond)


class PolarEx:
    ''' Class representing a Polar exercise.
    '''
    def __init__(self, xml):
        self.time = datetime.strptime(
            xml.getElementsByTagName("time")[0].childNodes[0].nodeValue, timefmt_ex)
        if xml.getElementsByTagName("name"):
            self.name = xml.getElementsByTagName("name")[0].childNodes[0].nodeValue
        else:
            self.name = ""
        self.sport = xml.getElementsByTagName("sport")[0].childNodes[0].nodeValue
        resNode = xml.getElementsByTagName("result")[0]
        self.duration = str2timedelta(resNode.getElementsByTagName("duration")[0].childNodes[0].nodeValue)
        self.recRate = int(resNode.getElementsByTagName("recording-rate")[0].childNodes[0].nodeValue)
        if len(resNode.getElementsByTagName("heart-rate")) > 1:
            hrNode = resNode.getElementsByTagName("heart-rate")[1]
            self.hrAvg = hrNode.getElementsByTagName("average")[0].childNodes[0].nodeValue
            self.hrMax = hrNode.getElementsByTagName("maximum")[0].childNodes[0].nodeValue
        else:
            self.hrAvg = 0
            self.hrMax = 0

    def displayEx(self):
        pprint(vars(self))


class PolarLap:
    ''' Class representing a single lap coming from the polar side.
    '''
    def __init__(self, xml=None, polarEx=None):
        self.index = 0
        self.duration = 0
        self.hrAvg = 0
        self.hrMax = 0
        self.power = 0
        self.distance = 0
        if xml is not None:
            self.index = xml.attributes["index"].value
            self.duration = str2timedelta(
                xml.getElementsByTagName('duration')[0].childNodes[0].nodeValue)
            if xml.getElementsByTagName('heart-rate'):
                hrVals = xml.getElementsByTagName('heart-rate')[0]
                self.hrAvg = hrVals.getElementsByTagName('average')[0].childNodes[0].nodeValue
                self.hrMax = hrVals.getElementsByTagName('maximum')[0].childNodes[0].nodeValue
            if xml.getElementsByTagName('distance'):
                self.distance = xml.getElementsByTagName('distance')[0].childNodes[0].nodeValue

        if polarEx is not None:
            self.duration = polarEx.duration
            self.startTime = polarEx.time

    def setStart(self, start):
        self.startTime = start

    def xmlHeader(self, out):
        out.write('      <Lap StartTime="' + self.startTime.strftime(timefmt_out) + '">\n')
        out.write('        <TotalTimeSeconds>' + str(self.duration.total_seconds()) + '</TotalTimeSeconds>\n')
        out.write('        <DistanceMeters>' + str(self.distance) + '</DistanceMeters>\n')
        out.write('        <AverageHeartRateBpm>\n')
        out.write('          <Value>' + str(self.hrAvg) + '</Value>\n')
        out.write('        </AverageHeartRateBpm>\n')
        out.write('        <MaximumHeartRateBpm>\n')
        out.write('          <Value>' + str(self.hrMax) + '</Value>\n')
        out.write('        </MaximumHeartRateBpm>\n')
        out.write('        <Track>\n')

    def xmlFooter(self, out):
        out.write('        </Track>\n')
        out.write('      </Lap>\n')

    def displayLap(self):
        pprint(vars(self))


class GpxTrackPt:
    ''' Represents a single track coming from a GPX file.
    '''
    def __init__(self, xml):
        self.lat = xml.attributes["lat"].value
        self.lon = xml.attributes["lon"].value
        self.ele = xml.getElementsByTagName("ele")[0].childNodes[0].nodeValue
        self.time = datetime.strptime(
            xml.getElementsByTagName("time")[0].childNodes[0].nodeValue, timefmt_gpx)
        self.nsat = xml.getElementsByTagName("sat")[0].childNodes[0].nodeValue

    def toXML(self, fd):
        fd.write('            <Position>\n')
        fd.write('              <LatitudeDegrees>' + self.lat + '</LatitudeDegrees>\n')
        fd.write('              <LongitudeDegrees>' + self.lon + '</LongitudeDegrees>\n')
        fd.write('            </Position>\n')
        fd.write('            <AltitudeMeters>' + self.ele + '</AltitudeMeters>\n')

    def displayPt(self):
        pprint(vars(self))


class PolarLapFactory:
    ''' Class serving as a factory for PolarLap objects.
    '''
    @staticmethod
    def getLapsFromXML(xml, startTime):
        ret = []
        start = startTime
        xmlLaps = xml.getElementsByTagName('lap')
        for xmlLap in xmlLaps:
            lap = PolarLap(xmlLap)
            lap.setStart(start)
            ret.append(lap)
            start += lap.duration
        return ret


def ceilTime(dTime):
    ''' Round up a datetime object to next second
    '''
    if dTime.microsecond > 0:
        dTime = dTime.replace(second=dTime.second+1, microsecond=0)
    return dTime


def localTime2UTC(localTime):
    ''' Converts the given time to UTC with respect to the current locale.
    '''
    local = localTime.strftime(timefmt_ex)
    timestamp = str(time.mktime(datetime.strptime(local, timefmt_ex).timetuple()))[:-2]
    utc = datetime.utcfromtimestamp(int(timestamp))
    return utc


def startTime(xml):
    ''' Calculate start time as gpx end-time minus number of hrm values.
    '''
    localTime = datetime.strptime(
        xml.getElementsByTagName("exercise")[0].getElementsByTagName("time")[0].childNodes[0].nodeValue,
        timefmt_ex)
    utcTime = localTime2UTC(localTime)
    return utcTime


def xmlOutHeader(out, exercise):
    ''' Writes the output XML header to the given file.
    '''
    out.write('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n')
    out.write('<TrainingCenterDatabase xmlns="http://www.garmin.com/'
              'xmlschemas/TrainingCenterDatabase/v2" '
              'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
              'xsi:schemaLocation="http://www.garmin.com/xmlschemas/'
              'TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/'
              'TrainingCenterDatabasev2.xsd">\n\n')
    out.write('  <Activities>\n')
    out.write('    <Activity Sport="'+exercise.sport+'">\n')
    out.write('      <Id>' + exercise.time.strftime(timefmt_out) + '</Id>\n')


def xmlOutFooter(out):
    ''' Writes the XML footer to the given file.
    '''
    out.write('    </Activity>\n')
    out.write('  </Activities>\n')
    out.write('</TrainingCenterDatabase>\n')


def createTrackPointHash(gpx):
    ''' Creates the hash table of GpxTrackPt objects, where the time of each
        GpxTrackPt serves as the key.
    '''
    retHash = {}
    trkList = gpx.getElementsByTagName('trkpt')
    for trk in trkList:
        trkPt = GpxTrackPt(trk)
        retHash[trkPt.time] = trkPt
    print("%d GPX track points have been parsed and created." % (len(retHash)))
    return retHash


def processFiles():
    ''' Processes the input file(s).
    '''
    # Open the output file
    try:
        out = open(outFile, 'w')
    except:
        print("Could not open %s for writing. Exiting." % outFile)
        sys.exit(1)

    xml = minidom.parse(xmlFile)
    gpxTrkPts = {}
    if gpxFile:
        gpx = minidom.parse(gpxFile)
        gpxTrkPts = createTrackPointHash(gpx)

    # TODO: we might have several exercises in one XML :(
    exercise = PolarEx(xml.getElementsByTagName("exercise")[0])

    # Extract HRM and speed values and split them
    hrmList = []
    speedList = []
    sampleList = xml.getElementsByTagName('sample')
    for sample in sampleList:
        type = sample.getElementsByTagName('type')[0].childNodes[0].nodeValue
        if type.lower() == 'heartrate':
            hrmList = sample.getElementsByTagName('values')[0].childNodes[0].nodeValue.split(',')
        if type.lower() == 'speed':
            speedList = sample.getElementsByTagName('values')[0].childNodes[0].nodeValue.split(',')
    print("Found %d HRM values." % (len(hrmList)))
    print("Found %d speed values." % (len(speedList)))

    # Determine the start time(s)
    start_time = startTime(xml)
    print("XML start time: %s" % str(start_time))
    if gpxTrkPts:
        print("GPX start time: %s" % str(sorted(gpxTrkPts.keys())[0]))

    # Extract the list of laps
    lapList = []
    if xml.getElementsByTagName('laps'):
        lapList = PolarLapFactory.getLapsFromXML(xml.getElementsByTagName('laps')[0], start_time)
        print("%d laps have been parsed and created." % (len(lapList)))
    else:
        print("There are no laps in the given training file (%s)." % (xmlFile))
        print("Creating a pseudo lap.")
        pseudoLap = PolarLap(None, exercise)
        lapList.append(pseudoLap)

    # Start of XML output
    xmlOutHeader(out, exercise)

    # For each lap...
    curLapTime = start_time
    curHrm = 0
    curSpeed = 0
    nAssignedGpx = 0
    for lap in lapList:

        lap.xmlHeader(out)
        curTime = ceilTime(curLapTime)
        while (curTime < curLapTime + lap.duration):
            out.write('          <Trackpoint>\n')
            out.write('            <Time>' + curTime.strftime(timefmt_out) + '</Time>\n')

            # Look up the current time in the GPX hashtable
            if curTime in gpxTrkPts:
                trk = gpxTrkPts[curTime]
                trk.toXML(out)
                nAssignedGpx += 1

            # HRM
            if curHrm < len(hrmList):
                out.write('            <HeartRateBpm>\n')
                out.write('              <Value>' + hrmList[curHrm] + '</Value>\n')
                out.write('            </HeartRateBpm>\n')
                curHrm += 1

            # Speed
            if curSpeed < len(speedList):
                out.write('            <Extensions>\n')
                out.write('               <TPX xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2">\n')
                out.write('                 <Speed>' + speedList[curSpeed] + '</Speed>\n')
                out.write('               </TPX>\n')
                out.write('            </Extensions>\n')
                curSpeed += 1

            out.write('          </Trackpoint>\n')

            curTime += timedelta(0, exercise.recRate)
            # end while

        lap.xmlFooter(out)
        curLapTime += lap.duration
        # end for lap in lapList

    print("%d GPX track points have been assigned." % (nAssignedGpx))
    xmlOutFooter(out)
    out.close()


def main():
    ''' our main()
    '''
    global xmlFile, gpxFile, outFile

    # parse command line arguments
    parser = argparse.ArgumentParser(description="Convert Polar xml and gpx files to tcx")
    parser.add_argument("-x", "--xml", help="xml input file")
    parser.add_argument("-g", "--gpx", help="gpx input file")
    parser.add_argument("-o", "--out", help="xml output file")
    args = parser.parse_args()

    if args.xml:
        xmlFile = args.xml
    if args.gpx:
        gpxFile = args.gpx
    if args.out:
        outFile = args.out

    # At least xml file needs to be given
    if not xmlFile:
        print("Please provide an XML input file.")
        parser.print_help()
        sys.exit(1)

    # Give default output file name if none is given
    # TODO: Should be based on the date of the exercise
    if not outFile:
        outFile = "exercise-" + time.strftime("%Y-%m-%d") + ".tcx"

    # check the files for existence
    if xmlFile and not os.path.isfile(xmlFile):
        print("The given XML file %s doesn't exist." % (xmlFile))
        sys.exit(1)
    if gpxFile and not os.path.isfile(gpxFile):
        print("The given GPX file %s doesn't exist." % (gpxFile))
        sys.exit(1)
    if os.path.isfile(outFile):
        print("The given output file %s already exists. Exiting." % (outFile))
        sys.exit(1)

    processFiles()
    print("Exercise is written to '%s'" % outFile)
    sys.exit(0)


if __name__ == "__main__":
    main()
