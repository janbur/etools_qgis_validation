# ###########################
# Etools Locations QC Check
# ###########################

import itertools
import collections
import os
import qgis.core
from PyQt4.QtCore import QVariant
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from datetime import datetime
from shapely.geometry.multipolygon import MultiPolygon
from shapely import wkt


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

gateway_ids = [[1, "Province"], [2, "Cape Town"]]
country = "South Africa"
outdir = r"C:\Users\GIS\Documents\____UNICEF_ETOOLS\04_Data\00_UPDATE\South Africa"
# gateway_ids = [[1, "Country"], [4, "Province"], [3, "District"]]
# country = "Kyrgyzstan"
# outdir = r"C:\Users\GIS\Documents\____UNICEF_ETOOLS\04_Data\00_UPDATE\Kyrgyzstan"
#gateway_ids = [[4, "Country"], [1, "District"], [3, "Division"]]
#country = "Kenya"
#outdir = r"C:\Users\GIS\Documents\____UNICEF_ETOOLS\04_Data\00_UPDATE\Kenya"

null_pcode_qc = 1
dupl_pcode_qc = 1
null_ppcode_qc = 1
parent_qc = 1
geom_qc = 0

# set layers
loc_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == "locations_location"]
lyrsids = [i.id() for i in loc_lyr]

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
print "gateway ids:\t:{}".format(gateway_ids)
print "Threshold size for intersections: {}".format(thres)

cntryflag = 0
pcodes = []
qcstatus = ""

null_pcode_errors = []
dupl_pcode_errors = []
null_ppcode_errors = []
parent_errors = []
geom_errors = []
overlap_errors = []

results = []


def timediff():
	timedif = datetime.utcnow() - timediff.prevDate
	timediff.prevDate = datetime.utcnow()
	return str(timedif.seconds + float(timedif.microseconds) / 1000000)


timediff.prevDate = datetime.utcnow()

# set up image renderer
img = QImage(QSize(600, 600), QImage.Format_ARGB32_Premultiplied)

# set image's background color
color = QColor(255, 255, 255)
img.fill(color.rgb())

render = QgsMapRenderer()
render.setLayerSet(lyrsids)

# set extent
rect = QgsRectangle(render.fullExtent())
rect.scale(1.1)
render.setExtent(rect)

polygons = []

# initial loop to get pcodes and polygons per layer
for g in gateway_ids:
	# flag if Country
	if g[1] == "Country":
		cntryflag = 1
	# filter locations by gateway id
	loc_lyr[0].setSubsetString("\"gateway_id\"={}".format(g[0]))
	temp_polygons = []

	for ft in loc_lyr[0].getFeatures():
		# record pcode
		pcode = str(ft[pc_field]).strip()
		if pcode is not 'NULL' and pcode != '':
			pcodes.append(pcode)

		# add polygon to list
		geom = ft.geometry()
		if geom:
			temp_polygons.append(ft)
	polygons.append(temp_polygons)

	lst = []
	lst.append(loc_lyr[0].id())
	render.setLayerSet(lst)

	render.setOutputSize(img.size(), img.logicalDpiX())
	# create painter
	p = QPainter()
	p.begin(img)
	p.setRenderHint(QPainter.Antialiasing)

	# do the rendering
	render.render(p)

	p.end()

	if not os.path.exists(outdir):
		os.makedirs(outdir)
	filename = "{}_adm-{}_{}.png".format(country, l, '{0:%Y}{0:%m}{0:%d}'.format(datetime.utcnow()))
	path = os.path.join(outdir, filename)

	# save image
	b = img.save(path, "png")
	# print "Snapshot for level {} created at {}".format(l, path)
	l += 1

l = 0

# reset query filter
loc_lyr[0].setSubsetString('')

# list duplicated pcodes
duplpcodes = ["'" + item + "'" for item, count in collections.Counter(pcodes).items() if count > 1]
duplquery = ''

for d in duplpcodes:
	duplquery = ",".join(list(duplpcodes))

# main loop for all levels / gateway ids
for g in gateway_ids:

	# set error counters for each admin level
	null_pcode_errors_level_count = 0
	dupl_pcode_errors_level_count = 0
	null_ppcode_errors_level_count = 0
	parent_errors_level_count = 0
	geom_errors_level_count = 0
	overlap_errors_level_count = 0

	expr = QgsExpression("\"gateway_id\"={}".format(g[0]))
	fts = loc_lyr[0].getFeatures(QgsFeatureRequest(expr))
	ftcount = 0

	# Geometry QC Check setup
	# create a memory layer for intersections
	mem_layer = QgsVectorLayer("MultiPolygon?crs=epsg:4326", "location_locations_overlaps", "memory")
	mem_layer.startEditing()
	pr = mem_layer.dataProvider()
	pr.addAttributes(
		[QgsField("lyrid", QVariant.String), QgsField("fid1", QVariant.Int), QgsField("fid2", QVariant.Int)])

	# calculate combinations
	combinations = itertools.combinations(polygons[l], 2)
	combCount = len(list(combinations))
	print combCount

	for ft in fts:
		# Null Pcode QC Check
		pcode = str(ft[pc_field]).strip()
		if pcode is 'NULL' or pcode == '':
			null_pcode_errors.append([l, ft])
			null_pcode_errors_level_count += 1

		# Null Parent Pcode QC Check
		ppcode = str(ft[pid_field]).strip()
		if (ppcode is 'NULL' or ppcode =='') and g[1] != "Country":
			null_ppcode_errors.append([l, ft])
			null_ppcode_errors_level_count += 1
		ftcount += 1

		ftgeom = ft.geometry()
		ftid = str(ft[id_field]).strip()
		ftpc = str(ft[pc_field]).strip()
		ftpid = str(ft[pid_field]).strip()
		ftn = str(ft[name_field]).strip()

		if ftgeom:
			# Geometry QC Check setup
			if geom_qc == 1:
				for feature1, feature2 in combinations:
					if feature1.geometry().intersects(feature2.geometry()):
						geom = feature1.geometry().intersection(feature2.geometry())
						if ftgeom and ftgeom.area() > thres:
							print "ABOVE THRES: {}".format(ftgeom.area())
							feature = QgsFeature()
							fields = mem_layer.pendingFields()
							feature.setFields(fields, True)
							feature.setAttributes([0, feature1.id(), feature2.id()])
							if ftgeom.wkbType() == 7:
								geom_col = ftgeom.asGeometryCollection()
								geom_col_wkt = [wkt.loads(sing_g.exportToWkt()) for sing_g in geom_col if
												sing_g.type() == 2]
								mp = MultiPolygon(geom_col_wkt)
								feature.setGeometry(QgsGeometry.fromWkt(mp.wkt))
							else:
								feature.setGeometry(ftgeom)
							pr.addFeatures([feature])
							mem_layer.updateExtents()
							mem_layer.commitChanges()
							overlap_errors.append([l, feature1, feature2, ftgeom])
							overlap_errors_level_count += 1

				mem_layer.commitChanges()
				if overlap_errors_level_count > 0:
					QgsMapLayerRegistry.instance().addMapLayer(mem_layer)

			# Parent Pcodes QC Check
			if g[1] != "Country" and parent_qc == 1:
				ft_centr = ftgeom.pointOnSurface()
				expr_prev = QgsExpression("\"gateway_id\"={}".format(gateway_ids[l - 1][0])) # will not work if no country level available!!! l - need to change
				pfts = loc_lyr[0].getFeatures(QgsFeatureRequest(expr_prev))
				# print "{}-{}-{}-{}-{}-{}-exp:{}-Pcount:{}".format(ftid,ftpc,ftpid,ftn,l,g[0],"\"gateway_id\"={}".format(gateway_ids[l - 1][0]),len(list(pfts)))

				for pft in pfts:
					pft_geom = pft.geometry()
					pftid = str(pft[id_field]).strip()
					pftpc = str(pft[pc_field]).strip()
					pftn = str(pft[name_field]).strip()
					if pft_geom:
						if ft_centr.intersects(pft_geom):
							if ftpid != pftid:
								parent_errors.append([l, g[1], ftid, ftpc, ftn, ftpid, pftid, pftpc, pftn])
								parent_errors_level_count += 1
					else:
						parent_errors.append([l, g[1], ftid, ftpc, ftn, ftpid, pftid, pftpc, pftn])
						parent_errors_level_count += 1
		else:
			geom_errors.append([l, "empty / invalid geometry", ft.id()])
			geom_errors_level_count += 1

	# Duplicated Pcode QC Check
	query = '"' + str(pc_field) + '" in (' + str(duplquery) + ')'
	selection = loc_lyr[0].getFeatures(QgsFeatureRequest().setFilterExpression(query))
	dupl_pcode_errors_level_count = len(list([k.id() for k in selection]))
	dupl_pcode_errors.append([l, dupl_pcode_errors_level_count, [k.id() for k in selection]])

	# Count errors and QC status
	total_errors = overlap_errors_level_count + null_pcode_errors_level_count + dupl_pcode_errors_level_count + null_ppcode_errors_level_count + parent_errors_level_count
	status = ""
	if total_errors == 0:
		status = "OK"
	else:
		if null_ppcode_errors_level_count == 1 and l == 0:
			status = "OK"
		else:
			status = "CHECK"

	# print layer summary
	results.append([l, g[0], g[1], ftcount, overlap_errors_level_count, null_pcode_errors_level_count, dupl_pcode_errors_level_count, null_ppcode_errors_level_count, parent_errors_level_count, status])
	l += 1


print "\nNull Pcodes QC Check"
if len(list(null_pcode_errors)) > 0:
	print "Level\tFid\tFName"
	for e in null_pcode_errors:
		print "{}\t{}\t{}".format(e[0], e[1][id_field], e[1][name_field])
else:
	print "OK"

print "\nDuplicate Pcodes QC Check"
dupl_err_sum = sum([e[1] for e in dupl_pcode_errors])
if dupl_err_sum > 0:
	print "Level\tCount\tFids"
	for e in dupl_pcode_errors:
		print "{}\t{}".format(e[0], e[1], e[2])
else:
	print "OK"

print "\nNull Parent Pcodes QC Check"
if len(list(null_ppcode_errors)) > 0:
	print "Level\tFid\tFName"
	for e in null_ppcode_errors:
		print "{}\t{}\t{}".format(e[0], e[1][id_field], e[1][name_field])
else:
	print "OK"


print "\nParent Pcodes QC Check"
if len(list(parent_errors)) > 0:
	print "Level\tLevelName\tFid\tFPcode\tFName\tWrongParentID\tCorrectParentID\tCorrectParentPcode\tCorrectParentName"
	for e in parent_errors:
		print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8])
else:
	print "OK"

print "\nOther QC check:"
if cntryflag == 0:
	print "ERROR - No Country level exists in gateway_id table!"
else:
	print "OK"


print "\nLocations Summary"
print "Level\tGateId\tGateName\tFtCount\tOverlaps\tNullPcodes\tDuplPcodes\tNullPPcodes\tWrongPPcodes\tStatus"
for r in results:
	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9])

endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
