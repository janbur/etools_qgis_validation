# ###########################
# SCRIPT 00-A - VALIDATE GEOMETRIES
# ###########################

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtCore import QVariant
from datetime import datetime, date, time
import itertools
import os

print "############################"
print "GEOMETRY QC"
print "############################"
startDate = datetime.utcnow()
print "Started: " + str(startDate) + "\n"

# input Pcode and Parent Pcode field names for all admin levels
fnames = ["admin0Pcod","admin1Pcod","admin2Pcod"]
fpnames = ["admin0Pcod","admin0Pcod","admin1Pcod"]

# set layers
lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() <> "locations_location"]

# threshold size for intersections
thres = 0.0000001

# level counter
l = 0

# print input settings
print "INPUT"
print "Level\tLayer\tDateModif\tPcodeField\tPPcodeField\tCount"
for lyr in lyrs:
	print "{}\t{}\t{}\t{}".format(l,lyr.name(),datetime.fromtimestamp(os.path.getmtime(lyr.dataProvider().dataSourceUri().split("|")[0])),fnames[l],fpnames[l],lyr.featureCount())
	l+=1
l = 0

print "Threshold size for intersections: {}".format(thres)
	
def timeDiff():
	timedif = datetime.utcnow() - timeDiff.prevDate
	timeDiff.prevDate = datetime.utcnow()
	return str(timedif.seconds + float(timedif.microseconds)/1000000)

timeDiff.prevDate = datetime.utcnow()

# Loop all layers
l = 0

results = []
errorCount = 0
qcstatus = ""

print "\nRESULTS"
for lyr in lyrs:
	print "\nAnalysing Level {}".format(l)
	geomerrors = []
	# create a memory layer for intersections
	mem_layer = QgsVectorLayer("MultiPolygon?crs=epsg:4326", "{}_overlaps".format(lyr.name()), "memory")
	mem_layer.startEditing()
	pr = mem_layer.dataProvider()
	pr.addAttributes([QgsField("lyrid",  QVariant.String), QgsField("fid1",  QVariant.Int), QgsField("fid2",  QVariant.Int)])

	# prepare a loop on the input layer
	polygons = []
	for feature in lyr.getFeatures():
		geom = feature.geometry()
		if geom:
			err = geom.validateGeometry()
			if not err:
				polygons.append(feature)
			else:
				polygons.append(feature)
				geomerrors.append([err, feature.id()])
				errorCount += 1
				for er in err:
					print "\t{}".format(er.what())
	lyr.setSelectedFeatures([g[1] for g in geomerrors])
	counter = 1
	overlaps = []
	combCount = len(list(itertools.combinations(polygons,2)))
	for feature1,feature2 in itertools.combinations(polygons, 2):
		if feature1.geometry().intersects(feature2.geometry()):
			geom = feature1.geometry().intersection(feature2.geometry())
			if geom.area() > thres:
				print "\t {}% - {} is intersecting with {} (area: {})".format(str(round((float(counter) / combCount) * 100,2)), feature1.id(), feature2.id(), geom.area())
				feature = QgsFeature()
				fields = mem_layer.pendingFields()
				feature.setFields(fields, True)
				feature.setAttributes([lyr.name(), feature1.id(), feature2.id()])
				feature.setGeometry(geom)
				pr.addFeatures([feature])
				mem_layer.updateExtents()
				mem_layer.commitChanges
				overlaps.append([feature1.id(), feature2.id()])
				errorCount += 1
		counter += 1
	
	mem_layer.commitChanges()
	if len(list(overlaps)) > 0:
		QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
	results.append([geomerrors,overlaps])
	l += 1
l=0

print "\nSUMMARY"
print "\nLevel\tGeomErrors\tIntersections"
for r in results:
	print "{}\t{}\t{}".format(l, len(r[0]), len(r[1]))
	l += 1

# update QC status
if errorCount == 0:
	qcstatus = "OK"
else:
	qcstatus = "MANUAL CHECK REQUIRED"

endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
print "\nQC STATUS:\t{}".format(qcstatus)
