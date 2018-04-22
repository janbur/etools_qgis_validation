# ###########################
#  Locations for eTools All-in-One QC Check
# ###########################

import itertools
import json
import collections
import os
import sys
import qgis.core
import requests
from qgis.core import *
from PyQt4.QtCore import QVariant
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from datetime import datetime, date, time
from shapely.geometry.multipolygon import MultiPolygon
from shapely import wkt
from difflib import SequenceMatcher


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
	def __init__(self, level, name, gat_id, nl_n, nl_pc_f, nl_n_f, nl_ppc_f, nl, new_fts, old_fts, n_geom_err, n_overlap_err, n_null_pc_err, n_dupl_pc_err, n_null_ppc_err, n_parent_err, o_geom_err , o_overlap_err, o_null_pc_err, o_dupl_pc_err, o_null_ppc_err, o_parent_err, n_no_parent_err, o_no_parent_err, cross_a, cross_ag, cross_an, cross_b, cross_br, cross_bnr, cross_bmr, cross_bnriu, cross_c, cross_qc, n_qc_stat_int="UNKNOWN", o_qc_stat_int="UNKNOWN"):
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
		self.cross_bnr = cross_bnr  # case B - no Remap
		self.cross_bmr = cross_bmr  # case B - multiple Remap
		self.cross_bnriu = cross_bnriu  # case B - no Remap in Use
		self.cross_c = cross_c  # case B
		self.cross_qc = cross_qc  # cross-check QC status


def saveimg(lyr_id, level, lyr_type):
	# set up image renderer
	img = QImage(QSize(600, 600), QImage.Format_ARGB32_Premultiplied)

	# set image's background color
	color = QColor(255, 255, 255)
	img.fill(color.rgb())

	render = QgsMapRenderer()
	render.setLayerSet([admin_levels[0].nl.id()])  # zoom extent to the country level

	# set extent
	rect = QgsRectangle(render.fullExtent())
	rect.scale(1.1)
	render.setExtent(rect)

	render.setLayerSet([lyr_id])
	render.setOutputSize(img.size(), img.logicalDpiX())
	# create painter
	p = QPainter()
	p.begin(img)
	p.setRenderHint(QPainter.Antialiasing)

	# do the rendering
	render.render(p)

	p.end()

	outdir = os.path.join(os.path.dirname(os.path.dirname(admin_levels[0].nl.dataProvider().dataSourceUri())), "PNG")
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	if lyr_type == "new":
		filename = "{}_adm-{}_{}_{}.png".format(country, level, lyr_type, '{0:%Y}{0:%m}{0:%d}'.format(datetime.utcnow()))
	else:
		filename = "{}_adm-{}_{}_{}.png".format(country, level, lyr_type, '{0:%Y}{0:%m}{0:%d}'.format(datetime.utcnow()))

	path = os.path.join(outdir, filename)

	# save image
	img.save(path, "png")
	# print "Snapshot for level {} created at {}".format(l, path)


# definition of admin levels and input layers

# UPDATED:
#params for Zambia
# admin_levels = []
# admin_levels.append(AdminLevel(0,"Country",None ,"zmb_popa_adm0_Dissolved","admin0Pcod","COUNTRY",None,[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(1,"Province",1,"zmb_popa_adm1_census2010f_ISCGM_CSO_OCHA_","Pcode_CSO","PROVINCE","admin0Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(2,"District",2,"zmb_popa_adm2_census2010f_ISCGM_CSO_OCHA_","Pcode_CSO","District_n","Prov_code",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# country = "Zambia"
# iso2 = "ZM"

# params for Angola
admin_levels = []
admin_levels.append(AdminLevel(0,"Country",None,"AGO_adm0","admin0Pcod","NAME_ENGLI",None,[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
admin_levels.append(AdminLevel(1,"Region",2,"AGO_adm1","admin1Pcod","NAME_1","admin0Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
admin_levels.append(AdminLevel(2,"District",3,"AGO_adm2","admin2Pcod","NAME_2","admin1Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
admin_levels.append(AdminLevel(3,"Subdistrict",4,"AGO_adm3","admin3Pcod","NAME_3","admin2Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
country = "Angola"
iso2 = "AO"



# NOT UPDATED:
# params for Rwanda
# admin_levels = []
# admin_levels.append(AdminLevel(0,"Country",0,"RWA_Admin1_Dissolved","admin0Pcod","admin0Nam","NULL",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(1,"Province",1,"RWA_Admin2_2006_NISR","admin1Pcod","PROVINCE","admin0Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(2,"District",2,"RWA_Admin3_2006_NISR","admin2Pcod","NOMDISTR","admin1Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# country = "Rwanda"
# iso2 = "RW"


# params for Burkina_Faso
# admin_levels = []
# admin_levels.append(AdminLevel(0,"Country",35,"bfa_admbnda_admint_1m_salb_itos","admin0Pcod","admin0Name","NULL",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(1,"Region",1,"bfa_admbnda_adm1_1m_salb_itos","admin1Pcod","admin1Name","admin0Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(2,"Province",2,"bfa_admbnda_adm2_1m_salb_itos","admin2Pcod","admin2Name","admin1Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# country = "Burkina_Faso"
# iso2 = "BF"


# params for Djibouti
# admin_levels = []
# admin_levels.append(AdminLevel(0,"Country",1,"DJI_Admin1_1996_FEWS","admin0Pcod","COUNTRY","",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(1,"Region",2,"DJI_Admin2_FEWS","admin1Pcod","ADMIN2","admin0Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(2,"District",3,"DJI_Admin3_FEWS","admin2Pcod","ADMIN3","admin1Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# country = "Djibouti"
# iso2 = "DJ"

# params for Tunisia
# admin_levels = []
# admin_levels.append(AdminLevel(0,"Country",1,"TUN_adm0","admin0Pcod","NAME_ENGLI","",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(1,"Governorate",2,"TUN_adm1","admin1Pcod","NAME_1","admin0Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(2,"Delegation",3,"TUN_adm2","admin2Pcod","NAME_2","admin1Pcod",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# country = "Tunisia"
# iso2 = "TN"

# params for Mozambique
# admin_levels = []
# admin_levels.append(AdminLevel(0,"Country",1,"moz_polbnda_adm0_country","HRPCode","COUNTRY","",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(1,"Province",2,"moz_polbnda_adm1_provinces_WFP_OCHA_ROSA","HRPCode","HRName","HRParent",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(2,"District",3,"moz_polbnda_adm2_districts_wfp_ine_pop2012_15_ocha","P_CODE","DISTRICT","PROV_CODE",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(3,"Posto",4,"moz_polbnda_adm3_postos_wfp_ine_ocha_","P_CODE","POSTO","D_PCODE",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# country = "Mozambique"
# iso2 = "MZ"


# params for Niger
# admin_levels = []
# admin_levels.append(AdminLevel(0,"Country",1,"NER_adm00_feb2018", "ISO2", "adm_00", "",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(1,"Region",2,"NER_adm01_feb2018","rowcacode1","adm_01","ISO2",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(2,"Department",3,"NER_adm02_feb2018","rowcacode2","adm_02","rowcacode1",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# admin_levels.append(AdminLevel(3,"Other",99,"NER_adm03_feb2018","rowcacode3","adm_03","rowcacode2",[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]))
# country = "NE"


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

# thresholds size for intersections
thres = 0.0000001

# level counter
l = 0

new_pcodes = []
old_pcodes = []

old_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == "locations_location"][0]

# settings for cross-check
geomsim_treshold = 99
textsim_treshold = 0.8


# read locations in use # ToDo replace with API call once tested
with open(r'') as json_data:
	loc_in_use = json.load(json_data)
pcodes_in_use = [liu['p_code'] for liu in loc_in_use]
ids_in_use = [liu['id'] for liu in loc_in_use]

# add layers and new/old features for all admin levels
for admin_level in admin_levels:
	new_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == admin_level.nl_n][0]
	new_fts = [ft for ft in new_lyr.getFeatures()]  # TODO: add check for null geom
	admin_level.nl = new_lyr
	admin_level.nfts = new_fts
	old_fts = []
	if admin_level.level > 0:
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

	for ft in fts:
		ftgeom = ft.geometry()

		if lyr_type == "new":
			ftpc = str(ft[admin_level.nl_pc_f])  # works for shapefiles
		else:
			ftpc = str(ft[pc_field]).strip()

		# Null Pcode QC Check
		if ftpc is 'NULL' or ftpc == '':  # works for shapefiles
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
			if admin_level.name != "Country" and parent_qc == 1:
				ft_centr = ftgeom.pointOnSurface()

				if lyr_type == "new":
					ftppc = str(ft[admin_level.nl_ppc_f]).strip()
					ftparent = ftppc
				else:
					ftpid = str(ft[pid_field]).strip()
					ftparent = ftpid

				parent_found_flag = 0
				for pft in pfts:
					pftgeom = pft.geometry()
					if pftgeom:
						if ft_centr.intersects(pftgeom):
							parent_found_flag = 1
							if lyr_type == "new":
								pftpc = str(pft[admin_levels[admin_level.level - 1].nl_pc_f]).strip()
								if ftparent != pftpc:
									admin_level.n_parent_err.append([ft, ftparent, pft])
							else:
								pftid = str(pft[id_field]).strip()
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
				admin_level.n_geom_err.append([ft])
			else:
				admin_level.o_geom_err.append([ft])

	# Duplicated Pcode QC Check
	if lyr_type == "new":
		query = '"' + str(admin_level.nl_pc_f) + '" in (' + str(new_duplquery) + ')'
		selection = admin_level.nl.getFeatures(QgsFeatureRequest().setFilterExpression(query))
		admin_level.n_dupl_pc_err = [k for k in selection]
	else:
		if admin_level.gat_id:
			query = "\"gateway_id\"={} AND \"{}\" in ({})".format(admin_level.gat_id, pc_field, str(old_duplquery))
			# query = '"' + str(pc_field) + '" in (' + str(old_duplquery) + ')'
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


print "\nCross-check QC"
######################
# Main loop for all levels
######################
for admin_level in admin_levels:
	# qc for new locations
	qc(admin_level, admin_level.nfts, admin_levels[admin_level.level - 1].nfts, "new")
	qc(admin_level, admin_level.ofts, admin_levels[admin_level.level - 1].ofts, "old")

	######################
	# Cross-check new and old data
	######################
	new_pcodes = []

	# list new pcodes
	for new_ft in admin_level.nfts:
		new_ft_pc = str(new_ft[admin_level.nl_pc_f]).strip()
		new_ft_name = str(new_ft[admin_level.nl_n_f]).strip()
		new_ft_geom = new_ft.geometry()
		if new_ft_pc:  # ToDo: add handling for locations with null pcodes - match by geom...?
			new_pcodes.append(new_ft_pc)
			if new_ft_pc in old_pcodes:  # CASE A

				for old_ft in admin_level.ofts:  # ToDo: check all old locations, regardless gateway id / level
					old_ft_pc = str(old_ft[pc_field]).strip()
					if old_ft_pc == new_ft_pc:
						old_ft_name = old_ft[name_field].encode('utf-8').strip()
						old_ft_geom = old_ft.geometry()
						admin_level.cross_a.append([old_ft, new_ft])
						if not old_ft_geom.equals(new_ft_geom):  # CASE A - diff geom
							# Algorithm for measuring similarity of geometry
							intersect_geom = new_ft_geom.intersection(old_ft_geom)
							geomsim_old = (intersect_geom.area() / old_ft_geom.area() * 100)
							geomsim_new = (intersect_geom.area() / new_ft_geom.area() * 100)
							if (geomsim_old < geomsim_treshold) and (geomsim_new < geomsim_treshold):
								admin_level.cross_ag.append([old_ft, new_ft, geomsim_old, geomsim_new])
						if new_ft_name != old_ft_name:  # CASE A - diff name
							# Algorithm for measuring similarity of names
							textsim = SequenceMatcher(None, old_ft_name, new_ft_name).ratio()
							if textsim < textsim_treshold:
								admin_level.cross_an.append([old_ft, new_ft, textsim])
			else:  # CASE C
				admin_level.cross_c.append(new_ft)

	for old_ft in admin_level.ofts:
		old_ft_pc = str(old_ft[pc_field]).strip()
		old_ft_name = old_ft[name_field].encode('utf-8').strip()
		old_ft_geom = old_ft.geometry()
		if old_ft_pc:
			if old_ft_pc not in new_pcodes:  # CASE B
				admin_level.cross_b.append(old_ft)

				# try to match removed location with new location
				remapflag = 0
				for new_ft in admin_level.nfts:
					if new_ft.geometry().contains(old_ft.geometry().pointOnSurface()):
						new_ft_pc = str(new_ft[admin_level.nl_pc_f]).strip()
						new_ft_name = str(new_ft[admin_level.nl_n_f]).strip()
						new_ft_geom = new_ft.geometry()
						textsim = SequenceMatcher(None, old_ft_name, new_ft_name).ratio()
						intersect_geom = new_ft_geom.intersection(old_ft_geom)
						geomsim_old = (intersect_geom.area() / old_ft_geom.area() * 100)
						geomsim_new = (intersect_geom.area() / new_ft_geom.area() * 100)

						if (geomsim_old > geomsim_treshold) and (geomsim_new > geomsim_treshold):
							admin_level.cross_br.append(old_ft, new_ft, textsim, geomsim_old, geomsim_new)
							remapflag += 1
							# print "Suggested remap from old ft: {}-{}-{} to new ft: {}-{}-{}".format(old_ft.id(),old_ft_pc,old_ft_name,new_ft.id(),new_ft_pc,new_ft_name)
				if remapflag == 0:
					admin_level.cross_bnr.append(old_ft)

					# check if missing location is in use
					if old_ft_pc in pcodes_in_use:
						admin_level.cross_bnriu.append(old_ft)
						print "WARNING: Location (ftid: {}, pcode: {}, name: {}) shall be removed but is in use".format(old_ft.id(),
																								   old_ft_pc,
																								   old_ft_name)

				elif remapflag > 1:
					admin_level.cross_bmr.append(old_ft)

	print "\nLevel: {}".format(admin_level.level)
	total_diffs = len(admin_level.cross_ag) + len(admin_level.cross_an) + len(admin_level.cross_b) + len(admin_level.cross_c)
	if total_diffs > 0:
		print "CASE\tOLD PCODE\tNEW PCODE\tOLD FID\tNEW FID\tOLD NAME\tNEW NAME\tSIMILARITY"
		if len(admin_level.cross_ag) > 0:
			for a_geom in admin_level.cross_ag:
				print "A-geom\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a_geom[0][pc_field], a_geom[1][admin_level.nl_pc_f], a_geom[0][id_field], a_geom[1].id(), a_geom[0][name_field],
																  a_geom[1][admin_level.nl_n_f], str(round(a_geom[2], 1)) + "/" + str(round(a_geom[3], 1)))
		if len(admin_level.cross_an) > 0:
			for a_name in admin_level.cross_an:
				print "A-name\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a_name[0][pc_field], a_name[1][admin_level.nl_pc_f], a_name[0][id_field], a_name[1].id(), a_name[0][name_field],
																  a_name[1][admin_level.nl_n_f], str(round(a_name[2], 1)))
		if len(admin_level.cross_b) > 0:
			for b in admin_level.cross_b:
				print "B-remov\t{}\t\t{}\t\t{}\t".format(b[pc_field], b[id_field], b[name_field])
		if len(admin_level.cross_c) > 0:
			for c in admin_level.cross_c:
				print "C-added\t\t{}\t\t{}\t\t{}".format(c[admin_level.nl_pc_f], c.id(), c[admin_level.nl_n_f])
	else:
		print "OK"


print "\nNull Pcodes QC Check"
total_null_pc_err = sum([len(a.n_null_pc_err + a.o_null_pc_err) for a in admin_levels])
if total_null_pc_err > 0:
	print "Level\tType\tFtid\tFtName"
	for a in admin_levels:
		for e in a.n_null_pc_err:
			print "{}\t{}\t{}\t{}".format(a.level, "new", e.id(), e[a.nl_n_f].encode('utf-8'))  # Todo: check id() for postgis / shp
		for e in a.o_null_pc_err:
			print "{}\t{}\t{}\t{}".format(a.level, "old", e.id(), e[name_field].encode('utf-8'))  # Todo: check id() for postgis / shp
else:
	print "OK"


print "\nDuplicate Pcodes QC Check"
total_dupl_pc_err = sum([len(a.n_dupl_pc_err + a.o_dupl_pc_err) for a in admin_levels])
if total_dupl_pc_err > 0:
	print "Level\tType\tFtCount\tFtids\tPcodes"
	for a in admin_levels:
		new_dupl_count = len(a.n_dupl_pc_err)
		if new_dupl_count > 0:
			print "{}\t{}\t{}\t{}\t{}".format(a.level, "new", new_dupl_count, [f.id() for f in a.n_dupl_pc_err], [f[a.nl_pc_f] for f in a.n_dupl_pc_err])  # Todo: check id() for postgis / shp
		old_dupl_count = len(a.o_dupl_pc_err)
		if old_dupl_count > 0:
			print "{}\t{}\t{}\t{}\t{}".format(a.level, "old", old_dupl_count, [f.id() for f in a.o_dupl_pc_err], [f[pc_field] for f in a.o_dupl_pc_err])  # Todo: check id() for postgis / shp
else:
	print "OK"


print "\nNull Parent Pcodes QC Check"
total_null_ppc_err = sum([len(a.n_null_ppc_err + a.o_null_ppc_err) for a in admin_levels])
if total_null_ppc_err > 0:
	print "Level\tType\tFtid\tPcode\tFtName"
	for a in admin_levels:
		for e in a.n_null_ppc_err:
			print "{}\t{}\t{}\t{}\t{}".format(a.level, "new", e.id(), e[a.nl_pc_f], e[a.nl_n_f].encode('utf-8'))  # Todo: check id() for postgis / shp
		for e in a.o_null_ppc_err:
			print "{}\t{}\t{}\t{}\t{}".format(a.level, "old", e.id(), e[pc_field], e[name_field].encode('utf-8'))  # Todo: check id() for postgis / shp
else:
	print "OK"

print "\nParent Pcodes QC Check"
total_parent_err = sum([len(a.n_parent_err + a.o_parent_err) for a in admin_levels])
if total_parent_err > 0:
	print "Level\tType\tFid\tFPcode\tFName\tWrongParentID\tCorrectParentID\tCorrectParentPcode\tCorrectParentName"
	for a in admin_levels:
		for e in a.n_parent_err:
			print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "new", e[0].id(), e[0][a.nl_pc_f], e[0][a.nl_n_f].encode('utf-8'), e[0][a.nl_ppc_f], e[2].id(), e[2][admin_levels[a.level - 1].nl_pc_f], e[2][admin_levels[a.level - 1].nl_n_f].encode('utf-8'))  # Todo: check id() for postgis / shp
		for e in a.o_parent_err:
			print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "old", e[0].id(), e[0][pc_field], e[0][name_field].encode('utf-8'), e[0][pid_field], e[2].id(), e[2][pc_field], e[2][name_field].encode('utf-8'))  # Todo: check id() for postgis / shp
else:
	print "OK"

print "\nNo Parent QC Check"
total_no_parent_err = sum([len(a.n_no_parent_err + a.o_no_parent_err) for a in admin_levels])
if total_no_parent_err > 0:
	print "Level\tType\tFid\tFPcode\tFName\tParentID"
	for a in admin_levels:
		for e in a.n_no_parent_err:
			print "{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "new", e[0].id(), e[0][a.nl_pc_f], e[0][a.nl_n_f].encode('utf-8'), e[0][a.nl_ppc_f])  # Todo: check id() for postgis / shp
		for e in a.o_no_parent_err:
			print "{}\t{}\t{}\t{}\t{}\t{}".format(a.level, "old", e[0].id(), e[0][pc_field], e[0][name_field].encode('utf-8'), e[0][pid_field])  # Todo: check id() for postgis / shp
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
		print "Lev\tOldFid\tNewFid\tOldFtPcode\tNewFtPcode\tOldFtName\tNewFtName\tNameSim\tGeomSimOld\tGeomSimNew"
		for a in admin_levels:
			for br in a.cross_br:
				print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, br[0][id_field], br[1].id(), br[0][pc_field], br[1][a.nl_pc_f],
																  br[0][name_field], br[1][a.nl_n_f], round(br[2], 2),
																  round(br[3], 2), round(br[4], 2))

	total_caseBnR = sum([len(a.cross_bnr) for a in admin_levels])
	print "\nCase BnR - Removed Locations with no Remap:\t{}".format(total_caseBnR)
	if total_caseBnR > 0:
		print "Level\tFtid\tPCode\tFtName"
		for a in admin_levels:
			for bnr in a.cross_bnr:
				print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, bnr[id_field], bnr[pc_field], bnr[name_field])

	total_caseBmR = sum([len(a.cross_bmr) for a in admin_levels])
	print "\nCase BmR - Removed Locations with multiple Remaps:\t{}".format(total_caseBmR)
	if total_caseBmR > 0:
		print "Level\tFtid\tPCode\tFtName"
		for a in admin_levels:
			for bmr in a.cross_bmr:
				print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, bmr[id_field], bmr[pc_field], bmr[name_field])

	total_caseBnRiU = sum([len(a.cross_bnriu) for a in admin_levels])
	print "\nCase BnRiU - Removed Locations in Use with no Remap:\t{}".format(total_caseBnRiU)
	if total_caseBnRiU > 0:
		print "Level\tFtid\tPCode\tFtName"
		for a in admin_levels:
			for bnriu in a.cross_bnriu:
				print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, bnriu[id_field], bnriu[pc_field], bnriu[name_field])


print "\nGeneral Settings:"
print "Area threshold for geom intersections: {}".format(thres)
print "Geom similarity threshold: {}".format(geomsim_treshold)
print "Name similarity threshold: {}".format(textsim_treshold)

print "\nGeneral Summary"
print "Level\tAdmin Name\tNew Lyr\tNLPCodeF\tNLNameF\tNLPPcodeF\tDateModif\tGate Id\tNew FtCount\tOld FtCount"
for a in admin_levels:
	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, a.name, a.nl.name(), a.nl_pc_f, a.nl_n_f, a.nl_ppc_f, datetime.fromtimestamp(os.path.getmtime(a.nl.dataProvider().dataSourceUri().split("|")[0])), a.gat_id, len(a.nfts), len(a.ofts))

print "\nInternal QC Summary"
print "Level\tNew Over\tNew NullPc\tNew DuplPc\tNew NullPpc\tNew WrongPpc\tNew No Parent\tNew QC Status\tOld Over\tOld NullPc\tOld DuplPc\tOld NullPpc\tOld WrongPpc\tOld No Parent\tOld QC Status"
for a in admin_levels:
	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level,
																					  len(a.n_overlap_err),
																					  len(a.n_null_pc_err),
																					  len(a.n_dupl_pc_err),
																					  len(a.n_null_ppc_err),
																					  len(a.n_parent_err),
																			  		  len(a.n_no_parent_err),
																					  a.n_qc_stat_int,
																					  len(a.o_overlap_err),
																					  len(a.o_null_pc_err),
																					  len(a.o_dupl_pc_err),
																					  len(a.o_null_ppc_err),
																					  len(a.o_parent_err),
																					  len(a.o_no_parent_err),
																				  	  a.o_qc_stat_int)

l = 0
print "\nCross-Check QC Summary"
print "Lev\tOld\tNew\tA\tAG\tAN\tB\tC\tBr\tBnR\tBmR\tBnRiU\tQC"
for a in admin_levels:
	count_old = len(a.ofts)
	count_new = len(a.nfts)
	count_a = len(a.cross_a)
	count_ag = len(a.cross_ag)
	count_an = len(a.cross_an)
	count_b = len(a.cross_b)
	count_c = len(a.cross_c)
	count_br = len(a.cross_br)
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
	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a.level, count_old, count_new, count_a, count_ag, count_an, count_b, count_c, count_br, count_bnr, count_bmr, count_bnriu, cross_qc_status)
	l += 1

print "\nLegend:\nOK - no errors, CHECK - manual check required, ERROR - major errors, NO DATA - no locations available"
endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
