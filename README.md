# Polar2Tcx [![Build Status](https://travis-ci.org/marthinsen/polar2tcx.svg?branch=master)](https://travis-ci.org/marthinsen/polar2tcx)

Polar2Tcx lets you convert and merge proprietary Polar XML/GPX files from
www.polarpersonaltrainer.com into TCX files that can be uploaded to strava.com
for instance. Polar2Tcx is for personal use only and has a lot of limitations.

## Installation
Installation is not required, but is done like this

```
$ python setup.py install
```

## Usage
1. Export Polar training data from polarpersonaltrainer.com (XML, GPX or both)
2. Run polar2tcx.py as follows:
   ```
   $ polar2tcx.py -x polar.xml -g polar.gpx -o out.xml
   ```
3. Upload the file out.xml to Strava (possibly by using
   [stravaupload](https://github.com/marthinsen/stravaupload))
4. Enjoy

Call Polar2tcx with -h or --help in order to show a detailed help on all
available command line arguments.
