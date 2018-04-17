# ###########################
# Etools Locations QC Check
# ###########################

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtCore import QVariant
from datetime import datetime, date, time
import itertools
import collections
import os

print "############################"
print "Etools Locations QC Check"
print "############################"
startDate = datetime.utcnow()
print "Started: {}\n".format(str(startDate))

# input Pcode, Parent Pcode and Name fields for all admin levels
id_field = "id"
pc_field = "p_code"
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
print "Level\tFid\tGateId\tGateName\tFtCount\tNullPcodes\tDuplPcodes\tNullPPcodes\tWrongPPcodes"
cntryflag = 0
errors = []
results = []
nullids = []
pcodes = []
ftsaffected = []
errorCount = 0
qcstatus = ""


def timediff():
	timedif = datetime.utcnow() - timediff.prevDate
	timediff.prevDate = datetime.utcnow()
	return str(timedif.seconds + float(timedif.microseconds) / 1000000)


timediff.prevDate = datetime.utcnow()


for g in gateway_tbl[0].getFeatures():
	expr = QgsExpression("\"gateway_id\"={}".format(g["id"]))
	for ft in loc_lyr[0].getFeatures(QgsFeatureRequest(expr)):
		pcode = str(ft[pc_field]).strip()
		if pcode is not 'NULL' and pcode != '':
			pcodes.append(pcode)
duplpcodes = ["'" + item + "'" for item, count in collections.Counter(pcodes).items() if count > 1]
duplquery = ''

for d in duplpcodes:
	duplquery = ",".join(list(duplpcodes))


for g in gateway_tbl[0].getFeatures():
	expr = QgsExpression("\"gateway_id\"={}".format(g["id"]))
	ftcount = 0
	gateway_ids.append(g["id"])

	null_pcode_ids = []
	null_ppcode_ids = []
	loc_lyr[0].setSelectedFeatures(tempnullids)
	nullids.append([loc_lyr[0].name(), tempnullids])

	for ft in loc_lyr[0].getFeatures(QgsFeatureRequest(expr)):
		pcode = str(ft[pc_field]).strip()
		ppcode = str(ft[ppc_field]).strip()

		if pcode is 'NULL' or pcode =='':
			null_pcode_ids.append(ft.id())
		if ppcode is 'NULL' or ppcode =='':
			null_ppcode_ids.append(ft.id())
		ftcount += 1

	query = '"' + str(pc_field) + '" in (' + str(duplquery) + ')'
	selection = loc_lyr[0].getFeatures(QgsFeatureRequest().setFilterExpression(query))
	selids = [k.id() for k in selection]

	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(l, g.id(), g['id'], g['name'], ftcount, len(list(null_pcode_ids)), len(list(selids)), len(list(null_ppcode_ids)))
	if g["name"] == "Country":
		cntryflag = 1
	l += 1
if cntryflag == 0:
	errors.append("No Country level exists in gateway_id table!")


endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
print "\nQC STATUS:\t{}".format(qcstatus)
