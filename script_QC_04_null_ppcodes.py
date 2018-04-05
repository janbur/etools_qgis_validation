# ###########################
# Null Parent Pcodes QC Check
# ###########################

import sys
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time

print "############################"
print "Null Parent Pcodes QC Check"
print "############################"
startDate = datetime.utcnow()
print "Started: " + str(startDate) + "\n"

# input Pcode and Parent Pcode field names for all admin levels
fnames = ["admin0Pcod","admin1Pcod","admin2Pcod","admin3Pcod"]
fpnames = ["admin0Pcod","admin0Pcod","admin1Pcod","admin2Pcod"]

# set layers
lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() <> "locations_location"]

# level counter
l = 0

# print input settings
print "Input"
print "Level\tLayer\tDateModif\tPcodeField\tPPcodeField\tCount"
for lyr in lyrs:
	print "{}\t{}\t{}\t{}\t{}\t{}".format(l,lyr.name(),datetime.fromtimestamp(os.path.getmtime(lyr.dataProvider().dataSourceUri().split("|")[0])),fnames[l],fpnames[l],lyr.featureCount())
	l+=1
l = 0


nullids = []
ftsaffected = []

errorCount = 0
qcstatus = ""

l = 0

print "\nDetails"
for lyr in lyrs:
	if l>0:
		fts = lyr.getFeatures()
		tempnullids = []
		for ft in fts:
			ftppc = str(ft[fpnames[l]]).strip()
			if ftppc is 'NULL' or ftppc =='':
				tempnullids.append(ft.id())
				ftsaffected.append(ft)
				print "Level {} - feature {} has null Parent Pcode: {}".format(l,ft.id(),ftppc)	
				errorCount += 1
		lyr.setSelectedFeatures(tempnullids)
		nullids.append([lyr.name(), tempnullids])
	l += 1

print "\nSummary"
print "\nNumber of features with empty parent pcodes:\t" + str(len(list(ftsaffected)))
print "\nLayer\tCountFeaturesWithEmptyPPcodes\tFeaturesIds"

for i in nullids:
	print i[0] + "\t" + str(len(list(i[1]))) + "\t" + str(list(i[1]))


# update QC status
if errorCount == 0:
	qcstatus = "OK"
else:
	qcstatus = "MANUAL CHECK REQUIRED"

endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
print "\nQC STATUS:\t{}".format(qcstatus)
