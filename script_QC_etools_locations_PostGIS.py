# ###########################
# Etools Locations QC Check
# ###########################

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtCore import QVariant
from datetime import datetime, date, time
import itertools
import os

print "############################"
print "Etools Locations QC Check"
print "############################"
startDate = datetime.utcnow()
print "Started: {}\n".format(str(startDate))

# input Pcode, Parent Pcode and Name fields for all admin levels
id_field = "id"
pc_field = "pcode"
ppc_field = "parent_id"
name_field = "name"
gateway_ids = []

# set layers
loc_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == "locations_location"]
gateway_tbl = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == "locations_gatewaytype"]

# threshold size for intersections
thres = 0.0000001

# level counter
l = 0

# print input settings
print "Input"

print "\nFields used"
print "id:\t{}".format(id_field)
print "pcode:\t{}".format(pc_field)
print "parent pcode:\t{}".format(ppc_field)
print "namepcode:\t{}".format(name_field)
print "Threshold size for intersections: {}".format(thres)

print "\nGateway ids"
print "Fid\tId\tName"
cntryflag = 0
errors = []
results = []
errorCount = 0
qcstatus = ""


def timediff():
	timedif = datetime.utcnow() - timediff.prevDate
	timediff.prevDate = datetime.utcnow()
	return str(timedif.seconds + float(timedif.microseconds) / 1000000)


timediff.prevDate = datetime.utcnow()


def geom_qc(l, fts):
	print "\nAnalysing Level {}".format(l)
	geomerrors = []
	geomerrorcount = 0
	# create a memory layer for intersections
	mem_layer = QgsVectorLayer("MultiPolygon?crs=epsg:4326", "locations_overlaps", "memory")
	mem_layer.startEditing()
	pr = mem_layer.dataProvider()
	pr.addAttributes(
		[QgsField("lyrid", QVariant.String), QgsField("fid1", QVariant.Int), QgsField("fid2", QVariant.Int)])

	# prepare a loop on the input layer
	polygons = []
	for feature in fts:
		print feature.id()
		geom = feature.geometry()
		if geom:
			err = geom.validateGeometry()
			if not err:
				polygons.append(feature)
			else:
				polygons.append(feature)
				geomerrors.append([err, feature.id()])
				geomerrorcount += 1
				for er in err:
					print "\t{}".format(er.what())
	#lyr.setSelectedFeatures([g[1] for g in geomerrors])
	counter = 1
	overlaps = []
	combCount = len(list(itertools.combinations(polygons, 2)))
	print combCount
	for feature1, feature2 in itertools.combinations(polygons, 2):
		if feature1.geometry().intersects(feature2.geometry()):
			geom = feature1.geometry().intersection(feature2.geometry())
			if geom.area() > thres:
				print "\t {}% - {} is intersecting with {} (area: {}, {}%)".format(
					str(round((float(counter) / combCount) * 100, 2)), feature1.id(), feature2.id(), geom.area(),
					feature1.geometry().area() / geom.area() * 100)
				feature = QgsFeature()
				fields = mem_layer.pendingFields()
				feature.setFields(fields, True)
				feature.setAttributes([l, feature1.id(), feature2.id()])
				feature.setGeometry(geom)
				pr.addFeatures([feature])
				mem_layer.updateExtents()
				mem_layer.commitChanges
				overlaps.append([feature1.id(), feature2.id()])
				geomerrorcount += 1
		counter += 1

	mem_layer.commitChanges()
	if len(list(overlaps)) > 0:
		QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
	results.append([geomerrors, overlaps])


for g in gateway_tbl[0].getFeatures():
	expr = QgsExpression("\"gateway_id\"={}".format(g["id"]))
	ftcount = 0
	gateway_ids.append(g["id"])
	geom_qc(l, loc_lyr[0].getFeatures(QgsFeatureRequest(expr)))
	for ft in loc_lyr[0].getFeatures(QgsFeatureRequest(expr)):
		ftcount += 1
	print "{}\t{}\t{}\t{}".format(g.id(), g['id'], g['name'], ftcount)
	if g["name"] == "Country":
		cntryflag = 1
	l += 1
if cntryflag == 0:
	errors.append("No Country level exists in gateway_id table!")

print "\nGeometry QC Check Details"



print "\nSummary"
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
