# ###########################
#  Locations for eTools All-in-One QC Check
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
print "Locations for eTools All-in-One QC Check"
print "############################"
startDate = datetime.utcnow()
print "Started: {}\n".format(str(startDate))


def timediff():
	timedif = datetime.utcnow() - timediff.prevDate
	timediff.prevDate = datetime.utcnow()
	return str(timedif.seconds + float(timedif.microseconds) / 1000000)


timediff.prevDate = datetime.utcnow()


class AdminLevel:
	def __init__(self, level, name, gat_id, nl_n, nl_pc_f, nl_n_f, nl_ppc_f, nl, new_fts, old_fts, n_geom_err, n_overlap_err, n_null_pc_err, n_dupl_pc_err, n_null_ppc_err, n_parent_err, o_geom_err , o_overlap_err, o_null_pc_err, o_dupl_pc_err, o_null_ppc_err, o_parent_err, n_qcstatus="UNKNOWN", o_qcstatus="UNKNOWN"):
		self.level = level
		self.name = name
		self.gat_id = gat_id
		self.nl_n = nl_n
		self.nl_pc_f = nl_pc_f
		self.nl_n_f = nl_n_f
		self.nl_ppc_f = nl_ppc_f
		self.nl = nl
		self.nfts = new_fts
		self.ofts = old_fts
		self.n_geom_err = n_geom_err
		self.n_overlap_err = n_overlap_err
		self.n_null_pc_err = n_null_pc_err
		self.n_dupl_pc_err = n_dupl_pc_err
		self.n_null_ppc_err = n_null_ppc_err
		self.n_parent_err = n_parent_err
		self.n_qcstatus = n_qcstatus
		self.o_geom_err = o_geom_err
		self.o_overlap_err = o_overlap_err
		self.o_null_pc_err = o_null_pc_err
		self.o_dupl_pc_err = o_dupl_pc_err
		self.o_null_ppc_err = o_null_ppc_err
		self.o_parent_err = o_parent_err
		self.o_qcstatus = o_qcstatus


def saveimg(lyr_id, level, lyr_type):
	# set up image renderer
	img = QImage(QSize(600, 600), QImage.Format_ARGB32_Premultiplied)

	# set image's background color
	color = QColor(255, 255, 255)
	img.fill(color.rgb())

	render = QgsMapRenderer()
	render.setLayerSet([lyr_id])

	# set extent
	rect = QgsRectangle(render.fullExtent())
	rect.scale(1.1)
	render.setExtent(rect)

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
	filename = "{}_adm-{}_{}_{}.png".format(country, level, lyr_type, '{0:%Y}{0:%m}{0:%d}'.format(datetime.utcnow()))
	path = os.path.join(outdir, filename)

	# save image
	img.save(path, "png")
	# print "Snapshot for level {} created at {}".format(l, path)


# definition of admin levels and input layers

# params for Djibouti
# admin_levels = []
# admin_levels.append(AdminLevel(0,"Country",1,"DJI_Admin1_1996_FEWS","admin0Pcod","COUNTRY",""))
# admin_levels.append(AdminLevel(1,"Region",2,"DJI_Admin2_FEWS","admin1Pcod","ADMIN2","admin0Pcod"))
# admin_levels.append(AdminLevel(2,"District",3,"DJI_Admin3_FEWS","admin2Pcod","ADMIN3","admin1Pcod"))
# country = "Djibouti"
# outdir = r"C:\Users\GIS\Documents\____UNICEF_ETOOLS\04_Data\00_UPDATE\Djibouti"

# params for Angola
admin_levels = []
admin_levels.append(AdminLevel(0,"Country",1,"AGO_adm0","admin0Pcod","NAME_ENGLI","", [],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
admin_levels.append(AdminLevel(1,"Region",2,"AGO_adm1","admin1Pcod","NAME_1","admin0Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
admin_levels.append(AdminLevel(2,"District",3,"AGO_adm2","admin2Pcod","NAME_2","admin1Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
admin_levels.append(AdminLevel(3,"Subdistrict",4,"AGO_adm3","admin3Pcod","NAME_3","admin2Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
country = "Angola"
outdir = r"C:\Users\GIS\Documents\____UNICEF_ETOOLS\04_Data\00_UPDATE\Angola"

# params for Niger
# admin_levels = []
# admin_levels.append(AdminLevel(0,"Country",1,"NER_adm00_feb2018", "ISO2", "adm_00", ""))
# admin_levels.append(AdminLevel(1,"Region",2,"NER_adm01_feb2018","rowcacode1","adm_01","ISO2"))
# admin_levels.append(AdminLevel(2,"Department",3,"NER_adm02_feb2018","rowcacode2","adm_02","rowcacode1"))
# admin_levels.append(AdminLevel(3,"Other",99,"NER_adm03_feb2018","rowcacode3","adm_03","rowcacode2"))
# country = "Niger"
# outdir = r"C:\Users\GIS\Documents\____UNICEF_ETOOLS\04_Data\00_UPDATE\Niger"


# input Pcode, Parent Pcode and Name fields for old layer
id_field = "id"
pc_field = "p_code"
pid_field = "parent_id"
name_field = "name"

# select type of actions to be performed
null_pcode_qc = 1
dupl_pcode_qc = 1
null_ppcode_qc = 1
parent_qc = 1
geom_qc = 1

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
new_pcodes = []
old_pcodes = []

old_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == "locations_location"][0]

# add layers and new/old features for all admin levels
for admin_level in admin_levels:
	new_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == admin_level.nl_n][0]
	new_fts = [ft for ft in new_lyr.getFeatures()]  # TODO: add check for null geom
	admin_level.nl = new_lyr
	admin_level.nfts = new_fts
	old_lyr.setSubsetString("\"gateway_id\"={}".format(admin_level.gat_id))
	old_fts = [ft for ft in old_lyr.getFeatures()]  # TODO: add check for null geom
	admin_level.ofts = old_fts
	for nft in new_fts:
		nft_pc = nft[admin_level.nl_pc_f]
		if nft_pc:
			new_pcodes.append(nft[admin_level.nl_pc_f])
	for oft in old_fts:
		oft_pc = oft[pc_field]
		if oft_pc:
			old_pcodes.append(oft_pc)
	saveimg(new_lyr.id(), admin_level.level, "new")
	saveimg(old_lyr.id(), admin_level.level, "old")
	old_lyr.setSubsetString("")


# list duplicated pcodes
new_duplpcodes = ["'" + item + "'" for item, count in collections.Counter(new_pcodes).items() if count > 1]
new_duplquery = ''
old_duplpcodes = ["'" + item + "'" for item, count in collections.Counter(old_pcodes).items() if count > 1]
old_duplquery = ''

for nd in new_duplpcodes:
	new_duplquery = ",".join(list(new_duplpcodes))
for od in old_duplpcodes:
	old_duplquery = ",".join(list(old_duplpcodes))


def qc(admin_level, fts, pfts, lyr_type):
	# Geometry QC Check setup
	# create a memory layer for intersections
	mem_layer = QgsVectorLayer("MultiPolygon?crs=epsg:4326", "level_{}_{}_overlaps".format(admin_level.level, lyr_type), "memory")
	mem_layer.startEditing()
	pr = mem_layer.dataProvider()
	pr.addAttributes(
		[QgsField("lyrid", QVariant.String), QgsField("fid1", QVariant.Int), QgsField("fid2", QVariant.Int)])

	# calculate combinations
	combinations = itertools.combinations(fts, 2)

	# print "{}-{}-{}-{}".format(admin_level.level, admin_level.nl_n_f,fts,pfts)
	for ft in fts:
		ftgeom = ft.geometry()
		ftid = str(ft.id()).strip()
		if lyr_type == "new":
			ftpc = "{}".format(ft[admin_level.nl_pc_f]).strip()
			# print "{}-{}-{}-{}".format(admin_level.level,ftid, admin_level.nl_n_f, admin_level.nl_n)
			ftn = "{}".format(ft[admin_level.nl_n_f].encode('utf-8'))
			# print "added {}".format(ftn)
		else:
			ftpc = str(ft[pc_field]).strip()
			ftn = "{}".format(ft[name_field].encode('utf-8')).strip()

		# Null Pcode QC Check
		if ftpc is 'NULL' or ftpc == '':
			if lyr_type == "new":
				admin_level.n_null_pc_err.append(ft)
			else:
				admin_level.o_null_pc_err.append(ft)

		# Null Parent Pcode QC Check
		if admin_level.name != "Country":
			if lyr_type == "new":
				ftppc = str(ft[admin_level.nl_ppc_f]).strip()
				ftparent = ftppc
			else:
				ftpid = str(ft[pid_field]).strip()
				ftparent = ftpid

			if ftparent is 'NULL' or ftparent =='':
				if lyr_type == "new":
					admin_level.n_null_ppc_err.append(ft)
				else:
					admin_level.o_null_ppc_err.append(ft)

		if ftgeom:
			# Geometry QC Check setup
			if geom_qc == 1:
				for feature1, feature2 in combinations:
					if feature1.geometry().intersects(feature2.geometry()):
						intersect_geom = feature1.geometry().intersection(feature2.geometry())
						if intersect_geom and intersect_geom.area() > thres:
							print "{} - ABOVE THRES: {}".format(admin_level.level, intersect_geom.area())
							feature = QgsFeature()
							fields = mem_layer.pendingFields()
							feature.setFields(fields, True)
							feature.setAttributes([0, feature1.id(), feature2.id()])
							if intersect_geom.wkbType() == 7:
								geom_col = intersect_geom.asGeometryCollection()
								geom_col_wkt = [wkt.loads(sing_g.exportToWkt()) for sing_g in geom_col if
												sing_g.type() == 2]
								mp = MultiPolygon(geom_col_wkt)
								feature.setGeometry(QgsGeometry.fromWkt(mp.wkt))
							else:
								feature.setGeometry(intersect_geom)
							pr.addFeatures([feature])
							mem_layer.updateExtents()
							mem_layer.commitChanges()
							if lyr_type == "new":
								#print "{}-{}-{}".format(admin_level.level,admin_level.name,len(list(admin_level.n_overlap_err)))
								admin_level.n_overlap_err.append(1)
								#print "{}-{}-{}".format(admin_level.level, admin_level.name, len(list(admin_level.n_overlap_err)))
							else:
								admin_level.o_overlap_err.append([feature1, feature2, intersect_geom])

				mem_layer.commitChanges()
				if lyr_type == "new":
					# print len(list(admin_level.n_overlap_err))
					if len(admin_level.n_overlap_err) > 0:
						QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
				else:
					if len(admin_level.o_overlap_err) > 0:
						QgsMapLayerRegistry.instance().addMapLayer(mem_layer)

			# Parent Pcodes QC Check
			if admin_level.name != "Country" and parent_qc == 1:
				ft_centr = ftgeom.pointOnSurface()

				for pft in pfts:
					pftgeom = pft.geometry()
					pftid = str(pft.id()).strip()
					if lyr_type == "new":
						pftpc = str(pft[admin_levels[admin_level.level - 1].nl_pc_f]).strip()
						pftn = str(pft[admin_levels[admin_level.level - 1].nl_n_f].encode('utf-8')).strip()
						pftident = pftpc
					else:
						pftpc = str(ft[pc_field]).strip()
						pftn = str(ft[name_field].encode('utf-8')).strip()
						pftident = pftid
					if pftgeom:
						if ft_centr.intersects(pftgeom):
							if ftparent != pftident:
								if lyr_type == "new":
									admin_level.n_parent_err.append([admin_level.name, ftid, ftpc, ftn, ftparent, pftident, pftn])
								else:
									admin_level.o_parent_err.append([admin_level.name, ftid, ftpc, ftn, ftparent, pftident, pftn])
					else:
						if lyr_type == "new":
							admin_level.n_parent_err.append([admin_level.name, ftid, ftpc, ftn, ftparent, pftident, pftn])
						else:
							admin_level.o_parent_err.append([admin_level.name, ftid, ftpc, ftn, ftparent, pftident, pftn])
		else:
			if lyr_type == "new":
				admin_level.n_geom_err.append(["empty / invalid geometry", ft.id()])
			else:
				admin_level.o_geom_err.append(["empty / invalid geometry", ft.id()])
	# Duplicated Pcode QC Check
	if lyr_type == "new":
		query = '"' + str(admin_level.nl_pc_f) + '" in (' + str(new_duplquery) + ')'
		selection = admin_level.nl.getFeatures(QgsFeatureRequest().setFilterExpression(query))
		admin_level.n_dupl_pc_err = [k.id() for k in selection]
	else:
		query = '"' + str(pc_field) + '" in (' + str(old_duplquery) + ')'
		selection = old_lyr.getFeatures(QgsFeatureRequest().setFilterExpression(query))
		admin_level.o_dupl_pc_err = [k.id() for k in selection]

	# Count errors and QC status
	if lyr_type == "new":
		overlap_errors_level_count = len(admin_level.n_overlap_err)
		null_pcode_errors_level_count = len(admin_level.n_null_pc_err)
		dupl_pcode_errors_level_count = len(admin_level.n_dupl_pc_err)
		null_ppcode_errors_level_count = len(admin_level.n_null_ppc_err)
		parent_errors_level_count = len(admin_level.n_parent_err)
		fcount = len(admin_level.nfts)
	else:
		overlap_errors_level_count = len(admin_level.o_overlap_err)
		null_pcode_errors_level_count = len(admin_level.o_null_pc_err)
		dupl_pcode_errors_level_count = len(admin_level.o_dupl_pc_err)
		null_ppcode_errors_level_count = len(admin_level.o_null_ppc_err)
		parent_errors_level_count = len(admin_level.o_parent_err)
		fcount = len(admin_level.ofts)

	total_errors = overlap_errors_level_count + null_pcode_errors_level_count + dupl_pcode_errors_level_count + null_ppcode_errors_level_count + parent_errors_level_count
	if total_errors == 0 and fcount > 0:
		status = "OK"
	elif fcount == 0:
		status = "NOFEATS"
	else:
		if null_ppcode_errors_level_count == 1 and admin_level.name == "Country":
			status = "OK"
		else:
			status = "CHECK"

	if lyr_type == "new":
		admin_level.n_qcstatus = status
	else:
		admin_level.o_qcstatus = status


# main loop for all levels
for admin_level in admin_levels:
	# qc for new locations
	qc(admin_level, admin_level.nfts, admin_levels[admin_level.level - 1].nfts, "new")
	qc(admin_level, admin_level.ofts, admin_levels[admin_level.level - 1].ofts, "old")



# print "\nNull Pcodes QC Check"
# if len(list(null_pcode_errors)) > 0:
# 	print "Level\tFid\tFName"
# 	for e in null_pcode_errors:
# 		print "{}\t{}\t{}".format(e[0], e[1][id_field], e[1][name_field])
# else:
# 	print "OK"
#
# print "\nDuplicate Pcodes QC Check"
# dupl_err_sum = sum([e[1] for e in dupl_pcode_errors])
# if dupl_err_sum > 0:
# 	print "Level\tCount\tFids"
# 	for e in dupl_pcode_errors:
# 		print "{}\t{}".format(e[0], e[1], e[2])
# else:
# 	print "OK"
#
# print "\nNull Parent Pcodes QC Check"
# if len(list(null_ppcode_errors)) > 0:
# 	print "Level\tFid\tFName"
# 	for e in null_ppcode_errors:
# 		print "{}\t{}\t{}".format(e[0], e[1][id_field], e[1][name_field])
# else:
# 	print "OK"
#
#
# print "\nParent Pcodes QC Check"
# if len(list(parent_errors)) > 0:
# 	print "Level\tLevelName\tFid\tFPcode\tFName\tWrongParentID\tCorrectParentID\tCorrectParentPcode\tCorrectParentName"
# 	for e in parent_errors:
# 		print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8])
# else:
# 	print "OK"
#
# print "\nOther QC check:"
# if cntryflag == 0:
# 	print "ERROR - No Country level exists in gateway_id table!"
# else:
# 	print "OK"


print "\nLocations Summary"
print "Level\tNewLyr\tGateId\tGateName\tNewFtCount\tOldFtCount\tNewOver\tOldOver\tNewNullPc\tOldNullPc\tNewDuplPc\tOldDuplPc\tNewNullPpc\tOldNullPpc\tNewWrongPpc\tOldWrongPpc\tNewStatus\tOldStatus"
for a in admin_levels:
	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, a.name, a.gat_id, a.name,
																					  len(a.nfts), len(a.ofts),
																					  len(a.n_overlap_err),
																					  len(a.o_overlap_err),
																					  len(a.n_null_pc_err),
																					  len(a.o_null_pc_err),
																					  len(a.n_dupl_pc_err),
																					  len(a.o_dupl_pc_err),
																					  len(a.n_null_ppc_err),
																					  len(a.o_null_ppc_err),
																					  len(a.n_parent_err),
																					  len(a.o_parent_err), a.n_qcstatus,
																					  a.o_qcstatus)
endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
