# ###########################
# Etools Locations QC Check
# ###########################

import itertools
import collections
import os
import qgis.core
from PyQt4.QtCore import QVariant
from datetime import datetime


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
country = "Kyrgyzstan"
outdir = r"C:"

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
print "Threshold size for intersections: {}".format(thres)

cntryflag = 0
errors = []
pcodes = []
errorCount = 0
qcstatus = ""
geom_errorCount = 0

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


for g in gateway_ids:
	# flag if Country
	if g[1] == "Country":
		cntryflag = 1
	# filter locations by gateway id
	loc_lyr[0].setSubsetString("\"gateway_id\"={}".format(g[0]))
	for ft in loc_lyr[0].getFeatures():
		pcode = str(ft[pc_field]).strip()
		if pcode is not 'NULL' and pcode != '':
			pcodes.append(pcode)

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
	filename = "{}_adm-{}_gid-{}_{}.png".format(country, l, g[0], '{0:%Y}{0:%m}{0:%d}'.format(datetime.utcnow()))
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
	expr = QgsExpression("\"gateway_id\"={}".format(g[0]))
	fts = loc_lyr[0].getFeatures(QgsFeatureRequest(expr))
	ftcount = 0

	null_pcode_ids = []
	null_ppcode_ids = []

	pcode_fid = loc_lyr[0].dataProvider().fieldNameIndex(pc_field)
	parentid_fid = loc_lyr[0].dataProvider().fieldNameIndex(pid_field)
	parent_errors_count = 0

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
		pcode = str(ft[pc_field]).strip()
		if pcode is 'NULL' or pcode == '':
			null_pcode_ids.append(ft.id())
			null_pcode_errors.append([l, ft])

		# Null Parent Pcode QC Check
		ppcode = str(ft[pid_field]).strip()
		if ppcode is 'NULL' or ppcode =='':
			null_ppcode_ids.append(ft.id())
			null_ppcode_errors.append([l, ft])
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
				geom_errorCount += 1
		counter = 1
		overlaps = []
		combCount = len(list(itertools.combinations(polygons, 2)))
		for feature1, feature2 in itertools.combinations(polygons, 2):
			if feature1.geometry().intersects(feature2.geometry()):
				geom = feature1.geometry().intersection(feature2.geometry())
				if geom.area() > thres:
					feature = QgsFeature()
					fields = mem_layer.pendingFields()
					feature.setFields(fields, True)
					feature.setAttributes([g[1], feature1.id(), feature2.id()])
					feature.setGeometry(geom)
					pr.addFeatures([feature])
					mem_layer.updateExtents()
					mem_layer.commitChanges()
					overlaps.append([feature1, feature2, geom])
					overlap_errors.append([l,feature1, feature2, geom])
					errorCount += 1
			counter += 1

		mem_layer.commitChanges()
		if len(list(overlaps)) > 0:
			QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
		#results.append([geomerrors, overlaps])

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
	overlap_count = len(list(overlaps))

	total_errors = null_pcode_count + dupl_pcode_count + null_ppcode_count + overlap_count + parent_errors_count
	status = ""
	if total_errors == 0:
		status = "OK"
	else:
		if null_ppcode_count == 1 and l == 0:
			status = "OK"
		else:
			status = "CHECK"

	# print layer summary
	results.append([l, g[0], g[1], ftcount, overlap_count, null_pcode_count, dupl_pcode_count, null_ppcode_count, parent_errors_count,status])
	l += 1

print "\nParent Pcodes QC Check"
if len(list(parent_errors)) > 0:
	print "Level\tLevelName\tFid\tFPcode\tFName\tWrongParentID\tCorrectParentID\tCorrectParentPcode\tCorrectParentName"
	for e in parent_errors:
		print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(e[0],e[1],e[2],e[3],e[4],e[5],e[6],e[7],e[8])

print "\nGlobal errors:"
if cntryflag == 0:
	print "ERROR - No Country level exists in gateway_id table!"
else:
	print "OK - No global errors."


print "\nLocations Summary"
print "Level\tGateId\tGateName\tFtCount\tOverlaps\tNullPcodes\tDuplPcodes\tNullPPcodes\tWrongPPcodes\tStatus"
for r in results:
	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9])

endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)