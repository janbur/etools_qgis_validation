# ###########################
# QC DUPLICATE PCODES
# ###########################

import sys
from qgis.core import *
from PyQt4.QtCore import *
import collections
from datetime import datetime, date, time

print "############################"
print "QC DUPLICATE PCODES"
print "############################"
startDate = datetime.utcnow()
print "Started: " + str(startDate) + "\n"

# input Pcode and Parent Pcode field names for all admin levels
fnames = ["admin0Pcod","admin1Pcod","admin2Pcod","admin3Pcod"]
fpnames = ["admin0Pcod","admin0Pcod","admin1Pcod","admin2Pcod"]

# set layers
lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() <> "locations_location"]



pcodes = []
duplids = []
duplpcodes = []

errorCount = 0
qcstatus = ""

# level counter
l = 0

# print input settings
print "INPUT"
print "Level\tLayer\tDateModif\tPcodeField\tPPcodeField\tCount"
for lyr in lyrs:
	print "{}\t{}\t{}\t{}\t{}\t{}".format(l,lyr.name(),datetime.fromtimestamp(os.path.getmtime(lyr.dataProvider().dataSourceUri().split("|")[0])),fnames[l],fpnames[l],lyr.featureCount())
	l+=1
l = 0

for lyr in lyrs:
	fts = lyr.getFeatures()
	# check pcodes
	for ft in fts:
		ftn = str(ft[fnames[l]]).strip()
		if ftn is not 'NULL':
			pcodes.append(ftn)
	l += 1
duplpcodes = ["'" + item + "'" for item, count in collections.Counter(pcodes).items() if count > 1]
duplquery = ''

for d in duplpcodes:
	duplquery = ",".join(list(duplpcodes))

duplpcodesperlyr = []
ftsaffected = []
l = 0

print "\nDETAILS"

for lyr in lyrs:
	tempduplpcodes = []
	tempduplpcodesids = []
	
	query = '"' + str(fnames[l]) + '" in (' + str(duplquery) + ')'
	selection = lyr.getFeatures(QgsFeatureRequest().setFilterExpression(query))
	selids = [k.id() for k in selection]
	lyr.setSelectedFeatures(selids)
	selection = lyr.getFeatures(QgsFeatureRequest().setFilterExpression(query))
	for ft in selection:
		ftpc = str(ft[fnames[l]]).strip()
		ftsaffected.append(ft)
		tempduplpcodes.append(ftpc)
		print "Level {} - feature {} has duplicate Pcode: {}".format(l,ft.id(),ftpc)
		errorCount += 1
	duplpcodesperlyr.append([lyr.name(), tempduplpcodes])
	l += 1

print "\nSUMMARY"

print "\nLayer\tFeaturesAffected\tDuplPcodes"
for i in duplpcodesperlyr:
	print i[0] + "\t" + str(len(list(i[1]))) + "\t" + str(list(i[1]))

print "\nDuplicated Pcodes: " + str(duplpcodes)
print "\nTotal Number of duplicated pcodes: " + str(len(list(duplpcodes)))
print "Total Number of features affected: " + str(len(list(ftsaffected)))

# update QC status
if errorCount == 0:
	qcstatus = "OK"
else:
	qcstatus = "MANUAL CHECK REQUIRED"

endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
print "\nQC STATUS:\t{}".format(qcstatus)
