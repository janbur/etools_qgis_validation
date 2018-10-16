# ###########################
#  Locations for eTools QC Check
# ###########################

import itertools
import json
import collections
import os
import numpy
import sys
import qgis.core
import requests
from qgis.core import *
from PyQt4.QtCore import QVariant
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from datetime import datetime, date, time
import time as t
from shapely.geometry.multipolygon import MultiPolygon
from shapely import wkt
from difflib import SequenceMatcher
from math import sin, cos, sqrt, atan2, radians

print "############################"
print "Locations for eTools QC Check"
print "############################"
startDate = datetime.utcnow()
print "Started: {}\n".format(startDate)


class AdminLevel:
	def __init__(self, level, name, gat_id, nl_n, nl_pc_f, nl_n_f, nl_ppc_f, nl, new_fts, old_fts, n_geom_err, n_overlap_err, n_null_pc_err, n_dupl_pc_err, n_null_ppc_err, n_parent_err, o_geom_err , o_overlap_err, o_null_pc_err, o_dupl_pc_err, o_null_ppc_err, o_parent_err, n_no_parent_err, o_no_parent_err, cross_a, cross_ag, cross_an, cross_b, cross_br, cross_briu, cross_bnr, cross_bmr, cross_bnriu, cross_c, cross_qc, n_qc_stat_int="UNKNOWN", o_qc_stat_int="UNKNOWN"):
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
		self.n_no_parent_err = n_no_parent_err
		self.n_qc_stat_int = n_qc_stat_int
		self.o_geom_err = o_geom_err
		self.o_overlap_err = o_overlap_err
		self.o_null_pc_err = o_null_pc_err
		self.o_dupl_pc_err = o_dupl_pc_err
		self.o_null_ppc_err = o_null_ppc_err
		self.o_parent_err = o_parent_err
		self.o_no_parent_err = o_no_parent_err
		self.o_qc_stat_int = o_qc_stat_int
		self.cross_a = cross_a  # case A
		self.cross_ag = cross_ag  # case A - diff geom
		self.cross_an = cross_an  # case A - diff name
		self.cross_b = cross_b  # case B
		self.cross_br = cross_br  # case B - with Remap
		self.cross_briu = cross_briu  # case B - with Remap in Use
		self.cross_bnr = cross_bnr  # case B - no Remap
		self.cross_bmr = cross_bmr  # case B - multiple Remap
		self.cross_bnriu = cross_bnriu  # case B - no Remap in Use
		self.cross_c = cross_c  # case B
		self.cross_qc = cross_qc  # cross-check QC status

def calc_distance(lat1dd,lon1dd,lat2dd,lon2dd):
	# approximate radius of earth in m
	R = 6373.0

	lat1 = radians(lat1dd)
	lon1 = radians(lon1dd)
	lat2 = radians(lat2dd)
	lon2 = radians(lon2dd)

	dlon = lon2 - lon1
	dlat = lat2 - lat1

	a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))

	distance = (R * c) * 1000
	return distance


def saveimg(lyr_id, lyr_name, level, lyr_type):
	# set up image renderer
	image = QImage(QSize(600, 600), QImage.Format_ARGB32_Premultiplied)

	painter = QPainter(image)
	settings = iface.mapCanvas().mapSettings()
	settings.setLayers([lyr_id])
	settings.setOutputSize(image.size())

	render = QgsMapRenderer()
	render.setLayerSet([admin_levels[0].nl.id()])  # zoom extent to the country level

	# set extent
	rect = QgsRectangle(render.fullExtent())
	rect.scale(1.1)
	settings.setExtent(rect)

	job = QgsMapRendererCustomPainterJob(settings, painter)
	job.renderSynchronously()
	painter.end()

	outdir = os.path.join(os.path.dirname(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri())), "PNG")
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	if lyr_type == "new":
		filename = "{}_adm-{}_{}_{}_{}.png".format(country, level, qc_type, lyr_type, lyr_name, '{0:%Y}{0:%m}{0:%d}'.format(datetime.utcnow()))
	else:
		filename = "{}_adm-{}_{}_{}_{}_{}.png".format(country, level, qc_type, lyr_type, lyr_name, '{0:%Y}{0:%m}{0:%d}'.format(datetime.utcnow()))

	path = os.path.join(outdir, filename)

	# save image
	image.save(path, "png")
	# print "Snapshot for level {} created at {}".format(l, path)


# definition of admin levels and input layers

admin_levels = []

admin_levels.append(AdminLevel(0, 'Country', 1, 'kgz_admbnda_adm0_20180827', 'ADM0_PCODE', 'AMD0_EN', None,[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
admin_levels.append(AdminLevel(1, 'Province', 4, 'kgz_admbnda_adm1_20180827', 'ADM1_PCODE', 'ADM1_EN', 'ADM0_PCODE',[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
admin_levels.append(AdminLevel(2, 'District', 3, 'kgz_admbnda_adm2_20180827', 'ADM2_PCODE', 'ADM2_EN', 'ADM1_PCODE',[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
admin_levels.append(AdminLevel(3, 'Municipality', 6, 'kgz_admbnda_adm3_20180827', 'ADM3_PCO_1', 'ADM3_EN', 'ADM2_PCODE',[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
country = 'Kyrgyzstan'
iso2 = 'KG'
iso3 = 'KGZ'
workspace_id = 39



qc_type = 'before'  # options: "before" - BEFORE UPLOAD or "after" - AFTER UPLOAD
qc_type_oldnew = 'both'  # options: "old" - validate only data from eTools, "new" - validate only data from HDX/GADM, "both" - both old and new + cross-check

old_label = "old"
if qc_type == "after":
	old_label = "updated"

# input Pcode, Parent Pcode and Name fields for old layer
id_field = "id"
pc_field = "p_code"
pid_field = "parent_id"
name_field = "name"
old_lyr_name = "{}_loc_geom_{}".format(country, qc_type)

# select type of actions to be performed
null_pcode_qc = 1
dupl_pcode_qc = 1
null_ppcode_qc = 1
parent_qc = 1
geom_qc = 1

# thresholds size for intersections
thres = 0.0000001

# level counter
l = 0

new_pcodes = []
old_pcodes = []

old_lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if old_lyr_name in layer.name()]

# settings for cross-check
geomsim_treshold = 90
textsim_treshold = 0.9
geomsim_remap_treshold = 1
point_dist_treshold = 1  # in meters

def getval(ft, field):
	if field:
		val = ft[field]
		if val:
			if isinstance(val, basestring):
				result = "{}".format(val.encode('UTF-8').strip())
			else:
				result = "{}".format(val)
		else:
			result = ""
	else:
		result = ""
	return result


# add layers and new/old features for all admin levels
for admin_level in admin_levels:
	new_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == admin_level.nl_n][0]
	new_fts = [ft for ft in new_lyr.getFeatures()]  # TODO: add check for null geom
	admin_level.nl = new_lyr
	admin_level.nfts = new_fts
	old_fts = []


	# TODO: checking both points and polygons...
	for old_lyr in old_lyrs:
		if admin_level.gat_id or admin_level.gat_id == 0:
			old_lyr.setSubsetString("\"gateway_id\"={}".format(admin_level.gat_id))
			old_fts = old_fts + [ft for ft in old_lyr.getFeatures()]  # TODO: add check for null geom
		elif admin_level.gat_id is None:
			old_lyr.setSubsetString("\"gateway_id\" is NULL")  # TODO: Should not we skip adding features if gateway_id is None?
			old_fts = old_fts + [ft for ft in old_lyr.getFeatures()]  # TODO: add check for null geom
	admin_level.ofts = old_fts

	for nft in new_fts:
		nft_pc = getval(nft, admin_level.nl_pc_f)
		if nft_pc:
			new_pcodes.append(nft_pc)
	for oft in old_fts:
		oft_pc = getval(oft, pc_field)
		if oft_pc:
			old_pcodes.append(oft_pc)
	saveimg(new_lyr.id(), new_lyr.name(), admin_level.level, "new")
	for old_lyr in old_lyrs:
		saveimg(old_lyr.id(), old_lyr.name(), admin_level.level, "old")
		old_lyr.setSubsetString("")


# read locations in use # ToDo replace with API call once tested
json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri()))), "{}_loc_in_use.json".format(country))
with open(json_path) as json_data:
	loc_in_use = json.load(json_data)
	pcodes_in_use = [liu['p_code'] for liu in loc_in_use]
	ids_in_use = [liu['id'] for liu in loc_in_use]


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

	for ft in fts:
		ftgeom = ft.geometry()

		if lyr_type == "new":
			ftpc = getval(ft, admin_level.nl_pc_f)  # works for shapefiles
		else:
			ftpc = getval(ft, pc_field)

		# Null Pcode QC Check
		if ftpc is 'NULL' or ftpc == '':  # works for shapefiles
			if lyr_type == "new":
				admin_level.n_null_pc_err.append(ft)
			else:
				admin_level.o_null_pc_err.append(ft)

		# Null Parent Pcode QC Check
		if admin_level.level != 0:
			if lyr_type == "new":
				ftppc = getval(ft, admin_level.nl_ppc_f)
				ftparent = ftppc
			else:
				ftpid = getval(ft, pid_field)
				ftparent = ftpid

			if ftparent is 'NULL' or ftparent == '':
				if lyr_type == "new":
					admin_level.n_null_ppc_err.append(ft)
				else:
					admin_level.o_null_ppc_err.append(ft)

		if ftgeom:
			# Geometry QC Check setup
			if geom_qc == 1:
				for feature1, feature2 in combinations:
					if feature1.geometry() and feature2.geometry():
						if feature1.geometry().intersects(feature2.geometry()):
							intersect_geom = feature1.geometry().intersection(feature2.geometry())
							if intersect_geom and intersect_geom.area() > thres:
								# print "{} - ABOVE THRES: {}".format(admin_level.level, intersect_geom.area())
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
									admin_level.n_overlap_err.append(1)
								else:
									admin_level.o_overlap_err.append([feature1, feature2, intersect_geom])
				mem_layer.commitChanges()
				if lyr_type == "new":
					if len(admin_level.n_overlap_err) > 0:
						QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
				else:
					if len(admin_level.o_overlap_err) > 0:
						QgsMapLayerRegistry.instance().addMapLayer(mem_layer)

			# Parent Pcodes QC Check
			if admin_level.level != 0 and parent_qc == 1:
				ft_centr = ftgeom.pointOnSurface()

				if lyr_type == "new":
					ftppc = getval(ft, admin_level.nl_ppc_f)
					ftparent = ftppc
				else:
					ftpid = getval(ft, pid_field)
					ftparent = ftpid

				parent_found_flag = 0
				for pft in pfts:
					pftgeom = pft.geometry()
					if pftgeom:
						if ft_centr.intersects(pftgeom):
							parent_found_flag = 1
							if lyr_type == "new":
								pftpc = getval(pft, admin_levels[admin_level.level - 1].nl_pc_f)
								if ftparent != pftpc:
									admin_level.n_parent_err.append([ft, ftparent, pft])
							else:
								pftid = getval(pft, id_field)
								if ftparent != pftid:
									admin_level.o_parent_err.append([ft, ftparent, pft])
					# else:
					# 	if lyr_type == "new":
					# 		admin_level.n_parent_err.append([ft, ftparent, pft])
					# 	else:
					# 		admin_level.o_parent_err.append([ft, ftparent, pft])
				if parent_found_flag == 0:
					if lyr_type == "new":
						admin_level.n_no_parent_err.append([ft, ftparent])
					else:
						admin_level.o_no_parent_err.append([ft, ftparent])

		else:
			if lyr_type == "new":
				admin_level.n_geom_err.append(ft)
			else:
				admin_level.o_geom_err.append(ft)

	# Duplicated Pcode QC Check
	if lyr_type == "new":
		query = "\"{}\" in ({})".format(admin_level.nl_pc_f, new_duplquery)
		selection = admin_level.nl.getFeatures(QgsFeatureRequest().setFilterExpression(query))
		admin_level.n_dupl_pc_err = [k for k in selection]
	else:
		if admin_level.gat_id:
			for old_lyr in old_lyrs:
				query = "\"gateway_id\"={} AND \"{}\" in ({})".format(admin_level.gat_id, pc_field, old_duplquery) # TODO: loop old lyrs...
				selection = old_lyr.getFeatures(QgsFeatureRequest().setFilterExpression(query))
				admin_level.o_dupl_pc_err = [k for k in selection]

	# Count errors and QC status
	if lyr_type == "new":
		overlap_errors_level_count = len(admin_level.n_overlap_err)
		null_pcode_errors_level_count = len(admin_level.n_null_pc_err)
		dupl_pcode_errors_level_count = len(admin_level.n_dupl_pc_err)
		null_ppcode_errors_level_count = len(admin_level.n_null_ppc_err)
		parent_errors_level_count = len(admin_level.n_parent_err)
		no_parent_errors_level_count = len(admin_level.n_no_parent_err)
		fcount = len(admin_level.nfts)
	else:
		overlap_errors_level_count = len(admin_level.o_overlap_err)
		null_pcode_errors_level_count = len(admin_level.o_null_pc_err)
		dupl_pcode_errors_level_count = len(admin_level.o_dupl_pc_err)
		null_ppcode_errors_level_count = len(admin_level.o_null_ppc_err)
		parent_errors_level_count = len(admin_level.o_parent_err)
		no_parent_errors_level_count = len(admin_level.o_no_parent_err)
		fcount = len(admin_level.ofts)

	total_errors = overlap_errors_level_count + null_pcode_errors_level_count + dupl_pcode_errors_level_count + null_ppcode_errors_level_count + parent_errors_level_count + no_parent_errors_level_count
	if total_errors == 0 and fcount > 0:
		status = "OK"
	elif fcount == 0:
		status = "NO DATA"
	else:
		if null_ppcode_errors_level_count == 1 and total_errors == 1 and admin_level.name == "Country":
			status = "OK"
		elif overlap_errors_level_count == total_errors:
			status = "CHECK"
		else:
			status = "ERROR"

	if lyr_type == "new":
		admin_level.n_qc_stat_int = status
	else:
		admin_level.o_qc_stat_int = status


######################
# Main loop for all levels
######################
for admin_level in admin_levels:
	# qc for new locations
	if qc_type_oldnew == "new" or qc_type_oldnew == "both": qc(admin_level, admin_level.nfts, admin_levels[admin_level.level - 1].nfts, "new")
	if qc_type_oldnew == "old" or qc_type_oldnew == "both": qc(admin_level, admin_level.ofts, admin_levels[admin_level.level - 1].ofts, "old")

	######################
	# Cross-check new and old data
	######################
	new_pcodes = []

	# list new pcodes
	if qc_type_oldnew == "new" or qc_type_oldnew == "both":
		for new_ft in admin_level.nfts:
			new_ft_pc = getval(new_ft, admin_level.nl_pc_f)
			new_ft_name = getval(new_ft, admin_level.nl_n_f)
			new_ft_geom = new_ft.geometry()
			if new_ft_pc:  # ToDo: add handling for locations with null pcodes - match by geom...?
				new_pcodes.append(new_ft_pc)

				if new_ft_pc in old_pcodes:  # CASE A
					for old_ft in admin_level.ofts:  # ToDo: check all old locations, regardless gateway id / level
						old_ft_pc = getval(old_ft, pc_field)
						if old_ft_pc == new_ft_pc:
							old_ft_name = getval(old_ft, name_field)
							old_ft_geom = old_ft.geometry()
							admin_level.cross_a.append([old_ft, new_ft])
							if not old_ft_geom or not new_ft_geom:
								admin_level.cross_ag.append([old_ft, new_ft, -99, -99])  # ToDo: change -99 to None?
							elif not old_ft_geom.equals(new_ft_geom):  # CASE A - diff geom
								# Algorithm for measuring similarity of geometry
								intersect_geom = new_ft_geom.intersection(old_ft_geom)
								if old_ft_geom.area() > 0 and new_ft_geom.area() > 0:  # ToDo: make sure geom has area
									geomsim_old = (intersect_geom.area() / old_ft_geom.area() * 100)
									geomsim_new = (intersect_geom.area() / new_ft_geom.area() * 100)
									if (geomsim_old < geomsim_treshold) or (geomsim_new < geomsim_treshold):
										admin_level.cross_ag.append([old_ft, new_ft, geomsim_old, geomsim_new])
										# ToDo: remapping?
								else:
									if old_ft_geom.wkbType() == QGis.WKBPoint and new_ft_geom.wkbType() == QGis.WKBPoint:  # Matching points
										distance = calc_distance(old_ft_geom.asPoint().y(),old_ft_geom.asPoint().x(),new_ft_geom.asPoint().y(),new_ft_geom.asPoint().x())
										if distance > point_dist_treshold:
											admin_level.cross_ag.append([old_ft, new_ft, distance, distance])  # ToDo: change -99 to None?
									else:
										admin_level.cross_ag.append([old_ft, new_ft, -99, -99])  # ToDo: change -99 to None?
							if new_ft_name != old_ft_name:  # CASE A - diff name
								# Algorithm for measuring similarity of names
								textsim = SequenceMatcher(None, old_ft_name, new_ft_name).ratio()
								if textsim < textsim_treshold:
									admin_level.cross_an.append([old_ft, new_ft, textsim])
				else:  # CASE C
					admin_level.cross_c.append(new_ft)

	if qc_type_oldnew == "old" or qc_type_oldnew == "both":
		for old_ft in admin_level.ofts:
			old_ft_pc = getval(old_ft, pc_field)
			old_ft_name = getval(old_ft, name_field)
			old_ft_geom = old_ft.geometry()
			if old_ft_pc:
				if old_ft_pc not in new_pcodes:  # CASE B
					admin_level.cross_b.append(old_ft)

					# try to match removed location with new location
					remapflag = 0
					if old_ft_geom:  # check if geometry is ok
						for new_ft in admin_level.nfts:
							if new_ft.geometry().contains(old_ft.geometry().pointOnSurface()):
								new_ft_pc = getval(new_ft, admin_level.nl_pc_f)
								new_ft_name = getval(new_ft, admin_level.nl_n_f)
								new_ft_geom = new_ft.geometry()
								textsim = SequenceMatcher(None, old_ft_name, new_ft_name).ratio()
								intersect_geom = new_ft_geom.intersection(old_ft_geom)
								geomsim_old = (intersect_geom.area() / old_ft_geom.area() * 100)
								geomsim_new = (intersect_geom.area() / new_ft_geom.area() * 100)
								#print "{}-{}-{}".format(new_ft_pc,geomsim_old,geomsim_new)

								if (geomsim_old > geomsim_remap_treshold) or (geomsim_new > geomsim_remap_treshold) or (geomsim_old < 0 and geomsim_new < 0):  # ToDo: for some reason negative area/similarity is returned for exactly same geometries
									admin_level.cross_br.append([old_ft, new_ft, textsim, geomsim_old, geomsim_new])
									remapflag += 1

									if old_ft_pc in pcodes_in_use:
										admin_level.cross_briu.append([old_ft, new_ft, textsim, geomsim_old, geomsim_new])
									# print "Suggested remap from old ft: {}-{}-{} to new ft: {}-{}-{}".format(old_ft.id(),old_ft_pc,old_ft_name,new_ft.id(),new_ft_pc,new_ft_name)
					if remapflag == 0:
						admin_level.cross_bnr.append(old_ft)

						# check if missing location is in use
						if old_ft_pc in pcodes_in_use:
							admin_level.cross_bnriu.append(old_ft)

					elif remapflag > 1:
						admin_level.cross_bmr.append(old_ft)


# OLD DATASETS QC REPORT
if qc_type_oldnew == "old" or qc_type_oldnew == "both":
	print "\nOld Dataset QC Check"

	print "\nOld Dataset Geometry QC Check"
	total_o_geom_err = sum([len(a.o_geom_err) for a in admin_levels])
	if total_o_geom_err > 0:
		print "Level\tType\tFtid\tFtName\tFtPcode"
		for a in admin_levels:
			for e in a.o_geom_err:
				print "{}\t{}\t{}\t{}\t{}".format(a.level, "old", e.id(), getval(e, name_field), getval(e, pc_field))  # Todo: check id() for postgis / shp
	else:
		print "OK"


	print "\nOld Dataset Null Pcodes QC Check"
	total_o_null_pc_err = sum([len(a.o_null_pc_err) for a in admin_levels])
	if total_o_null_pc_err > 0:
		print "Level\tType\tFtid\tFtName"
		for a in admin_levels:
			for e in a.o_null_pc_err:
				print "{}\t{}\t{}\t{}".format(a.level, "old", e.id(), getval(e, name_field))  # Todo: check id() for postgis / shp
	else:
		print "OK"


	print "\nOld Dataset Duplicate Pcodes QC Check"
	total_o_dupl_pc_err = sum([len(a.o_dupl_pc_err) for a in admin_levels])
	if total_o_dupl_pc_err > 0:
		print "Level\tType\tFtCount\tFtids\tPcodes"
		for a in admin_levels:
			old_dupl_count = len(a.o_dupl_pc_err)
			if old_dupl_count > 0:
				print "{}\t{}\t{}\t{}\t{}".format(a.level, "old", old_dupl_count, [f.id() for f in a.o_dupl_pc_err], [getval(f, pc_field) for f in a.o_dupl_pc_err])  # Todo: check id() for postgis / shp
	else:
		print "OK"


	print "\nOld Dataset Null Parent Pcodes QC Check"
	total_o_null_ppc_err = sum([len(a.o_null_ppc_err) for a in admin_levels])
	if total_o_null_ppc_err > 0:
		print "Level\tType\tFtid\tPcode\tFtName"
		for a in admin_levels:
			for e in a.o_null_ppc_err:
				print "{}\t{}\t{}\t{}\t{}".format(a.level, "old", e.id(), getval(e, pc_field), getval(e, name_field))  # Todo: check id() for postgis / shp
	else:
		print "OK"


	print "\nOld Dataset Parent Pcodes QC Check"
	total_o_parent_err = sum([len(a.o_parent_err) for a in admin_levels])
	if total_o_parent_err > 0:
		print "Level\tType\tFid\tFPcode\tFName\tWrongParentID\tCorrectParentID\tCorrectParentPcode\tCorrectParentName"
		for a in admin_levels:
			for e in a.o_parent_err:
				print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "old", e[0].id(), getval(e[0], pc_field), getval(e[0], name_field), getval(e[0], pid_field), e[2].id(), getval(e[2], pc_field), getval(e[2], name_field))  # Todo: check id() for postgis / shp
	else:
		print "OK"


	print "\nOld Dataset No Parent QC Check"
	total_o_no_parent_err = sum([len(a.o_no_parent_err) for a in admin_levels])
	if total_o_no_parent_err > 0:
		print "Level\tType\tFid\tFPcode\tFName\tParentID"
		for a in admin_levels:
			for e in a.o_no_parent_err:
				print "{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "old", e[0].id(), getval(e[0], pc_field), getval(e[0], name_field), getval(e[0], pid_field))  # Todo: check id() for postgis / shp
	else:
		print "OK"


	loc_in_use_count = len(loc_in_use)
	print "\nOld Dataset - Locations in Use: {}".format(loc_in_use_count)
	if loc_in_use_count > 0:
		print "Level\tFid\tFPcode\tFName\tLevel"
		for a in admin_levels:
			loc_in_use_level = [l for l in loc_in_use if l["gateway_id"] == a.gat_id]
			for l in loc_in_use_level:
				print "{}\t{}\t{}\t{}\t{}".format(a.level, l["id"], l["p_code"], getval(l,"name"), l["level"])

if qc_type_oldnew == "new" or qc_type_oldnew == "both":
	# NEW DATASETS QC REPORT
	print "\nNew Dataset QC Check"


	print "\nNew Dataset Geometry QC Check"
	total_n_geom_err = sum([len(a.n_geom_err) for a in admin_levels])
	if total_n_geom_err > 0:
		print "Level\tType\tFtid\tFtName\tFtPcode"
		for a in admin_levels:
			for e in a.n_geom_err:
				print "{}\t{}\t{}\t{}\t{}".format(a.level, "new", e.id(), getval(e, a.nl_n_f), getval(e, a.nl_pc_f))  # Todo: check id() for postgis / shp
	else:
		print "OK"


	print "\nNew Dataset Null Pcodes QC Check"
	total_n_null_pc_err = sum([len(a.n_null_pc_err) for a in admin_levels])
	if total_n_null_pc_err > 0:
		print "Level\tType\tFtid\tFtName"
		for a in admin_levels:
			for e in a.n_null_pc_err:
				print "{}\t{}\t{}\t{}".format(a.level, "new", e.id(), getval(e, a.nl_n_f))  # Todo: check id() for postgis / shp
	else:
		print "OK"


	print "\nNew Dataset Duplicate Pcodes QC Check"
	total_n_dupl_pc_err = sum([len(a.n_dupl_pc_err) for a in admin_levels])
	if total_n_dupl_pc_err > 0:
		print "Level\tType\tFtCount\tFtids\tPcodes"
		for a in admin_levels:
			new_dupl_count = len(a.n_dupl_pc_err)
			if new_dupl_count > 0:
				print "{}\t{}\t{}\t{}\t{}".format(a.level, "new", new_dupl_count, [f.id() for f in a.n_dupl_pc_err], [getval(f, a.nl_pc_f) for f in a.n_dupl_pc_err])  # Todo: check id() for postgis / shp
	else:
		print "OK"


	print "\nNew Dataset Null Parent Pcodes QC Check"
	total_n_null_ppc_err = sum([len(a.n_null_ppc_err ) for a in admin_levels])
	if total_n_null_ppc_err > 0:
		print "Level\tType\tFtid\tPcode\tFtName"
		for a in admin_levels:
			for e in a.n_null_ppc_err:
				print "{}\t{}\t{}\t{}\t{}".format(a.level, "new", e.id(), getval(e, a.nl_pc_f), getval(e, a.nl_n_f))  # Todo: check id() for postgis / shp
	else:
		print "OK"


	print "\nNew Dataset Parent Pcodes QC Check"
	total_n_parent_err = sum([len(a.n_parent_err) for a in admin_levels])
	if total_n_parent_err > 0:
		print "Level\tType\tFid\tFPcode\tFName\tWrongParentID\tCorrectParentID\tCorrectParentPcode\tCorrectParentName"
		for a in admin_levels:
			for e in a.n_parent_err:
				print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "new", e[0].id(), getval(e[0], a.nl_pc_f), getval(e[0], a.nl_n_f), getval(e[0], a.nl_ppc_f), e[2].id(), getval(e[2], admin_levels[a.level - 1].nl_pc_f), getval(e[2], admin_levels[a.level - 1].nl_n_f))  # Todo: check id() for postgis / shp
	else:
		print "OK"

	print "\nNew Dataset No Parent QC Check"
	total_n_no_parent_err = sum([len(a.n_no_parent_err) for a in admin_levels])
	if total_n_no_parent_err > 0:
		print "Level\tType\tFid\tFPcode\tFName\tParentID"
		for a in admin_levels:
			for e in a.n_no_parent_err:
				print "{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "new", e[0].id(), getval(e[0], a.nl_pc_f), getval(e[0], a.nl_n_f), getval(e[0], a.nl_ppc_f))  # Todo: check id() for postgis / shp
	else:
		print "OK"


if qc_type_oldnew == "both":
	print "\nCross-check QC"
	for a in admin_levels:
		print "\nLevel: {}".format(a.level)
		total_diffs = len(a.cross_ag) + len(a.cross_an) + len(a.cross_b) + len(a.cross_c)
		if total_diffs > 0:
			print "CASE\tOLD PCODE\tNEW PCODE\tOLD FID\tNEW FID\tOLD NAME\tNEW NAME\tSIMILARITY"
			if len(a.cross_ag) > 0:
				for a_geom in a.cross_ag:
					print "A-geom\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(getval(a_geom[0], pc_field), getval(a_geom[1], a.nl_pc_f), getval(a_geom[0], id_field), a_geom[1].id(), getval(a_geom[0], name_field),
																	  getval(a_geom[1], a.nl_n_f), str(round(a_geom[2], 1)) + "/" + str(round(a_geom[3], 1)))
			if len(a.cross_an) > 0:
				for a_name in a.cross_an:
					print "A-name\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(getval(a_name[0], pc_field), getval(a_name[1], a.nl_pc_f), getval(a_name[0], id_field), a_name[1].id(), getval(a_name[0], name_field),
																	  getval(a_name[1], a.nl_n_f), str(round(a_name[2], 1)))
			if len(a.cross_b) > 0:
				for b in a.cross_b:
					print "B-remov\t{}\t\t{}\t\t{}\t".format(getval(b, pc_field), getval(b, id_field), getval(b, name_field))
			if len(a.cross_c) > 0:
				for c in a.cross_c:
					print "C-added\t\t{}\t\t{}\t\t{}".format(getval(c, a.nl_pc_f), c.id(), getval(c, a.nl_n_f))
		else:
			print "OK"


	print "\nRemap Summary"
	total_fts_caseB = sum([len(a.cross_b) for a in admin_levels])
	if total_fts_caseB == 0:
		print "Remap is not required - no removed Locations"
	else:
		total_caseBr = sum([len(a.cross_br) for a in admin_levels])
		if total_caseBr > 0:
			print "\nCase B - Removed Locations with suggested Remaps: {}".format(total_caseBr)
			header_br = "Lev\tOldFid\tNewFid\told_pcode\tnew_pcode\tOldFtName\tNewFtName\tNameSim\tGeomSimOld\tGeomSimNew"
			header_br_csv = "Lev;OldFid;NewFid;old_pcode;new_pcode;OldFtName;NewFtName;NameSim;GeomSimOld;GeomSimNew"
			print header_br
			for a in admin_levels:
				# write remap tables to csv files
				if len(a.cross_br) > 0:
					outpath = os.path.join(
						os.path.dirname(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri())),
						"{}_adm{}_{}_remap.csv".format(a.nl_n, a.level, qc_type))
					f = open(outpath, 'w')
					f.write("{}\n".format(header_br_csv))

				for br in a.cross_br:
					line_br = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, getval(br[0], id_field), br[1].id(), getval(br[0], pc_field), getval(br[1], a.nl_pc_f),
																		  getval(br[0], name_field), getval(br[1], a.nl_n_f), round(br[2], 2),
																	  round(br[3], 2), round(br[4], 2))
					line_br_csv = "{};{};{};{};{};{};{};{};{};{}".format(a.level, getval(br[0], id_field), br[1].id(), getval(br[0], pc_field), getval(br[1], a.nl_pc_f),
																		  getval(br[0], name_field), getval(br[1], a.nl_n_f), round(br[2], 2),
																	  round(br[3], 2), round(br[4], 2))

					print line_br
					if len(a.cross_br) > 0:
						f.write("{}\n".format(line_br_csv))
				if len(a.cross_br) > 0:
					f.close()

		total_caseBRiU = sum([len(a.cross_briu) for a in admin_levels])
		if total_caseBRiU > 0:
			print "\nCase BRiU - Removed Locations with suggested Remaps in Use: {}".format(total_caseBRiU)
			header_briu = "Lev\tOldFid\tNewFid\told_pcode\tnew_pcode\tOldFtName\tNewFtName\tNameSim\tGeomSimOld\tGeomSimNew"
			header_briu_csv = "Lev;OldFid;NewFid;old_pcode;new_pcode;OldFtName;NewFtName;NameSim;GeomSimOld;GeomSimNew"
			print header_briu
			for a in admin_levels:
				# write remap tables to csv files
				if len(a.cross_briu) > 0:
					outpath = os.path.join(
						os.path.dirname(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri())),
						"{}_adm{}_{}_remap_in_use.csv".format(a.nl_n, a.level, qc_type))
					f = open(outpath, 'w')
					f.write("{}\n".format(header_briu_csv))

				for br in a.cross_briu:
					line_briu = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, getval(br[0], id_field), br[1].id(), getval(br[0], pc_field), getval(br[1], a.nl_pc_f),
																		  getval(br[0], name_field), getval(br[1], a.nl_n_f), round(br[2], 2),
																	  round(br[3], 2), round(br[4], 2))
					line_briu_csv = "{};{};{};{};{};{};{};{};{};{}".format(a.level, getval(br[0], id_field), br[1].id(), getval(br[0], pc_field), getval(br[1], a.nl_pc_f),
																		  getval(br[0], name_field), getval(br[1], a.nl_n_f), round(br[2], 2),
																	  round(br[3], 2), round(br[4], 2))

					print line_briu
					if len(a.cross_briu) > 0:
						f.write("{}\n".format(line_briu_csv))
				if len(a.cross_briu) > 0:
					f.close()


		total_caseBnR = sum([len(a.cross_bnr) for a in admin_levels])
		print "\nCase BnR - Removed Locations with no Remap:\t{}".format(total_caseBnR)
		if total_caseBnR > 0:
			print "Level\tFtid\tPCode\tFtName"
			for a in admin_levels:
				for bnr in a.cross_bnr:
					print "{}\t{}\t{}\t{}".format(a.level, getval(bnr, id_field), getval(bnr, pc_field), getval(bnr, name_field))

		total_caseBmR = sum([len(a.cross_bmr) for a in admin_levels])
		print "\nCase BmR - Removed Locations with multiple Remaps:\t{}".format(total_caseBmR)
		if total_caseBmR > 0:
			print "Level\tFtid\tPCode\tFtName"
			for a in admin_levels:
				for bmr in a.cross_bmr:
					print "{}\t{}\t{}\t{}".format(a.level, getval(bmr, id_field), getval(bmr, pc_field), getval(bmr, name_field))

		total_caseBnRiU = sum([len(a.cross_bnriu) for a in admin_levels])
		print "\nCase BnRiU - Removed Locations in Use with no Remap:\t{}".format(total_caseBnRiU)
		if total_caseBnRiU > 0:
			print "Level\tFtid\tPCode\tFtName"
			for a in admin_levels:
				for bnriu in a.cross_bnriu:
					print "{}\t{}\t{}\t{}".format(a.level, getval(bnriu, id_field), getval(bnriu, pc_field), getval(bnriu, name_field))


print "\nGeneral Settings:"
print "Country: {} (ISO2: {}, ISO3: {})".format(country, iso2, iso3)
print "Workspace ID: {}".format(workspace_id)  #  ToDo: add API call to check workspace ID and name https://etools-staging.unicef.org/api/v2/workspaces/
print "Area threshold for geom intersections: {}".format(thres)
print "Geom similarity threshold: {}% [0-100%]".format(geomsim_treshold)
print "Name similarity threshold: {} [0-1]".format(textsim_treshold)
print "Geom similarity threshold (for remap): {}% [0-100%]".format(geomsim_remap_treshold)
print "Point distance threshold (in meters): {}".format(point_dist_treshold)
print "Locations in use URL: https://etools.unicef.org/api/management/gis/in-use/?country_id={}".format(workspace_id)

if qc_type_oldnew == "both":
	print "\nInput Data Overview"
	for a in admin_levels:
		print "Level: {}".format(a.level)
		print "{}\t{}".format([old_lyr.name() for old_lyr in old_lyrs],a.nl.name())
		print "{}\t{}".format(len(a.ofts), len(a.nfts))


	print "\nGeneral Summary"
	print "Level\tAdmin Name\tNew Layer\tNLPCodeF\tNLNameF\tNLPPcodeF\tDateModif\tGate Id\tNew FtCount\tOld FtCount"
	for a in admin_levels:
		print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, a.name, a.nl.name(), a.nl_pc_f, a.nl_n_f, a.nl_ppc_f, datetime.fromtimestamp(os.path.getmtime(a.nl.dataProvider().dataSourceUri().split("|")[0])), a.gat_id, len(a.nfts), len(a.ofts))
	total_o_fts = sum([len(a.ofts) for a in admin_levels])
	total_n_fts = sum([len(a.nfts) for a in admin_levels])

	print "Total number of {} Locations: {}".format(old_label, total_o_fts)
	print "Total number of new Locations: {}".format(total_n_fts)


	old_fts_count = 0
	for old_lyr in old_lyrs:
		old_fts_count += len(list(old_lyr.getFeatures()))  # ToDo test this feature

	if old_fts_count != total_o_fts:
		print "WARNING: {} old Locations are not associated with any of the admin levels!".format(old_fts_count - total_o_fts)


if qc_type_oldnew == "old" or qc_type_oldnew == "both":
	print "\nInternal QC Summary - {} Datasets".format(old_label.title())
	print "Level\tGeomErr\tOverlaps\tNull Pcode\tDupl Pcode\tNull PPc\tWrong PPc\tNo Parent\tQC Status"
	for a in admin_levels:
		print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level,
																						  len(a.o_geom_err),
																						  len(a.o_overlap_err),
																						  len(a.o_null_pc_err),
																						  len(a.o_dupl_pc_err),
																						  len(a.o_null_ppc_err),
																						  len(a.o_parent_err),
																						  len(a.o_no_parent_err),
																						  a.o_qc_stat_int)

if qc_type_oldnew == "new" or qc_type_oldnew == "both":
	print "\nInternal QC Summary - New Datasets"
	print "Level\tGeomErr\tOverlaps\tNull Pcode\tDupl Pcode\tNull PPc\tWrong PPc\tNo Parent\tQC Status"
	for a in admin_levels:
		print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level,
																						  len(a.n_geom_err),
																						  len(a.n_overlap_err),
																						  len(a.n_null_pc_err),
																						  len(a.n_dupl_pc_err),
																						  len(a.n_null_ppc_err),
																						  len(a.n_parent_err),
																						  len(a.n_no_parent_err),
																						  a.n_qc_stat_int)

if qc_type_oldnew == "both":
	print "\nCross-Check QC Summary"
	print "Lev\t{}\tNew\tA\tB\tC\tAg\tAn\tBr\tBRiU\tBnR\tBmR\tBnRiU\tQC".format(old_label.title())
	for a in admin_levels:
		count_old = len(a.ofts)
		count_new = len(a.nfts)
		count_a = len(a.cross_a)
		count_ag = len(a.cross_ag)
		count_an = len(a.cross_an)
		count_b = len(a.cross_b)
		count_c = len(a.cross_c)
		count_br = len(a.cross_br)
		count_briu = len(a.cross_briu)
		count_bnr = len(a.cross_bnr)
		count_bmr = len(a.cross_bmr)
		count_bnriu = len(a.cross_bnriu)

		error_count = count_bmr + count_bnriu  # BmR + BnRiU count
		warning_count = count_ag + count_an + count_b  # AG + AN + B
		if error_count == 0 and warning_count == 0:
			cross_qc_status = "OK"
		elif error_count == 0 and warning_count > 0:
			cross_qc_status = "CHECK"
		elif error_count > 0:
			cross_qc_status = "ERROR"
		print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, count_old, count_new, count_a, count_b, count_c, count_ag, count_an, count_br, count_briu, count_bnr, count_bmr, count_bnriu, cross_qc_status)

	print "\nLegend:"
	print "{} - Locations currently available in eTools".format(old_label.title())
	print "New - new Locations to be uploaded to eTools"
	print "A - matching Locations in both {} and New datasets (i.e. same Pcode)".format(old_label.title())
	print "B - Locations (Pcodes) available in {} dataset (eTools) but not available in New dataset (HDX etc.) - i.e. 'Removed locations'".format(old_label.title())
	print "C - Locations (Pcodes) available in New dataset (HDX etc.) but not available in Old dataset (eTools) - i.e. 'Added locations'"
	print "Ag - matching Locations (A) with different geometry"
	print "An - matching Locations (A) with different names"
	print "Br - removed Locations (B) that can be remapped (matched) with Locations in New dataset"
	print "BRiU - removed Locations (B) that can be remapped (matched) with Locations in New dataset that are in use"
	print "BnR - removed Locations (B) that cannot be remapped (matched) with Locations in New dataset"
	print "BmR - removed Locations (B) that have more than one remapped (matching) Locations in New dataset (not allowed)"
	print "BnRiU - 'BnR' Locations that are in use (referenced to interventions or trips)"
	print "\nQC - OK - no errors, CHECK - manual check required, ERROR - major errors, NO DATA - no locations available"

endDate = datetime.utcnow()
print "\nCompleted: {}".format(endDate)
print "Total processing time: {}".format(endDate - startDate)

