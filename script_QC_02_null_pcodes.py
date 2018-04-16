# ###########################
# Null Pcodes QC Check
# ###########################

import sys
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time

print "############################"
print "Null Pcodes QC Check"
print "############################"
startDate = datetime.utcnow()
print "Started: " + str(startDate) + "\n"

# input Pcode, Parent Pcode and Name fields for all admin levels
pc_fields = ["HRpcode", "HRpcode", "HRpcode"]
ppc_fields = ["HRparent", "HRparent", "HRparent"]
name_fields = ["HRname", "HRname", "HRname"]

# set layers
lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() != "locations_location"]

nullids = []
ftsaffected = []
errorCount = 0
qcstatus = ""


# level counter
l = 0

# print input settings
print "Input"
print "Level\tLayer\tDateModif\tPcodeField\tPPcodeField\tCount"
for lyr in lyrs:
	print "{}\t{}\t{}\t{}\t{}\t{}".format(l,lyr.name(),datetime.fromtimestamp(os.path.getmtime(lyr.dataProvider().dataSourceUri().split("|")[0])),pc_fields[l],ppc_fields[l],lyr.featureCount())
	l+=1
l = 0

print "\nDetails"
for lyr in lyrs:
	fts = lyr.getFeatures()
	# check pcodes
	tempnullids = []
	for ft in fts:
		ftn = str(ft[pc_fields[l]]).strip()
		if ftn is 'NULL' or ftn =='':
			tempnullids.append(ft.id())
			ftsaffected.append(ft)
			print "Level {} - feature {} has null Pcode".format(l,ft.id())
			errorCount += 1
	lyr.setSelectedFeatures(tempnullids)
	nullids.append([lyr.name(), tempnullids])
	l += 1
	
print "\nSummary"
print "\nNumber of features with empty pcodes:\t" + str(len(list(ftsaffected)))
print "\nLayer\tCountFeaturesWithEmptyPcodes\tFeaturesIds"

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
