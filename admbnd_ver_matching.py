from datetime import datetime, date, time
from difflib import SequenceMatcher
from math import sin, cos, sqrt, atan2, radians

import os

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

start_time = datetime.now()
print "Started at: {}".format(start_time)

adm_level = 2

# #####################
# #GADM
old_pcode_field = 'GID_1'
old_name_field = 'NAME_1'
old_lyr_name = 'GADM_gadm36_IRN_1'
old_lyr_label = 'GADM'
#
# new_pcode_field = 'GID_1'
# new_name_field = 'NAME_1'
# new_lyr_name = 'GADM_gadm36_IRN_1'
# new_lyr_label = 'GADM'
#
# old_pcode_field = 'GID_2'
# old_name_field = 'NAME_2'
# old_lyr_name = 'GADM_gadm36_IRN_2'
# old_lyr_label = 'GADM'
#
# new_pcode_field = 'GID_2'
# new_name_field = 'NAME_2'
# new_lyr_name = 'GADM_gadm36_IRN_2'
# new_lyr_label = 'GADM'
#
# #####################
# # IOM
# old_pcode_field = 'ADM1_CODE'
# old_name_field = 'ADM1_NAME'
# old_lyr_name = 'IOM_IRN_ADM1_wgs84'
# old_lyr_label = 'IOM'
#
new_pcode_field = 'ADM1_CODE'
new_name_field = 'ADM1_NAME'
new_lyr_name = 'IOM_IRN_ADM1_wgs84'
new_lyr_label = 'IOM'
#
# old_pcode_field = 'ADM2_CODE'
# old_name_field = 'ADM2_NAME'
# old_lyr_name = 'IOM_IRN_ADM2_wgs84'
# old_lyr_label = 'IOM'
#
# new_pcode_field = 'ADM2_CODE'
# new_name_field = 'ADM2_NAME'
# new_lyr_name = 'IOM_IRN_ADM2_wgs84'
# new_lyr_label = 'IOM'
#
#
# #####################
# # UNHCR
# old_pcode_field = 'pcode'
# old_name_field = 'name'
# old_lyr_name = 'UNHCR_IRN_Admin1_wgs84'
# old_lyr_label = 'UNHCR'
#
# new_pcode_field = 'pcode'
# new_name_field = 'name'
# new_lyr_name = 'UNHCR_IRN_Admin1_wgs84'
# new_lyr_label = 'UNHCR'
#
# old_pcode_field = 'pcode'
# old_name_field = 'name'
# old_lyr_name = 'UNHCR_IRN_Admin2_wgs84'
# old_lyr_label = 'UNHCR'
#
# new_pcode_field = 'pcode'
# new_name_field = 'name'
# new_lyr_name = 'UNHCR_IRN_Admin2_wgs84'
# new_lyr_label = 'UNHCR'
#
#
#
# #####################
# # WFP
# old_pcode_field = 'adm1_id'
# old_name_field = 'adm1_name'
# old_lyr_name = 'WFP_irn_bnd_adm1_wfpge'
# old_lyr_label = 'WFP'
#
# new_pcode_field = 'adm1_id'
# new_name_field = 'adm1_name'
# new_lyr_name = 'WFP_irn_bnd_adm1_wfpge'
# new_lyr_label = 'WFP'
#
# old_pcode_field = 'adm2_id'
# old_name_field = 'adm2_name'
# old_lyr_name = 'WFP_irn_bnd_adm2_wfpge'
# old_lyr_label = 'WFP'
#
# new_pcode_field = 'adm2_id'
# new_name_field = 'adm2_name'
# new_lyr_name = 'WFP_irn_bnd_adm2_wfpge'
# new_lyr_label = 'WFP'




old_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == old_lyr_name][0]
new_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == new_lyr_name][0]

n_index = QgsSpatialIndex()
for f in new_lyr.getFeatures():
	n_index.insertFeature(f)

new_fts = {feature.id(): feature for (feature) in new_lyr.getFeatures()} #[ft for ft in new_lyr.getFeatures()]
old_fts = {feature.id(): feature for (feature) in old_lyr.getFeatures()} #[ft for ft in old_lyr.getFeatures()]



old2new_links = []

for oft in old_fts.values():
	old2new_dist = []
	oft_centr = oft.geometry().pointOnSurface()
	match_found = 0

	# first try intersecting with nearest neighbors
	near_ids = n_index.intersects(oft.geometry().boundingBox())
	for nid in near_ids:
		nnft = new_fts[nid]
		if oft_centr.intersects(nnft.geometry()):
			old2new_dist.append([oft,nnft,0, "intersect"])
			# print("{}\t{}".format(oft[old_pcode_field],nnft[new_pcode_field]))
			match_found += 1

	# no intersecting neighbor
	if match_found == 0:
		for nft in new_fts.values():
			if oft_centr.intersects(nft.geometry()):
				old2new_dist.append([oft,nft,0, "intersect"])
				#print("{}\t{}".format(oft[old_pcode_field],nft[new_pcode_field]))
				match_found += 1
			else:
				dist = calc_distance(oft.geometry().pointOnSurface().asPoint().y(), oft.geometry().pointOnSurface().asPoint().x(), nft.geometry().asPoint().y(), nft.geometry().asPoint().x())
				old2new_dist.append([oft,nft,dist,"neigbor"])
				#print("{}\t{}\t{}".format(oft[old_pcode_field],nft[new_pcode_field],oft.geometry().pointOnSurface().distance(nft.geometry())))


	nn = min(old2new_dist, key=lambda x: x[2])
	oft = nn[0]
	nft = nn[1]
	old_name = getval(oft, old_name_field)
	old_pcode = oft[old_pcode_field]
	new_name = getval(nft, new_name_field)
	new_pcode = nft[new_pcode_field]
	intersect_geom = nft.geometry().intersection(oft.geometry())
	geomsim_old = (intersect_geom.area() / oft.geometry().area() * 100)
	geomsim_new = (intersect_geom.area() / nft.geometry().area() * 100)
	centr_dist = calc_distance(oft.geometry().pointOnSurface().asPoint().y(), oft.geometry().pointOnSurface().asPoint().x(), nft.geometry().pointOnSurface().asPoint().y(), nft.geometry().pointOnSurface().asPoint().x())
	name_sim = SequenceMatcher(None, old_name, new_name).ratio() * 100

	if match_found > 1:
		old2new_links.append([old_pcode, new_pcode, old_name, new_name, name_sim, geomsim_old, geomsim_new, nn[2], centr_dist, 'ERROR - multiple intersects'])
	else:
		old2new_links.append([old_pcode, new_pcode, old_name, new_name, name_sim, geomsim_old, geomsim_new, nn[2], centr_dist, 'OK'])


outpath = os.path.join(os.path.dirname(new_lyr.dataProvider().dataSourceUri()),"Adm{}_{}_remappedTO_{}.txt".format(adm_level, old_lyr_label, new_lyr_label))
f = open(outpath, 'w')
header_csv = "{}_pcode\t{}_pcode\tpcode_check\t{}_name\t{}_name\tname_sim\tgeomsim_{}\tgeomsim_{}\tdis_m\tcentr_dist_m\tcomment".format(old_lyr_label, new_lyr_label, old_lyr_label, new_lyr_label, old_lyr_label, new_lyr_label)
f.write("{}\n".format(header_csv))

for l in old2new_links:
	csv_output = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(l[0], l[1], l[0]==l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[8], l[9])
	f.write("{}\n".format(csv_output))
f.close()
print "Finished at: {}".format(datetime.now())
print "Time: {}".format(datetime.now() - start_time)
avg_name_sim = sum([a[4] for a in old2new_links])/len(old2new_links)
print "Average name sim: {}".format(avg_name_sim)

# ooo = [f for f in old_fts.values() if f[old_pcode_field] == "MZ007309250"][0]
# nnn = [f for f in new_fts.values() if f[new_pcode_field] == "MZ008102263"][0]
# intersect_geom = nnn.geometry().intersection(ooo.geometry())
# geomsim_old = (intersect_geom.area() / ooo.geometry().area() * 100)
# geomsim_new = (intersect_geom.area() / nnn.geometry().area() * 100)
#
# # create a memory layer with two points
# layer =  QgsVectorLayer('Polygon', 'polygons' , "memory")
# pr = layer.dataProvider()
# # add the first point
# pg = QgsFeature()
# pg.setGeometry(intersect_geom)
# pr.addFeatures([pg])
# pg = QgsFeature()
# pg.setGeometry(ooo.geometry())
# pr.addFeatures([pg])
# pg = QgsFeature()
# pg.setGeometry(nnn.geometry())
# pr.addFeatures([pg])
# # update extent of the layer
# layer.updateExtents()
# # update extent
# layer.updateExtents()
# # add the layer to the canvas
# QgsMapLayerRegistry.instance().addMapLayers([layer])