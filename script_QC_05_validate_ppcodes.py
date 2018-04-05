# ###########################
# Parent Pcodes QC Check
# ###########################

import sys
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time
import os


print "############################"
print "Parent Pcodes QC Check"
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


errors = []
admin_layers = []

errorCount = 0
qcstatus = ""


print "\nDetails"
for lyr in lyrs:
	admin_layers.append(lyr)		
	pcode_fid = lyr.dataProvider().fieldNameIndex(fnames[l])
	parentcode_fid = lyr.dataProvider().fieldNameIndex(fpnames[l])

	fts = admin_layers[l].getFeatures()
	ftsaffected = []
	tempwrongppc = []
	
	if l==0:
		count = len(list(fts))
		if count != 1:
			print lyr.name() + " - only 1 feature on level 0 is allowed"
		for ft in admin_layers[l].getFeatures():
			ftpc = str(ft[fnames[l]]).strip()
			ftppc = str(ft[fpnames[l]]).strip()
			if ftpc is 'NULL' or ftpc =='':
				errorCount += 1
				print "ERROR - Empty pcode at level 0"
	else:
		pfts = admin_layers[l-1].getFeatures()
		
		for ft in admin_layers[l].getFeatures():
			ft_centr = ft.geometry().pointOnSurface()
			ftpc = str(ft[fnames[l]]).strip()
			ftppc = str(ft[fpnames[l]]).strip()
			for pft in admin_layers[l-1].getFeatures():
				pft_geom = pft.geometry()
				if ft_centr.intersects(pft_geom) == True:
					pftn = str(pft[fnames[l-1]])
					if ftppc != pftn:
						errorCount += 1
						print "Level: " + str(l) + ", pcode=" + ftpc + ", fid = " + str(ft.id()) + " has parent pcode: " + ftppc + ". Correct pcode is: " + pftn
						tempwrongppc.append(ftppc)
						ftsaffected.append(ft.id())
		errors.append([lyr.name(), tempwrongppc])
		lyr.setSelectedFeatures(ftsaffected)
	l = l+1

print "\nSummary"
print "\nLayer\tCountErrors\tWrongParentPcodes"
for i in errors:
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
