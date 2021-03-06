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

datasets = []

#######################
# DEFINE ALL INPUT DATASETS BY ADMIN LEVEL
s1 = "OCHA"
s2 = "UNICEF"
s3 = "FAO"
s4 = "WFP"
s5 = "UNHCR"

datasets.append({'src': 'OCHA', 'lev': 0, 'lyr': 'OCHA_AFG_adm0', 'id': 'ID_0', 'namef': 'NAME_ENGLI'})
datasets.append({'src': 'OCHA', 'lev': 1, 'lyr': 'OCHA_AFG_adm1', 'id': 'ID_1', 'namef': 'NAME_1'})
datasets.append({'src': 'OCHA', 'lev': 2, 'lyr': 'OCHA_AFG_adm2', 'id': 'ID_2', 'namef': 'NAME_2'})
datasets.append({'src': 'UNICEF', 'lev': 0, 'lyr': 'UNICEF_AFG_adm0', 'id': 'HRpcode', 'namef': 'HRname'})
datasets.append({'src': 'UNICEF', 'lev': 1, 'lyr': 'UNICEF_AFG_adm1', 'id': 'HRpcode', 'namef': 'HRname'})
datasets.append({'src': 'UNICEF', 'lev': 2, 'lyr': 'UNICEF_AFG_adm2', 'id': 'HRpcode', 'namef': 'HRname'})
datasets.append({'src': 'FAO', 'lev': 0, 'lyr': 'FAO_AFG_adm0', 'id': 'ADM0_CODE', 'namef': 'ADM0_NAME'})
datasets.append({'src': 'FAO', 'lev': 1, 'lyr': 'FAO_AFG_adm1', 'id': 'ADM1_CODE', 'namef': 'ADM1_NAME'})
datasets.append({'src': 'FAO', 'lev': 2, 'lyr': 'FAO_AFG_adm2', 'id': 'ADM2_CODE', 'namef': 'ADM2_NAME'})
datasets.append({'src': 'UNHCR', 'lev': 1, 'lyr': 'UNHCR_AFG_adm1', 'id': 'pcode', 'namef': 'name'})
datasets.append({'src': 'UNHCR', 'lev': 2, 'lyr': 'UNHCR_AFG_adm2', 'id': 'pcode', 'namef': 'name'})

# END OF INPUT PARAMETERS
#######################

# add data source to the dictionary
sources = (s1, s2, s3, s4, s5)
sources_dict = {}
a = 1
for i in sources:
	sources_dict[i] = a
	a += 1


min_level = min([d['lev'] for d in datasets])
max_level = max([d['lev'] for d in datasets])

for l in range(min_level, max_level + 1):
	print "Level: {}".format(l)
	datasets_lev = [d for d in datasets if d['lev'] == l]
	# print filtered_datasets
	sources_filtered = [fd['src'] for fd in datasets_lev]
	# print sources_filtered
	source_dataset = ""
	target_dataset = ""

	for src in sources:
		if src in sources_filtered:
			source_dataset = [sf for sf in datasets_lev if sf['src'] == src][0]
			print "Source: {}".format(source_dataset)
			other_sources = [fd['src'] for fd in datasets_lev if not fd['src'] == source_dataset['src']]
			other_sources_filtered = []
			other_sources_filtered_dict = {}
			for src in sources:
				if src in other_sources:
					other_sources_filtered.append(src)
					other_sources_filtered_dict[src] = [sf for sf in datasets_lev if sf['src'] == src][0]
			print other_sources_filtered
			for td in other_sources_filtered:
				target_dataset = other_sources_filtered_dict[td]
				print "Target: {}".format(target_dataset)

				# Set input data
				adm_level = l

				old_pcode_field = source_dataset['id']
				old_name_field = source_dataset['namef']
				old_lyr_name = source_dataset['lyr']
				old_lyr_label = source_dataset['src']

				new_pcode_field = target_dataset['id']
				new_name_field = target_dataset['namef']
				new_lyr_name = target_dataset['lyr']
				new_lyr_label = target_dataset['src']


				# get QGIS layers
				old_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == old_lyr_name][0]
				new_lyr = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == new_lyr_name][0]

				# build spatial index for new features
				n_index = QgsSpatialIndex()
				for f in new_lyr.getFeatures():
					n_index.insertFeature(f)

				# get old and new features into dictionaries
				new_fts = {feature.id(): feature for (feature) in new_lyr.getFeatures()} #[ft for ft in new_lyr.getFeatures()]
				old_fts = {feature.id(): feature for (feature) in old_lyr.getFeatures()} #[ft for ft in old_lyr.getFeatures()]

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
							perc_overlap = nn_intersect_geom.area() / oft.geometry().area() * 100
							old2new_remap_overlaps.append([oft,nnft,perc_overlap, "intersect"])
							# print("{}\t{}\t{}".format(oft[old_pcode_field],nnft[new_pcode_field],perc_overlap))
							match_found += 1

					# do if no intersecting neighbors found
					if match_found == 0:

						# loop through all "new" admin boundaries and calculate distance
						for nft in new_fts.values():
							dist = oft.geometry().pointOnSurface().distance(nft.geometry()) # ToDo: measure distance to the nearset edge not between centroids
							old2new_remap_neighbors.append([oft,nft,dist,"neigbor"])
							# print("{}\t{}\t{}".format(oft[old_pcode_field],nft[new_pcode_field],dist))

					# find best match
					best_match = []
					if match_found == 0:
						# get the closest new boundary as the best match
						best_match = min(old2new_remap_neighbors, key=lambda x: x[2])
						dist = best_match[2]
					else:
						# get a new boundary which overlaps the largest portion of the "old" boundary as the best match
						best_match = max(old2new_remap_overlaps, key=lambda x: x[2])
						dist = 0

					# get "old" and "new" matching boundaries
					oft = best_match[0]
					nft = best_match[1]
					old_name = getval(oft, old_name_field)
					old_pcode = oft[old_pcode_field]
					new_name = getval(nft, new_name_field)
					new_pcode = nft[new_pcode_field]

					# intersect both geometries and calculate similarities
					intersect_geom = nft.geometry().intersection(oft.geometry())
					geomsim_old = (intersect_geom.area() / oft.geometry().area() * 100)
					geomsim_new = (intersect_geom.area() / nft.geometry().area() * 100)
					centr_dist = calc_distance(oft.geometry().pointOnSurface().asPoint().y(), oft.geometry().pointOnSurface().asPoint().x(), nft.geometry().pointOnSurface().asPoint().y(), nft.geometry().pointOnSurface().asPoint().x())

					# calculate name similarity
					name_sim = SequenceMatcher(None, old_name, new_name).ratio() * 100

					# add a pair of "old" and "new" polygons to the remap table
					old2new_remaps.append([old_pcode, new_pcode, old_name, new_name, name_sim, geomsim_old, geomsim_new, dist, centr_dist, 'OK'])


				# write a remap table to txt/csv file
				out_dir = os.path.abspath(os.path.join(os.path.join(new_lyr.dataProvider().dataSourceUri(), os.pardir), os.pardir))
				outpath = os.path.join(out_dir,"Adm{}_S{}-{}_remappedTO_S{}-{}.txt".format(adm_level, sources_dict[old_lyr_label], old_lyr_label, sources_dict[new_lyr_label], new_lyr_label))
				f = open(outpath, 'w')
				header_csv = "{}_pcode\t{}_pcode\tpcode_check\t{}_name\t{}_name\tname_sim\tgeomsim_{}\tgeomsim_{}\tdis_dd\tcentr_dist_m\tcomment".format(old_lyr_label, new_lyr_label, old_lyr_label, new_lyr_label, old_lyr_label, new_lyr_label)
				f.write("{}\n".format(header_csv))

				for ln in old2new_remaps:
					csv_output = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(ln[0], ln[1], ln[0]==ln[1], ln[2], ln[3], ln[4], ln[5], ln[6], ln[7], ln[8], ln[9])
					f.write("{}\n".format(csv_output))
				f.close()

				# print summary to the console
				print("old_pcode_field = {}".format(old_pcode_field))
				print("old_name_field = {}".format(old_name_field))
				print("old_lyr_name = {}".format(old_lyr_name))
				print("old_lyr_label = {}".format(old_lyr_label))

				print("new_pcode_field = {}".format(new_pcode_field))
				print("new_name_field = {}".format(new_name_field))
				print("new_lyr_name = {}".format(new_lyr_name))
				print("new_lyr_label = {}".format(new_lyr_label))

				avg_name_sim = sum([a[4] for a in old2new_remaps])/len(old2new_remaps)
				print "Average name sim: {}".format(avg_name_sim)

print "Finished at: {}".format(datetime.now())
print "Time: {}".format(datetime.now() - start_time)
