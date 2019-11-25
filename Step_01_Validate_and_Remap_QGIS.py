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


class AdminLevel:
	def __init__(self, level, name, gat_id, nl_n, nl_pc_f, nl_n_f, nl_ppc_f, nl, new_fts, old_fts, n_geom_err, n_overlap_err, n_null_name_err, n_null_pc_err, n_dupl_pc_err, n_null_ppc_err, n_parent_err, o_geom_err , o_overlap_err, o_null_name_err, o_null_pc_err, o_dupl_pc_err, o_null_ppc_err, o_parent_err, n_no_parent_err, o_no_parent_err, cross_a, cross_ag, cross_an, cross_b, cross_br, cross_briu, cross_bnr, cross_bmr, cross_bnriu, cross_c, cross_qc, cross_remaps, n_qc_stat_int="UNKNOWN", o_qc_stat_int="UNKNOWN"):
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
		self.n_null_name_err = n_null_name_err
		self.n_null_pc_err = n_null_pc_err
		self.n_dupl_pc_err = n_dupl_pc_err
		self.n_null_ppc_err = n_null_ppc_err
		self.n_parent_err = n_parent_err
		self.n_no_parent_err = n_no_parent_err
		self.n_qc_stat_int = n_qc_stat_int
		self.o_geom_err = o_geom_err
		self.o_overlap_err = o_overlap_err
		self.o_null_name_err = o_null_name_err
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
		self.cross_remaps = cross_remaps  # cross-check remaps

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
		filename = "{}_adm-{}_{}_{}_{}_{}.png".format(country, level, qc_type, lyr_type, lyr_name, '{0:%Y}{0:%m}{0:%d}'.format(startDate))
	else:
		filename = "{}_adm-{}_{}_{}_{}_{}.png".format(country, level, qc_type, lyr_type, lyr_name, '{0:%Y}{0:%m}{0:%d}'.format(startDate))

	path = os.path.join(outdir, filename)

	# save image
	image.save(path, "png")
	# print "Snapshot for level {} created at {}".format(l, path)


# definition of admin levels and input layers


admin_levels = []
input_levels = []

################################
########### SETTINGS ###########

input_levels.append([0, 'Country', 0, 'afg_admbnd_adm0_pol', 'HRpcode', 'HRname', None])
input_levels.append([1, 'Province', 1, 'afg_admbnd_adm1_pol', 'HRpcode', 'HRname', 'HRparent'])
input_levels.append([2, 'District', 2, 'afg_admbnd_adm2_pol', 'HRpcode', 'HRname', 'HRparent'])
country = 'Afghanistan'
iso2 = 'AF'
iso3 = 'AFG'
workspace_id = 24

qc_type = 'before'  # options: "before" - BEFORE UPLOAD or "after" - AFTER UPLOAD
qc_type_oldnew = 'both'  # options: "old" - validate only data from eTools, "new" - validate only data from HDX/GADM, "both" - both old and new + cross-check

# input Pcode, Parent Pcode and Name fields for old layer
id_field = "uuid"
pc_field = "p_code"
pid_field = "parent_pco"
name_field = "name"
old_lyr_name =  "Afghanistan_loc_geom_before".format(country, qc_type)

########### SETTINGS ###########
################################

for i in input_levels:
	admin_levels.append(AdminLevel(i[0], i[1], i[2], i[3], i[4], i[5], i[6],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))


old_label = "old"
if qc_type == "after":
	old_label = "updated"


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
pcodes_in_use = []

old_lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if old_lyr_name in layer.name()]

# settings for cross-check
geomsim_treshold = 90
textsim_treshold = 80
geomsim_treshold_same_name = 20
geomsim_remap_treshold = 1
point_dist_treshold = 1  # in meters

startDate = datetime.utcnow()


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

	new_fts = {feature.id(): feature for (feature) in new_lyr.getFeatures()}  # [ft for ft in new_lyr.getFeatures()]

	admin_level.nl = new_lyr
	admin_level.nfts = new_fts

	old_fts = {}
	if qc_type_oldnew == "old" or qc_type_oldnew == "both":
		old_fts = {feature.id(): feature for (feature) in old_lyrs[0].getFeatures() if feature["admin_leve"] == admin_level.gat_id}  # [ft for ft in new_lyr.getFeatures()]

	# TODO: checking both points and polygons...
	for old_lyr in old_lyrs:
		if admin_level.gat_id or admin_level.gat_id == 0:
			old_lyr.setSubsetString("\"admin_leve\"={}".format(admin_level.gat_id))
			old_fts.update({feature.id(): feature for (feature) in old_lyr.getFeatures()})  # [ft for ft in old_lyr.getFeatures()]

		elif admin_level.gat_id is None:
			old_lyr.setSubsetString("\"admin_leve\" is NULL")  # TODO: Should not we skip adding features if gateway_id is None?
			old_fts.update({feature.id(): feature for (feature) in old_lyr.getFeatures()})  # [ft for ft in old_lyr.getFeatures()]
	admin_level.ofts = old_fts

	for nft in new_fts.values():
		nft_pc = getval(nft, admin_level.nl_pc_f)
		if nft_pc:
			new_pcodes.append(nft_pc)
	for oft in old_fts.values():
		oft_pc = getval(oft, pc_field)
		if oft_pc:
			old_pcodes.append(oft_pc)
	saveimg(new_lyr.id(), new_lyr.name(), admin_level.level, "new")
	for old_lyr in old_lyrs:
		saveimg(old_lyr.id(), old_lyr.name(), admin_level.level, "old")
		old_lyr.setSubsetString("")

if qc_type_oldnew == "old" or qc_type_oldnew == "both":
	# read locations in use # ToDo replace with API call once tested
	json_path = os.path.join(os.path.dirname(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri())), "{}_loc_in_use.json".format(country))
	with open(json_path) as json_data:
		loc_in_use = json.load(json_data)
		for admin_level in admin_levels:
			pcodes_in_use.append([liu['p_code'] for liu in loc_in_use if liu['admin_leve'] == admin_level.gat_id])



def printlog(line):
	print line
	flog.write("{}\n".format(line))


# Start logging
log_path = os.path.join(os.path.dirname(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri())), "{}_qc_log_{}_{}.txt".format(country, qc_type, startDate.strftime("%Y%m%d_%H%M%S")))

flog = open(log_path, 'w', 2)


printlog("############################")
printlog("Locations for eTools QC Check")
printlog("############################")

printlog("Started: {}\n".format(startDate))

# list duplicated pcodes
new_duplpcodes = ["'" + item + "'" for item, count in collections.Counter(new_pcodes).items() if count > 1]
new_duplquery = ''
old_duplpcodes = ["'" + item + "'" for item, count in collections.Counter(old_pcodes).items() if count > 1]
old_duplquery = ''

for nd in new_duplpcodes:
	new_duplquery = ",".join(list(new_duplpcodes))
for od in old_duplpcodes:
	old_duplquery = ",".join(list(old_duplpcodes))


def qc(admin_level, fts, pfts, lyr_type, fts_index, pfts_index):
	# Geometry QC Check setup
	# create a memory layer for intersections
	mem_layer = QgsVectorLayer("MultiPolygon?crs=epsg:4326", "level_{}_{}_overlaps".format(admin_level.level, lyr_type), "memory")
	mem_layer.startEditing()
	pr = mem_layer.dataProvider()
	pr.addAttributes(
		[QgsField("lyrid", QVariant.String), QgsField("fid1", QVariant.Int), QgsField("fid2", QVariant.Int)])


	for ft in fts.values():
		# printlog("Null Name QC Check")
		# Null Name QC Check
		if lyr_type == "new":
			ftname = getval(ft, admin_level.nl_n_f)  # works for shapefiles
			if ftname is 'NULL' or ftname == '': admin_level.n_null_name_err.append(ft)
		else:
			ftname = getval(ft, name_field)
			if ftname is 'NULL' or ftname == '': admin_level.o_null_name_err.append(ft)

		ftgeom = ft.geometry()

		if lyr_type == "new":
			ftpc = getval(ft, admin_level.nl_pc_f)  # works for shapefiles
		else:
			ftpc = getval(ft, pc_field)

		# printlog("{}\t{}\t{}".format(ft.id(),ftname, ftpc))

		# printlog("Null Pcode QC Check")
		# Null Pcode QC Check
		if ftpc is 'NULL' or ftpc == '':  # works for shapefiles
			if lyr_type == "new":
				admin_level.n_null_pc_err.append(ft)
			else:
				admin_level.o_null_pc_err.append(ft)

		# printlog("Null Parent Pcode QC Check")
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
			# printlog("Geometry QC Check setup")
			# Geometry QC Check setup
			if geom_qc == 1:
				near_ids = fts_index.intersects(ft.geometry().boundingBox())

				for nid in near_ids:
					nft = fts[nid]
					if ft.geometry() and nft.geometry() and (ft.id() != nft.id()):
						if ft.geometry().intersects(nft.geometry()):
							intersect_geom = ft.geometry().intersection(nft.geometry())
							if intersect_geom and intersect_geom.area() > thres:
								# print "{} - ABOVE THRES: {}".format(admin_level.level, intersect_geom.area())
								feature = QgsFeature()
								fields = mem_layer.pendingFields()
								feature.setFields(fields, True)
								feature.setAttributes([0, ft.id(), nft.id()])
								if intersect_geom.wkbType() == 777:
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
									admin_level.o_overlap_err.append([ft, nft, intersect_geom])
				mem_layer.commitChanges()
				if lyr_type == "new":
					if len(admin_level.n_overlap_err) > 0:
						QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
				else:
					if len(admin_level.o_overlap_err) > 0:
						QgsMapLayerRegistry.instance().addMapLayer(mem_layer)

			# printlog("Parent Pcodes QC Check")
			# Parent Pcodes QC Check
			if admin_level.level != 0 and parent_qc == 1:
				# printlog("Parent Pcodes QC Check-0")
				ft_centr = ftgeom.pointOnSurface()
				# printlog("Parent Pcodes QC Check-1")
				if lyr_type == "new":
					ftppc = getval(ft, admin_level.nl_ppc_f)
					ftparent = ftppc
				else:
					ftpid = getval(ft, pid_field)
					ftparent = ftpid

				# printlog("Parent Pcodes QC Check-2")
				parent_found_flag = 0

				near_pids = pfts_index.intersects(ft.geometry().boundingBox())
				# printlog(near_pids)

				for npid in near_pids:
					# printlog("Parent Pcodes QC Check-3")
					pft = pfts[npid]
					pftgeom = pft.geometry()
					if pftgeom:
						# printlog("Parent Pcodes QC Check-4")
						if ft_centr.intersects(pftgeom):
							# printlog("Parent Pcodes QC Check-5")
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

	# printlog("Duplicated Pcode QC Check")
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

	l = admin_level.level

	# create spatial index for fts and pfts
	nfts_index = QgsSpatialIndex()
	npfts_index = QgsSpatialIndex()
	ofts_index = QgsSpatialIndex()
	opfts_index = QgsSpatialIndex()

	# qc for new locations
	# printlog("New QC Check")
	if qc_type_oldnew == "new" or qc_type_oldnew == "both":
		for nf in admin_level.nfts.values():
			nfts_index.insertFeature(nf)
		for npf in admin_levels[admin_level.level - 1].nfts.values():
			npfts_index.insertFeature(npf)
		qc(admin_level, admin_level.nfts, admin_levels[admin_level.level - 1].nfts, "new", nfts_index, npfts_index)

	# printlog("Old QC Check")
	if qc_type_oldnew == "old" or qc_type_oldnew == "both":
		for of in admin_level.ofts.values():
			ofts_index.insertFeature(of)
		for opf in admin_levels[admin_level.level - 1].ofts.values():
			opfts_index.insertFeature(opf)
		qc(admin_level, admin_level.ofts, admin_levels[admin_level.level - 1].ofts, "old", ofts_index, opfts_index)

	######################
	# Cross-check new and old data
	######################

	# build spatial index for new features
	n_index = QgsSpatialIndex()
	for f in admin_levels[l].nl.getFeatures():
		n_index.insertFeature(f)

	# get old and new features into dictionaries
	new_fts = {feature.id(): feature for (feature) in admin_levels[l].nl.getFeatures()}  # [ft for ft in new_lyr.getFeatures()]
	old_fts = {feature.id(): feature for (feature) in admin_levels[l].ofts.values()}  # [ft for ft in old_lyr.getFeatures()]

	old2new_remaps = []

	# loop through all "old" admin boundaries to get matching "new" boundary
	for oft in old_fts.values():
		old2new_remap_overlaps = []
		old2new_remap_neighbors = []
		oft_centr = oft.geometry().pointOnSurface()
		match_found = 0

		# first try intersecting with nearest neighbors
		near_ids = n_index.intersects(oft.geometry().boundingBox())
		for nid in near_ids:
			nnft = new_fts[nid]
			nn_intersect_geom = oft.geometry().intersection(nnft.geometry())
			if nn_intersect_geom.area() > 0:
				o_perc_overlap = nn_intersect_geom.area() / oft.geometry().area() * 100
				n_perc_overlap = nn_intersect_geom.area() / nnft.geometry().area() * 100
				old_name = getval(oft, name_field)
				new_name = getval(nnft, admin_level.nl_n_f)
				name_sim = SequenceMatcher(None, old_name, new_name).ratio() * 100

				old2new_remap_overlaps.append([oft, nnft, o_perc_overlap, n_perc_overlap, name_sim])
				# print("{}\t{}\t{}".format(oft[old_pcode_field],nnft[new_pcode_field],perc_overlap))
				match_found += 1

		# do if no intersecting neighbors found
		if match_found == 0:

			# loop through all "new" admin boundaries and calculate distance
			for nft in new_fts.values():
				dist = oft.geometry().pointOnSurface().distance(
					nft.geometry())  # ToDo: measure distance to the nearset edge not between centroids
				old2new_remap_neighbors.append([oft, nft, dist, "neigbor"])
		# print("{}\t{}\t{}".format(oft[old_pcode_field],nft[new_pcode_field],dist))

		# find best match
		best_match = []


		if match_found == 0:
			# get the closest new boundary as the best match
			best_match = min(old2new_remap_neighbors, key=lambda x: x[2])
			dist = best_match[2]
		else:
			# check if some otherlapping boundaries have exact name
			matching_names = [f for f in old2new_remap_overlaps if (f[4] > textsim_treshold) and (f[2] > geomsim_treshold_same_name or f[3] > geomsim_treshold_same_name)]
			if len(matching_names) == 1:
				best_match = matching_names[0]
			elif len(matching_names) > 1:
				matching_names_high_overlaps = [f for f in matching_names]
				# get a new boundary which overlaps the largest portion of the "old" boundary as the best match
				best_match = max(matching_names_high_overlaps, key=lambda x: x[2])
			else:
				# get a new boundary which overlaps the largest portion of the "old" boundary as the best match
				best_match = max(old2new_remap_overlaps, key=lambda x: x[2])
			dist = 0

		# get "old" and "new" matching boundaries
		oft = best_match[0]
		nft = best_match[1]
		old_name = getval(oft, name_field)
		old_pcode = getval(oft, pc_field)
		old_uuid = getval(oft, 'uuid')
		new_name = getval(nft, admin_level.nl_n_f)
		new_pcode = getval(nft, admin_level.nl_pc_f)

		# intersect both geometries and calculate similarities
		intersect_geom = nft.geometry().intersection(oft.geometry())
		geomsim_old = (intersect_geom.area() / oft.geometry().area() * 100)
		geomsim_new = (intersect_geom.area() / nft.geometry().area() * 100)
		centr_dist = calc_distance(oft.geometry().pointOnSurface().asPoint().y(),
								   oft.geometry().pointOnSurface().asPoint().x(),
								   nft.geometry().pointOnSurface().asPoint().y(),
								   nft.geometry().pointOnSurface().asPoint().x())

		# calculate name similarity
		name_sim = SequenceMatcher(None, old_name, new_name).ratio() * 100

		# add a pair of "old" and "new" polygons to the remap table
		old2new_remaps.append(
			[old_uuid, old_pcode, new_pcode, old_pcode == new_pcode, old_name, new_name, name_sim, geomsim_old, geomsim_new, dist, centr_dist, 'OK'])

	admin_level.cross_remaps = old2new_remaps

#Print workspace / source path
parent_dir3 = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri()))))
parent_dir2 = os.path.basename(os.path.dirname(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri())))
parent_dir1 = os.path.basename(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri()))
parent_dir = os.path.join(parent_dir3, parent_dir2, parent_dir1)
printlog("WORKSPACE: {}\n\n".format(parent_dir))


# OLD DATASETS QC REPORT

if qc_type_oldnew == "old" or qc_type_oldnew == "both":
	printlog("\nOld Dataset QC Check")

	printlog("\nOld Dataset Geometry QC Check")
	total_o_geom_err = sum([len(a.o_geom_err) for a in admin_levels])
	if total_o_geom_err > 0:
		printlog("Level\tType\tFtid\tFtName\tFtPcode")
		for a in admin_levels:
			for e in a.o_geom_err:
				printlog("{}\t{}\t{}\t{}\t{}".format(a.level, "old", e.id(), getval(e, name_field), getval(e, pc_field)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")


	printlog("\nOld Dataset Null Name QC Check")
	total_o_null_name_err = sum([len(a.o_null_name_err) for a in admin_levels])
	if total_o_null_name_err > 0:
		printlog("Level\tType\tFtid\tFtPcode\tFtName")
		for a in admin_levels:
			for e in a.o_null_name_err:
				printlog("{}\t{}\t{}\t{}\t{}".format(a.level, "old", e.id(), getval(e, pc_field), getval(e, name_field)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")


	printlog("\nOld Dataset Null Pcodes QC Check")
	total_o_null_pc_err = sum([len(a.o_null_pc_err) for a in admin_levels])
	if total_o_null_pc_err > 0:
		printlog("Level\tType\tFtid\tFtName")
		for a in admin_levels:
			for e in a.o_null_pc_err:
				printlog("{}\t{}\t{}\t{}".format(a.level, "old", e.id(), getval(e, name_field)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")

	printlog("\nOld Dataset Duplicate Pcodes QC Check")
	total_o_dupl_pc_err = sum([len(a.o_dupl_pc_err) for a in admin_levels])
	if total_o_dupl_pc_err > 0:
		printlog("Level\tType\tFtCount\tFtids\tPcodes")
		for a in admin_levels:
			old_dupl_count = len(a.o_dupl_pc_err)
			if old_dupl_count > 0:
				printlog("{}\t{}\t{}\t{}\t{}".format(a.level, "old", old_dupl_count, [f.id() for f in a.o_dupl_pc_err], [getval(f, pc_field) for f in a.o_dupl_pc_err]))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")


	printlog("\nOld Dataset Null Parent Pcodes QC Check")
	total_o_null_ppc_err = sum([len(a.o_null_ppc_err) for a in admin_levels])
	if total_o_null_ppc_err > 0:
		printlog("Level\tType\tFtid\tPcode\tFtName")
		for a in admin_levels:
			for e in a.o_null_ppc_err:
				printlog("{}\t{}\t{}\t{}\t{}".format(a.level, "old", e.id(), getval(e, pc_field), getval(e, name_field)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")

	printlog("\nOld Dataset Parent Pcodes QC Check")
	total_o_parent_err = sum([len(a.o_parent_err) for a in admin_levels])
	if total_o_parent_err > 0:
		printlog("Level\tType\tFid\tFPcode\tFName\tWrongParentID\tCorrectParentID\tCorrectParentPcode\tCorrectParentName")
		for a in admin_levels:
			for e in a.o_parent_err:
				printlog("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "old", e[0].id(), getval(e[0], pc_field), getval(e[0], name_field), getval(e[0], pid_field), e[2].id(), getval(e[2], pc_field), getval(e[2], name_field)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")

	printlog("\nOld Dataset No Parent QC Check")
	total_o_no_parent_err = sum([len(a.o_no_parent_err) for a in admin_levels])
	if total_o_no_parent_err > 0:
		printlog("Level\tType\tFid\tFPcode\tFName\tParentID")
		for a in admin_levels:
			for e in a.o_no_parent_err:
				printlog("{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "old", e[0].id(), getval(e[0], pc_field), getval(e[0], name_field), getval(e[0], pid_field)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")


	loc_in_use_count = len(loc_in_use)
	printlog("\nOld Dataset - Locations in Use: {}".format(loc_in_use_count))
	if loc_in_use_count > 0:
		printlog("Level\tFid\tFPcode\tFName\tLevel")
		for a in admin_levels:
			loc_in_use_level = [l for l in loc_in_use if l["gateway_id"] == a.gat_id]
			for l in loc_in_use_level:
				printlog("{}\t{}\t{}\t{}\t{}".format(a.level, l["id"], l["p_code"], getval(l,"name"), l["level"]))

# NEW DATASETS QC REPORT
if qc_type_oldnew == "new" or qc_type_oldnew == "both":
	printlog("\nNew Dataset QC Check")

	printlog("\nNew Dataset Geometry QC Check")
	total_n_geom_err = sum([len(a.n_geom_err) for a in admin_levels])
	if total_n_geom_err > 0:
		printlog("Level\tType\tFtid\tFtName\tFtPcode")
		for a in admin_levels:
			for e in a.n_geom_err:
				printlog("{}\t{}\t{}\t{}\t{}".format(a.level, "new", e.id(), getval(e, a.nl_n_f), getval(e, a.nl_pc_f)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")


	printlog("\nNew Dataset Null Name QC Check")
	total_n_null_name_err = sum([len(a.n_null_name_err) for a in admin_levels])
	if total_n_null_name_err > 0:
		printlog("Level\tType\tFtid\tFtPcode\tFtName")
		for a in admin_levels:
			for e in a.n_null_name_err:
				printlog("{}\t{}\t{}\t{}\t{}".format(a.level, "new", e.id(), getval(e, a.nl_pc_f), getval(e, a.nl_n_f)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")


	printlog("\nNew Dataset Null Pcodes QC Check")
	total_n_null_pc_err = sum([len(a.n_null_pc_err) for a in admin_levels])
	if total_n_null_pc_err > 0:
		printlog("Level\tType\tFtid\tFtName")
		for a in admin_levels:
			for e in a.n_null_pc_err:
				printlog("{}\t{}\t{}\t{}".format(a.level, "new", e.id(), getval(e, a.nl_n_f)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")

	printlog("\nNew Dataset Duplicate Pcodes QC Check")
	total_n_dupl_pc_err = sum([len(a.n_dupl_pc_err) for a in admin_levels])
	if total_n_dupl_pc_err > 0:
		printlog("Level\tType\tFtCount\tFtids\tPcodes")
		for a in admin_levels:
			new_dupl_count = len(a.n_dupl_pc_err)
			if new_dupl_count > 0:
				printlog("{}\t{}\t{}\t{}\t{}".format(a.level, "new", new_dupl_count, [f.id() for f in a.n_dupl_pc_err], [getval(f, a.nl_pc_f) for f in a.n_dupl_pc_err]))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")

	printlog("\nNew Dataset Null Parent Pcodes QC Check")
	total_n_null_ppc_err = sum([len(a.n_null_ppc_err ) for a in admin_levels])
	if total_n_null_ppc_err > 0:
		printlog("Level\tType\tFtid\tPcode\tFtName")
		for a in admin_levels:
			for e in a.n_null_ppc_err:
				printlog("{}\t{}\t{}\t{}\t{}".format(a.level, "new", e.id(), getval(e, a.nl_pc_f), getval(e, a.nl_n_f)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")

	printlog("\nNew Dataset Parent Pcodes QC Check")
	total_n_parent_err = sum([len(a.n_parent_err) for a in admin_levels])
	if total_n_parent_err > 0:
		printlog("Level\tType\tFid\tFPcode\tFName\tWrongParentID\tCorrectParentID\tCorrectParentPcode\tCorrectParentName")
		for a in admin_levels:
			for e in a.n_parent_err:
				printlog("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "new", e[0].id(), getval(e[0], a.nl_pc_f), getval(e[0], a.nl_n_f), getval(e[0], a.nl_ppc_f), e[2].id(), getval(e[2], admin_levels[a.level - 1].nl_pc_f), getval(e[2], admin_levels[a.level - 1].nl_n_f)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")

	printlog("\nNew Dataset No Parent QC Check")
	total_n_no_parent_err = sum([len(a.n_no_parent_err) for a in admin_levels])
	if total_n_no_parent_err > 0:
		printlog("Level\tType\tFid\tFPcode\tFName\tParentID")
		for a in admin_levels:
			for e in a.n_no_parent_err:
				printlog("{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "new", e[0].id(), getval(e[0], a.nl_pc_f), getval(e[0], a.nl_n_f), getval(e[0], a.nl_ppc_f)))  # Todo: check id() for postgis / shp
	else:
		printlog("OK")


if qc_type_oldnew == "both":
	printlog("\nCross-check QC")
	for a in admin_levels:
		printlog("\nLevel: {}".format(a.level))

		etools_remap_count = len([f for f in a.cross_remaps if f[1] in pcodes_in_use[a.level] and (f[1] != f[2])])

		header_csv = "old_uuid\told_pcode\tnew_pcode\tpcode_check\told_name\tnew_name\tname_sim\tgeomsim_old\tgeomsim_new\tdis_dd\tcentr_dist_m\tpCodeQC\tNameQC\tGeomQC\tInUse"
		out_dir = os.path.abspath(os.path.join(os.path.join(admin_levels[0].nl.dataProvider().dataSourceUri(), os.pardir), os.pardir))
		outpath = os.path.join(out_dir, "{}_remap_{}.txt".format(a.nl_n, startDate.strftime("%Y%m%d_%H%M%S")))

		if qc_type == "before":
			# write a remap table to txt/csv file
			f = open(outpath, 'w')
			f.write("{}\n".format(header_csv))

		if etools_remap_count > 0:
			outpath_in_use_for_etools = os.path.join(out_dir, "{}_remap_in_use_for_etools_{}.txt".format(a.nl_n, startDate.strftime("%Y%m%d_%H%M%S")))
			fiufe = open(outpath_in_use_for_etools, 'w')
			fiufe.write("{}\n".format(header_csv))
		printlog(header_csv)

		for ln in a.cross_remaps:
			pCodeQC = "check"
			nameQC = "check"
			geomQC = "check"
			inuse = 0
			if ln[1] == ln[2]:
				pCodeQC = "OK"
			if ln[6] > textsim_treshold:
				nameQC = "OK"
			if ln[7] > geomsim_treshold and ln[8] > geomsim_treshold:
				geomQC = "OK"
			if ln[1] in pcodes_in_use[a.level]:
				inuse = 1


			csv_output = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(ln[0], ln[1], ln[2], ln[3], ln[4],
																			 ln[5], ln[6], ln[7], ln[8], ln[9], ln[10], pCodeQC, nameQC, geomQC, inuse)
			if qc_type == "before":
				f.write("{}\n".format(csv_output))
			if etools_remap_count > 0:
				if ln[1] in pcodes_in_use[a.level] and (pCodeQC == "check"):
					fiufe.write("{}\n".format(csv_output))
			printlog(csv_output)

		if qc_type == "before":
			f.close()
		if etools_remap_count > 0:
			fiufe.close()

printlog("\nGeneral Settings:")
printlog("Country: {} (ISO2: {}, ISO3: {})".format(country, iso2, iso3))
printlog("Workspace ID: {}".format(workspace_id))  #  ToDo: add API call to check workspace ID and name https://etools-staging.unicef.org/api/v2/workspaces/
printlog("Area threshold for geom intersections: {}".format(thres))
printlog("Geom similarity threshold: {}% [0-100%]".format(geomsim_treshold))
printlog("Name similarity threshold: {} [0-100%]".format(textsim_treshold))
printlog("Geom similarity threshold (for remap): {}% [0-100%]".format(geomsim_remap_treshold))
printlog("Point distance threshold (in meters): {}".format(point_dist_treshold))
printlog("Locations in use URL: https://etools.unicef.org/api/management/gis/in-use/?country_id={}".format(workspace_id))

if qc_type_oldnew == "both":
	printlog("\nInput Data Overview")
	for a in admin_levels:
		printlog("Level: {}".format(a.level))
		printlog("{}\t{}".format([old_lyr.name() for old_lyr in old_lyrs],a.nl.name()))
		printlog("{}\t{}".format(len(a.ofts), len(a.nfts)))

	printlog("\nGeneral Summary")
	printlog("Level\tAdmin Name\tNew Layer\tNLPCodeF\tNLNameF\tNLPPcodeF\tDateModif\tGate Id\tNew FtCount\tOld FtCount")
	for a in admin_levels:
		printlog("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, a.name, a.nl.name(), a.nl_pc_f, a.nl_n_f, a.nl_ppc_f, datetime.fromtimestamp(os.path.getmtime(a.nl.dataProvider().dataSourceUri().split("|")[0])), a.gat_id, len(a.nfts), len(a.ofts)))
	total_o_fts = sum([len(a.ofts) for a in admin_levels])
	total_n_fts = sum([len(a.nfts) for a in admin_levels])

	printlog("Total number of {} Locations: {}".format(old_label, total_o_fts))
	printlog("Total number of new Locations: {}".format(total_n_fts))

	old_fts_count = 0
	for old_lyr in old_lyrs:
		old_fts_count += len(list(old_lyr.getFeatures()))  # ToDo test this feature

	if old_fts_count != total_o_fts:
		printlog("WARNING: {} old Locations are not associated with any of the admin levels!".format(old_fts_count - total_o_fts))

if qc_type_oldnew == "new":
	printlog("\nInput Data Overview")
	for a in admin_levels:
		printlog("Level: {}".format(a.level))
		printlog("{}\t{}".format("n/a",a.nl.name()))
		printlog("{}\t{}".format("n/a", len(a.nfts)))

	printlog("\nGeneral Summary")
	printlog("Level\tAdmin Name\tNew Layer\tNLPCodeF\tNLNameF\tNLPPcodeF\tDateModif\tGate Id\tNew FtCount\tOld FtCount")
	for a in admin_levels:
		printlog("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, a.name, a.nl.name(), a.nl_pc_f, a.nl_n_f, a.nl_ppc_f, datetime.fromtimestamp(os.path.getmtime(a.nl.dataProvider().dataSourceUri().split("|")[0])), a.gat_id, len(a.nfts), "n/a"))
	total_n_fts = sum([len(a.nfts) for a in admin_levels])

	printlog("Total number of new Locations: {}".format(total_n_fts))


if qc_type_oldnew == "old" or qc_type_oldnew == "both":
	printlog("\nInternal QC Summary - {} Datasets".format(old_label.title()))
	printlog("Level\tGeomErr\tOverlaps\tNull Name\tNull Pcode\tDupl Pcode\tNull PPc\tWrong PPc\tNo Parent\tQC Status")
	for a in admin_levels:
		printlog("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level,
																						  len(a.o_geom_err),
																						  len(a.o_overlap_err),
																 						  len(a.o_null_name_err),
																						  len(a.o_null_pc_err),
																						  len(a.o_dupl_pc_err),
																						  len(a.o_null_ppc_err),
																						  len(a.o_parent_err),
																						  len(a.o_no_parent_err),
																						  a.o_qc_stat_int))

if qc_type_oldnew == "new" or qc_type_oldnew == "both":
	printlog("\nInternal QC Summary - New Datasets")
	printlog("Level\tGeomErr\tOverlaps\tNull Name\tNull Pcode\tDupl Pcode\tNull PPc\tWrong PPc\tNo Parent\tQC Status")
	for a in admin_levels:
		printlog("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level,
																						  len(a.n_geom_err),
																						  len(a.n_overlap_err),
																 						  len(a.n_null_name_err),
																						  len(a.n_null_pc_err),
																						  len(a.n_dupl_pc_err),
																						  len(a.n_null_ppc_err),
																						  len(a.n_parent_err),
																						  len(a.n_no_parent_err),
																						  a.n_qc_stat_int))

if qc_type_oldnew == "both":
	printlog("\nCross-Check QC Summary")

	printlog("{}\tNew\tPs\tPd\tNs\tNd\tOy\tOn\tGs\tGd\tiU\tPdiU\tNdiU\tOniU\tGdiU\tQC".format(old_label.title()))
	for a in admin_levels:
		remaps = a.cross_remaps

		cross_pcode_same = [r for r in remaps if r[3] == True]
		cross_pcode_diff = [r for r in remaps if r[3] == False]
		cross_name_same = [r for r in remaps if r[6] >= textsim_treshold]
		cross_name_diff = [r for r in remaps if r[6] < textsim_treshold]
		cross_overlap_yes = [r for r in remaps if r[9] == 0]
		cross_overlap_no = [r for r in remaps if r[9] > 0]
		cross_geom_same = [r for r in remaps if r[7] >= geomsim_treshold and r[8] >= geomsim_treshold]
		cross_geom_diff = [r for r in remaps if not (r[7] >= geomsim_treshold and r[8] >= geomsim_treshold)]

		cross_in_use = [r for r in remaps if r[1] in pcodes_in_use[a.level]]
		cross_in_use_pcode_same = [r for r in remaps if (r[3] == True and r[1] in pcodes_in_use[a.level])]
		cross_in_use_pcode_diff = [r for r in remaps if (r[3] == False and r[1] in pcodes_in_use[a.level])]
		cross_in_use_name_same = [r for r in remaps if (r[6] >= textsim_treshold and r[1] in pcodes_in_use[a.level])]
		cross_in_use_name_diff = [r for r in remaps if (r[6] < textsim_treshold and r[1] in pcodes_in_use[a.level])]
		cross_in_use_overlap_yes = [r for r in remaps if (r[9] == 0 and r[1] in pcodes_in_use[a.level])]
		cross_in_use_overlap_no = [r for r in remaps if (r[9] > 0 and r[1] in pcodes_in_use[a.level])]
		cross_in_use_geom_same = [r for r in remaps if (
					r[7] >= geomsim_treshold and r[8] >= geomsim_treshold and r[1] in pcodes_in_use[a.level])]
		cross_in_use_geom_diff = [r for r in remaps if
								  not (r[7] >= geomsim_treshold and r[8] >= geomsim_treshold) and r[1] in pcodes_in_use[
									  a.level]]

		statusQC = "check"
		if len(cross_in_use_pcode_diff) == 0 and len(cross_in_use_name_diff) == 0 and len(cross_in_use_overlap_no) == 0 and len(cross_in_use_geom_diff) == 0:
			statusQC = "OK"

		printlog("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(len(a.ofts), len(a.nfts), len(cross_pcode_same),len(cross_pcode_diff),len(cross_name_same),len(cross_name_diff),len(cross_overlap_yes),len(cross_overlap_no),len(cross_geom_same),len(cross_geom_diff),len(cross_in_use), len(cross_in_use_pcode_diff), len(cross_in_use_name_diff), len(cross_in_use_overlap_no), len(cross_in_use_geom_diff), statusQC))

	printlog("\nLegend:")
	printlog("{} - Locations currently available in eTools".format(old_label.title()))
	printlog("New - new Locations to be uploaded to eTools")
	printlog("Ps - old Locations with the same Pcode as remapped Location")
	printlog("Pd - old Locations with different Pcode than remapped Location")
	printlog("Ns - old Locations with the same Name as remapped Location")
	printlog("Nd - old Locations with different Name than remapped Location")
	printlog("Oy - old Locations overlapping with remapped Location")
	printlog("On - old Locations not overlapping with remapped Location")
	printlog("Gs - old Locations with the same geometry as remapped Location")
	printlog("Gd - old Locations with different geometry than remapped Location")
	printlog("iU - old Locations in Use")
	printlog("PdiU - old Locations in use with different Pcode than remapped Location")
	printlog("NdiU - old Locations in use with different Name than remapped Location")
	printlog("OniU - old Locations in use not overlapping with remapped Location")
	printlog("GdiU - old Locations in use with different geometry than remapped Location")
	printlog("QC - QC status, 'check' - some major changes, 'OK' - no major changes")

endDate = datetime.utcnow()
printlog("\nCompleted: {}".format(endDate))
printlog("Total processing time: {}".format(endDate - startDate))

flog.close()