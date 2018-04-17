# ###########################
# Etools Locations QC Check
# ###########################

import itertools
import collections
import os
from qgis.core import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtCore import QVariant
from datetime import datetime, date, time

print "############################"
print "Etools Locations QC Check"
print "############################"
startDate = datetime.utcnow()
print "Started: {}\n".format(str(startDate))

# input Pcode, Parent Pcode and Name fields for all admin levels
id_field = "id"
pc_field = "p_code"
pid_field = "parent_id"
name_field = "name"
gateway_ids = [[1, "Country"], [4, "Province"], [3, "District"]]

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
print "parent id:\t{}".format(pid_field)
print "namepcode:\t{}".format(name_field)
print "Threshold size for intersections: {}".format(thres)

print "\nLocations Summary"
print "Level\tFid\tGateId\tGateName\tFtCount\tNullPcodes\tDuplPcodes\tNullPPcodes\tWrongPPcodes\tStatus"
cntryflag = 0
errors = []
results = []
pcodes = []
ftsaffected = []
errorCount = 0
qcstatus = ""

parent_errors = []


def timediff():
	timedif = datetime.utcnow() - timediff.prevDate
	timediff.prevDate = datetime.utcnow()
	return str(timedif.seconds + float(timedif.microseconds) / 1000000)


timediff.prevDate = datetime.utcnow()


for g in gateway_ids:
	# flag if Country
	if g[1] == "Country":
		cntryflag = 1

	# filter locations by gateway id
	expr = QgsExpression("\"gateway_id\"={}".format(g[0]))
	for ft in loc_lyr[0].getFeatures(QgsFeatureRequest(expr)):
		pcode = str(ft[pc_field]).strip()
		if pcode is not 'NULL' and pcode != '':
			pcodes.append(pcode)

# list duplicated pcodes
duplpcodes = ["'" + item + "'" for item, count in collections.Counter(pcodes).items() if count > 1]
duplquery = ''

for d in duplpcodes:
	duplquery = ",".join(list(duplpcodes))

# main loop for all levels / gateway ids
for g in gateway_ids:
	expr = QgsExpression("\"gateway_id\"={}".format(g[0]))
	fts = loc_lyr[0].getFeatures(QgsFeatureRequest(expr))
	ftcount = 0

	null_pcode_ids = []
	null_ppcode_ids = []

	pcode_fid = loc_lyr[0].dataProvider().fieldNameIndex(pc_field)
	parentid_fid = loc_lyr[0].dataProvider().fieldNameIndex(pid_field)
	ftsaffected = []
	tempwrongppc = []
	parent_errors_count = 0


	for ft in fts:
		# Null Pcode QC Check
		pcode = str(ft[pc_field]).strip()
		if pcode is 'NULL' or pcode =='':
			null_pcode_ids.append(ft.id())

		# Null Parent Pcode QC Check
		ppcode = str(ft[pid_field]).strip()
		if ppcode is 'NULL' or ppcode =='':
			null_ppcode_ids.append(ft.id())
		ftcount += 1

		# Parent Pcodes QC Check
		if g[0] != gateway_ids[0][0]:
			ft_centr = ft.geometry().pointOnSurface()
			ftid = str(ft[id_field]).strip()
			ftpc = str(ft[pc_field]).strip()
			ftpid = str(ft[pid_field]).strip()
			ftn = str(ft[name_field]).strip()

			expr_prev = QgsExpression("\"gateway_id\"={}".format(gateway_ids[l - 1][0]))
			pfts = loc_lyr[0].getFeatures(QgsFeatureRequest(expr_prev))

			for pft in pfts:
				pft_geom = pft.geometry()
				if ft_centr.intersects(pft_geom):
					pftid = str(pft[id_field]).strip()
					pftpc = str(pft[pc_field]).strip()
					pftn = str(pft[name_field]).strip()
					if ftpid != pftid:
						parent_errors_count += 1
						parent_errors.append([l, g[1], ftid, ftpc, ftn, ftpid, pftid, pftpc, pftn])

	# Duplicated Pcode QC Check
	query = '"' + str(pc_field) + '" in (' + str(duplquery) + ')'
	selection = loc_lyr[0].getFeatures(QgsFeatureRequest().setFilterExpression(query))
	dupl_pcode_ids = [k.id() for k in selection]

	# Count errors and QC status
	null_pcode_count = len(list(null_pcode_ids))
	dupl_pcode_count = len(list(dupl_pcode_ids))
	null_ppcode_count = len(list(null_ppcode_ids))
	total_errors = null_pcode_count + dupl_pcode_count + null_ppcode_count + parent_errors_count
	status = ""
	if total_errors == 0:
		status = "OK"
	else:
		if null_ppcode_count == 1 and l == 0:
			status = "OK"
		else:
			status = "CHECK"

	# print layer summary
	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(l, g[0], g[0], g[1], ftcount, null_pcode_count, dupl_pcode_count, null_ppcode_count, parent_errors_count,status)
	l += 1

print "\nGlobal errors:"
if cntryflag == 0:
	print "ERROR - No Country level exists in gateway_id table!"
else:
	print "OK - No global errors."

print "\nParent Pcodes QC Check"
if len(list(parent_errors)) > 0:
	print "Level\tLevelName\tFid\tFPcode\tFName\tWrongParentID\tCorrectParentID\tCorrectParentPcode\tCorrectParentName"
	for e in parent_errors:
		print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(e[0],e[1],e[2],e[3],e[4],e[5],e[6],e[7],e[8])

endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)