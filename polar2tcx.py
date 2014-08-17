#!/usr/bin/env python

from xml.dom import minidom
from datetime import datetime, timedelta
import math
import time

# Convert a string to a timedelta object
# Correct format if necessary
def str2timedelta(sTime):
  if '.' not in sTime:
    if sTime.count(':') == 1:
      dTime = datetime.strptime(sTime, '%H:%M')
    else:
      dTime = datetime.strptime(sTime.replace(':.',':00.'), '%H:%M:%S')
  else:
    dTime = datetime.strptime(sTime.replace(':.',':00.'), '%H:%M:%S.%f')
  
  return timedelta(hours=dTime.hour, minutes=dTime.minute, seconds=dTime.second, microseconds=dTime.microsecond)


# Round up a datetime object to next second
def ceilTime(dTime):
  if dTime.microsecond > 0:
    dTime = dTime.replace(second=dTime.second+1, microsecond=0)
  return dTime

# Calculate start time as gpx end-time minus number of hrm values
def startTime(hrm, trkList):
  gpx_time = datetime.strptime(trkList[-1].getElementsByTagName('time')[0].childNodes[0].nodeValue, '%Y-%m-%dT%H:%M:%S.%fZ')
  duration = timedelta(0,len(hrm)-1)
  return gpx_time - duration

xml = minidom.parse('in.xml')
gpx = minidom.parse('in.gpx')

trkList  = gpx.getElementsByTagName('trkpt')

hrm = xml.getElementsByTagName('sample')[0].getElementsByTagName('values')[0].childNodes[0].nodeValue.split(',')
laps = xml.getElementsByTagName('laps')[0].getElementsByTagName('lap')

#print "Time offset: " + str(offset(xml, trkList)) + " s"
start_time = startTime(hrm, trkList) #datetime.strptime(xml.getElementsByTagName('time')[0].firstChild.nodeValue, '%Y-%m-%d %H:%M:%S.0') + timedelta(0,time.altzone+offset(xml,trkList))

time_format = '%Y-%m-%dT%H:%M:%SZ'

out = open('out.tcx','w')

out.write('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n')
out.write('<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd">\n\n')

out.write('  <Activities>\n')
out.write('    <Activity Sport="Running">\n')
out.write('      <Id>' + start_time.strftime(time_format) + '</Id>\n')

lap_time = start_time
count_hrm = 0
count_pos = 0
n_gps = 0

for lap in laps:

  # calculate laptime
  lap_duration = str2timedelta(lap.getElementsByTagName('duration')[0].childNodes[0].nodeValue)
  lap_distance = lap.getElementsByTagName('distance')[0].childNodes[0].nodeValue
  lap_avg_bpm = lap.getElementsByTagName('heart-rate')[0].getElementsByTagName('average')[0].childNodes[0].nodeValue
  lap_max_bpm = lap.getElementsByTagName('heart-rate')[0].getElementsByTagName('maximum')[0].childNodes[0].nodeValue

  out.write('      <Lap StartTime="' + lap_time.strftime(time_format)  + '">\n')
  out.write('        <TotalTimeSeconds>' + str( lap_duration.total_seconds() ) + '</TotalTimeSeconds>\n')
  out.write('        <DistanceMeters>' + lap_distance + '</DistanceMeters>\n')
  out.write('        <AverageHeartRateBpm>\n')
  out.write('          <Value>' + lap_avg_bpm + '</Value>\n')
  out.write('        </AverageHeartRateBpm>\n')
  out.write('        <MaximumHeartRateBpm>\n')
  out.write('          <Value>' + lap_max_bpm + '</Value>\n')
  out.write('        </MaximumHeartRateBpm>\n')
  out.write('        <Track>\n')
  
  time = ceilTime(lap_time)

  while(time < lap_time + lap_duration) and count_hrm < len(hrm) and count_pos < len(trkList):
    out.write('          <Trackpoint>\n')
    out.write('            <Time>' + time.strftime(time_format) + '</Time>\n')
    
    gpx_time = datetime.strptime(trkList[count_pos].getElementsByTagName('time')[0].childNodes[0].nodeValue, '%Y-%m-%dT%H:%M:%S.%fZ')

    if gpx_time == time:
      out.write('            <Position>\n')
      out.write('              <LatitudeDegrees>' +  trkList[count_pos].getAttribute('lat') + '</LatitudeDegrees>\n')
      out.write('              <LongitudeDegrees>' + trkList[count_pos].getAttribute('lon') + '</LongitudeDegrees>\n')
      out.write('            </Position>\n')
      
      count_pos = count_pos + 1
      #print count_pos

    out.write('            <HeartRateBpm>\n')
    out.write('              <Value>' + hrm[count_hrm] + '</Value>\n')
    out.write('            </HeartRateBpm>\n')
    out.write('          </Trackpoint>\n')
   
    time = time + timedelta(0,1)
    count_hrm = count_hrm + 1
    
  out.write('        </Track>\n')
  out.write('      </Lap>\n')

  # Update laptime
  lap_time = lap_time + lap_duration

out.write('    </Activity>\n')
out.write('  </Activities>\n')
out.write('</TrainingCenterDatabase>\n')

out.close()
