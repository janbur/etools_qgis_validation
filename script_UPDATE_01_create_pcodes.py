# ###########################
# Create Pcodes - Add New Fields, Generate New Pcodes and Assign Parent Pcodes
# ###########################

import sys
import os
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time

print "############################"
print "Create Pcodes - Add New Fields, Generate New Pcodes and Assign Parent Pcodes"
print "############################"
startDate = datetime.utcnow()
print "Started: " + str(startDate) + "\n"

# input new Pcode and Parent Pcode field names for all admin levels
new_fnames = ["admin0Pcod","admin1Pcod","admin2Pcod","admin3Pcod","admin4Pcod"]
new_fpnames = ["admin0Pcod","admin0Pcod","admin1Pcod","admin2Pcod","admin3Pcod"]
country_iso2 = "TN"

ADD_FIELDS = 1 # 1 - add fields, 0 - do not add new fields
GENERATE_PCODES = 1 # 1 - generate new Pcodes, 0 - do not generate new Pcodes
UPDATE_PPCODES = 1 # 1 - update Parent Pcodes, 0 - do not update Parent Pcodes

# set layers
lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() <> "locations_location"]

nullids = []
ftsaffected = []
errorCount = 0
qcstatus = ""
admin_layers = []


# level counter
l = 0

# print input settings
print "Input"
print "Level\tLayer\tDateModif\tPcodeField\tPPcodeField\tCount"
for lyr in lyrs:
	print "{}\t{}\t{}\t{}\t{}\t{}".format(l,lyr.name(),datetime.fromtimestamp(os.path.getmtime(lyr.dataProvider().dataSourceUri().split("|")[0])),new_fnames[l],new_fpnames[l],lyr.featureCount())
	l+=1
print "\nADD_FIELDS: {}".format(ADD_FIELDS)
print "GENERATE_PCODES: {}".format(GENERATE_PCODES)
print "UPDATE_PPCODES: {}".format(UPDATE_PPCODES)

l = 0

for lyr in lyrs:
	caps = lyr.dataProvider().capabilities()
	fnames = []
	admin_layers.append(lyr)
	if ADD_FIELDS == 1 and caps & QgsVectorDataProvider.AddAttributes:
		fields = lyr.dataProvider().fields()
		for field in fields:
			fnames.append(field.name())
		# add pcode field
		if new_fnames[l] in fnames:
			print "Level {} - field {} already exists in {}".format(l, new_fnames[l],lyr.name())
		else:
			lyr.dataProvider().addAttributes([QgsField(new_fnames[l], QVariant.String, len=34)])
			lyr.updateFields()
			print "Level {} - added field {} to {}".format(l, new_fnames[l],lyr.name())
		# add parent pcode field
		if new_fpnames[l] in fnames or l == 0:
			print "Level {} - skip adding field {} to {}".format(l, new_fpnames[l],lyr.name())
		else:
			lyr.dataProvider().addAttributes([QgsField(new_fpnames[l], QVariant.String, len=34)])
			lyr.updateFields()
			print "Level {} - added field {} to {}".format(l, new_fpnames[l],lyr.name())
	new_pcode_fid = lyr.dataProvider().fieldNameIndex(new_fnames[l])
	new_parentcode_fid = lyr.dataProvider().fieldNameIndex(new_fpnames[l])

	lyr.startEditing()
	fts = lyr.getFeatures()
	resetCounter = 0
	if l==0:
		count = lyr.featureCount()
		if count != 1:
			errorCount += 1
			print "{} - only 1 feature on level 0 is allowed".format(l)
		for ft in lyr.getFeatures():
			if GENERATE_PCODES == 1:
				lyr.changeAttributeValue(ft.id(), new_pcode_fid, country_iso2)
				if resetCounter == 0:
					print "Level {} - sample Pcode generated: {}".format(l,country_iso2)
					resetCounter +=1
	else:
		parent_fts = admin_layers[l-1].getFeatures()
		for pft in parent_fts:
			pcode = 1
			for ft in lyr.getFeatures():
				if pft.geometry().contains(ft.geometry().pointOnSurface()):
					ppcodeStr = "{}".format(pft[new_fnames[l-1]])
					pcodeStr = "{}{:03d}".format(ppcodeStr,pcode)
					if GENERATE_PCODES == 1:
						lyr.changeAttributeValue(ft.id(), new_pcode_fid, pcodeStr)
						if resetCounter == 0:
							print "Level {} sample Pcode generated: {}".format(l,pcodeStr)
							resetCounter +=1
						#print "Level {} - fid: {}, pcode generated: {}".format(l, ft.id(),pcodeStr)
						pcode += 1
					if UPDATE_PPCODES == 1:
						lyr.changeAttributeValue(ft.id(), new_parentcode_fid, ppcodeStr)
						#print "Level {} - fid: {}, ppcode assigned: {}".format(l, ft.id(),ppcodeStr)
	lyr.commitChanges()
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
