# ###########################
# New Locations QC Check
# ###########################
# Note: layers need to be sorted in TOC from country level to lower levels

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
print "New Locations QC Check"
print "############################"
startDate = datetime.utcnow()
print "Started: {}\n".format(str(startDate))


# input Pcode, Parent Pcode and Name fields for all admin levels
#adm_levels = [["Country","HRpcode", "null"], ["Region", "HRpcode", "HRparent"], ["District", "HRpcode", "HRparent"]]
adm_levels = [["Country", "admin0Pcod", "null", "COUNTRY"], ["Region", "admin1Pcod", "admin0Pcod", "ADMIN2"], ["District", "admin2Pcod", "admin1Pcod", "ADMIN3"]]
country = "Djibouti"

# set layers
lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() != "locations_location"]
lyrsids = [i.id() for i in lyrs]

# threshold size for intersections
thres = 0.0000001

# level counter
l = 0

# print input settings
print "Input"
print "Level\tLayer\tDateModif\tPcodeField\tPPcodeField\tCount"
for lyr in lyrs:
	print "{}\t{}\t{}\t{}\t{}\t{}".format(l, lyr.name(), datetime.fromtimestamp(os.path.getmtime(lyr.dataProvider().dataSourceUri().split("|")[0])), adm_levels[l][1],adm_levels[l][2],lyr.featureCount())
	l+=1
l = 0

cntryflag = 0
pcodes = []
qcstatus = ""

admin_layers = []

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

# initial loop to get pcodes
for lyr in lyrs:
	admin_layers.append(lyr)
	fts = lyr.getFeatures()
	# check pcodes
	for ft in fts:
		ftpc = str(ft[adm_levels[l][1]]).strip()
		if ftpc is not 'NULL':
			pcodes.append(ftpc)

	lst = []
	lst.append(lyr.id())
	render.setLayerSet(lst)

	render.setOutputSize(img.size(), img.logicalDpiX())
	# create painter
	p = QPainter()
	p.begin(img)
	p.setRenderHint(QPainter.Antialiasing)

	# do the rendering
	render.render(p)

	p.end()

	outdir = os.path.join(os.path.dirname(os.path.dirname(lyr.dataProvider().dataSourceUri())), "PNG")
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	filename = "{}_adm-{}_{}.png".format(lyr.name(), l, '{0:%Y}{0:%m}{0:%d}'.format(datetime.utcnow()))
	path = os.path.join(outdir, filename)

	# save image
	b = img.save(path, "png")
	# print "Snapshot for level {} created at {}".format(l, path)
	l += 1

duplpcodes = ["'" + item + "'" for item, count in collections.Counter(pcodes).items() if count > 1]
duplquery = ''

for d in duplpcodes:
	duplquery = ",".join(list(duplpcodes))

duplpcodesperlyr = []
ftsaffected = []
l = 0


# main loop for all levels / gateway ids
for lyr in lyrs:

	# set error counters for each admin level
	null_pcode_errors_level_count = 0
	dupl_pcode_errors_level_count = 0
	null_ppcode_errors_level_count = 0
	parent_errors_level_count = 0
	geom_errors_level_count = 0
	overlap_errors_level_count = 0

	fts = lyr.getFeatures()
	ftcount = 0  # XXX

	# Geometry QC Check setup
	# create a memory layer for intersections
	mem_layer = QgsVectorLayer("MultiPolygon?crs=epsg:4326", "location_locations_overlaps", "memory")
	mem_layer.startEditing()
	pr = mem_layer.dataProvider()
	pr.addAttributes(
		[QgsField("lyrid", QVariant.String), QgsField("fid1", QVariant.Int), QgsField("fid2", QVariant.Int)])
	polygons = []

	for ft in fts:
		# Null Pcode QC Check
		pcode = str(ft[adm_levels[l][1]]).strip()
		if pcode is 'NULL' or pcode == '':
			null_pcode_errors.append([l, ft])
			null_pcode_errors_level_count += 1

		# Null Parent Pcode QC Check
		if l != 0:
			ppcode = str(ft[adm_levels[l][2]]).strip()
			if ppcode is 'NULL' or ppcode == '':
				null_ppcode_errors.append([l, ft])
				null_ppcode_errors_level_count += 1
		ftcount += 1

		# Geometry QC Check setup
		geom = ft.geometry()
		if geom:
			err = geom.validateGeometry()
			if not err:
				polygons.append(ft)
			else:
				polygons.append(ft)
				geom_errors.append([l, err, ft.id()])
				geom_errors_level_count += 1

		combCount = len(list(itertools.combinations(polygons, 2)))
		for feature1, feature2 in itertools.combinations(polygons, 2):
			if feature1.geometry().intersects(feature2.geometry()):
				geom = feature1.geometry().intersection(feature2.geometry())
				if geom and geom.area() > thres:
					print "ABOVE THRES: {}".format(geom.area())
					feature = QgsFeature()
					fields = mem_layer.pendingFields()
					feature.setFields(fields, True)
					feature.setAttributes([0, feature1.id(), feature2.id()])
					if geom.wkbType() == 7:
						geom_col = geom.asGeometryCollection()
						geom_col_wkt = [wkt.loads(sing_g.exportToWkt()) for sing_g in geom_col if sing_g.type() == 2]
						mp = MultiPolygon(geom_col_wkt)
						feature.setGeometry(QgsGeometry.fromWkt(mp.wkt))
					else:
						feature.setGeometry(geom)
					pr.addFeatures([feature])
					mem_layer.updateExtents()
					mem_layer.commitChanges()
					overlap_errors.append([l, feature1, feature2, geom])
					overlap_errors_level_count += 1

		mem_layer.commitChanges()
		if overlap_errors_level_count > 0:
			QgsMapLayerRegistry.instance().addMapLayer(mem_layer)

		# Parent Pcodes QC Check
		if l != 0:
			ft_centr = ft.geometry().pointOnSurface()
			ftid = str(ft.id()).strip()
			ftpc = str(ft[adm_levels[l][1]]).strip()
			ftn = str(ft[adm_levels[l][3]]).strip()
			ftppc = str(ft[adm_levels[l][2]]).strip()

			pfts = admin_layers[l-1].getFeatures()

			for pft in pfts:
				pft_geom = pft.geometry()
				if ft_centr.intersects(pft_geom):
					pftid = str(pft.id()).strip()
					pftpc = str(pft[adm_levels[l-1][1]]).strip()
					pftn = str(pft[adm_levels[l-1][3]]).strip()
					if ftppc != pftpc:
						parent_errors.append([l, adm_levels[l][0], ftid, ftpc, ftn, ftppc, pftid, pftpc, pftn])
						parent_errors_level_count += 1

	# Duplicated Pcode QC Check
	query = '"' + str(adm_levels[l][1]) + '" in (' + str(duplquery) + ')'
	selection = lyr.getFeatures(QgsFeatureRequest().setFilterExpression(query))
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
	results.append([l, adm_levels[l][0], adm_levels[l][0], ftcount, overlap_errors_level_count, null_pcode_errors_level_count, dupl_pcode_errors_level_count, null_ppcode_errors_level_count, parent_errors_level_count, status])
	l += 1


print "\nNull Pcodes QC Check"
if len(list(null_pcode_errors)) > 0:
	print "Level\tFid\tFName"
	for e in null_pcode_errors:
		print "{}\t{}\t{}".format(e[0], e[1].id(), e[1][adm_levels[l][3]])
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
		print "{}\t{}\t{}".format(e[0], e[1].id(), e[1][adm_levels[l][3]])
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
