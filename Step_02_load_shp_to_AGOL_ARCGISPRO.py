from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import arcpy
import os
import sys
import datetime
import re
import uuid


def printlog(message_text, type="M"):
	print(message_text)
	if type == "W":
		arcpy.AddWarning(message_text)
	elif type == "E":
		arcpy.AddError(message_text)
	else:
		arcpy.AddMessage(message_text)


aprx = arcpy.mp.ArcGISProject("CURRENT")
m = aprx.listMaps("Map")[0]


##################################
# GET INPUT PARAMETERS FROM TOOL UI
##################################
username = arcpy.GetParameterAsText(0)
passwd = arcpy.GetParameterAsText(1)
target_layer_name = arcpy.GetParameterAsText(2)
if not target_layer_name: target_layer_name = 'cod_admin_boundaries_MASTER'
tbl_upload_history_name = arcpy.GetParameterAsText(3)
if not tbl_upload_history_name: tbl_upload_history_name = 'tbl_upload_history_MASTER'
tbl_remap_history_name = arcpy.GetParameterAsText(4)
if not tbl_remap_history_name: tbl_remap_history_name = 'tbl_remap_history_MASTER'

input_shp_csv_file_full_path = arcpy.GetParameterAsText(5)
if not input_shp_csv_file_full_path: input_shp_csv_file_full_path = r'C:\Users\GIS\Documents\____UNICEF_ETOOLS\04_Data\AdminBoundaryRepo\INPUT_DATA_OTHER_COUNTRIES_LEV0\_input_data_02.csv'
base_folder = os.path.dirname(input_shp_csv_file_full_path)
csv_file = os.path.basename(input_shp_csv_file_full_path)
arcpy.env.workspace = base_folder
input_shp_csv_file = input_shp_csv_file_full_path

# Reference AGOL layers
target_layer = m.listLayers(target_layer_name)[0]
tbl_upload_history = m.listTables(tbl_upload_history_name)[0]
tbl_remap_history = m.listTables(tbl_remap_history_name)[0]
##################################




start_date = datetime.datetime.now()
printlog("started at: {}".format(start_date))


##################################
# READ LIST OF INPUT SHAPEFILES
##################################
shp_list = []
f = open(input_shp_csv_file, "r")
c = 0

for x in f:
	if c != 0:
		line = re.split(',', x)
		shp_list.append({'country': line[0], 'iso2': line[1], 'iso3': line[2], 'level': line[3], 'shp': line[4],
						 'def_lev_type': line[5], 'f_name': line[6], 'f_pcode': line[7], 'f_parent_pcode': line[8],
						 'f_name_en': line[9], 'f_name_fr': line[10], 'f_name_es': line[11], 'f_name_ar': line[12],
						 'f_name_lo': line[13], 'f_lev_type_field': line[14], 'comments': line[15], 'points': line[16], 'remap_tbl': line[17]})
	c = c+ 1

# check if all shapefiles are available AND all are polygons AND all are in WGS84 AND all remaps are available
check_all_shp = 1
check_all_pg = 1
check_all_wgs84 = 1
check_all_remaps_required_and_provided = 1
check_all_remaps_provided_and_exists = 1


for shp in shp_list:
	append_layer = os.path.join(base_folder, shp["shp"] + ".shp")
	exists = os.path.isfile(append_layer)
	pgcheck = 1
	wgscheck = 1
	remapcheck_provided = 1
	country_iso3 = shp['iso3']
	level = shp['level']


	# check shapefile
	if not exists:
		printlog("{} does not exist".format(shp["shp"]), "E")
		check_all_shp = 0
	else:
		desc = arcpy.Describe(append_layer)

		if not desc.shapeType == "Polygon":
			printlog("{} is of type {}".format(shp["shp"],desc.shapeType), "E")
			check_all_pg = 0
			pgcheck = 0

		if not desc.spatialReference.name == "GCS_WGS_1984":
			printlog("{} is not in WGS84 but in {}".format(shp["shp"],desc.spatialReference.name), "E")
			check_all_wgs84 = 0
			wgscheck = 0

	# check remap tables
	remap_file_name = shp['remap_tbl'].rstrip()
	# check previous version
	expression = arcpy.AddFieldDelimiters(tbl_upload_history, 'country_iso3') + " = '{}'".format(country_iso3)
	fields = ['country_iso3', 'version', 'upload_date']
	with arcpy.da.SearchCursor(tbl_upload_history, fields, where_clause=expression) as sTblHistoryCursor:
		versions = [[h[0], h[1], h[2]] for h in sTblHistoryCursor]
	highest_version = 0
	if len(versions) > 0:
		highest_version = max(v[1] for v in versions)
	del sTblHistoryCursor

	exists_remap = 0

	# check if remap table is required (previous version exists)
	if highest_version > 0: # REMAP required
		if remap_file_name:
			remap_file_path = os.path.join(base_folder, remap_file_name)
			exists_remap = os.path.isfile(remap_file_path)
			if not exists_remap:
				printlog("Remap file {} for {} level {} does not exist".format(remap_file_name, country_iso3, level), "E")
				check_all_remaps_provided_and_exists = 0
		else:
			printlog(
				"Remap for {} (level {}) is not provided but is required due to existing previous version. Provide valid remap table!".format(
					country_iso3, shp['level']), "E")
			check_all_remaps_required_and_provided = 0
			remapcheck_provided = 0

	else: # REMAP not required
		if remap_file_name:
			printlog(
				"Remap for {} (level {}) is provided ({}) but is not required due to no previous version and will be skipped".format(
					country_iso3, shp['level'], remap_file_name), "W")

		printlog("{}\t{}\t{}\t{}\t{}\t{}".format(shp["shp"],exists, pgcheck, wgscheck, remapcheck_provided, exists_remap))

if check_all_shp ==0 or check_all_pg ==0 or check_all_wgs84 ==0 or check_all_remaps_required_and_provided ==0 or check_all_remaps_provided_and_exists ==0:
	sys.exit()
printlog("All checks completed succesfully")


#######################################
# UPLOAD DATA PER COUNTRY
#######################################

dic_uuids = {}
counter = 1
list_countries = sorted(set([a['iso3'] for a in shp_list]))
dic_iso3 = {}

for l in list_countries:
	###########################
	# START A NEW 'UPLOAD': one country, all admin levels, get all required data for tbl_upload_history
	###########################
	upload_uuid = str(uuid.uuid4()).upper()
	country_iso3 = l

	# check previous version
	expression = arcpy.AddFieldDelimiters(tbl_upload_history, 'country_iso3') + " = '{}'".format(l)
	fields = ['country_iso3', 'version', 'upload_date']
	with arcpy.da.SearchCursor(tbl_upload_history, fields, where_clause=expression) as sTblHistoryCursor:
		versions = [[h[0],h[1],h[2]] for h in sTblHistoryCursor]
	highest_version = 0
	if len(versions) > 0:
		highest_version = max(v[1] for v in versions)
	current_version = int(highest_version) + 1
	del sTblHistoryCursor

	source = "" # ToDO: add source field to list in csv
	upload_date = start_date
	valid_from = start_date
	adm_inputs = []
	adm_counts = []
	adm_field_maps = []

	# get list of levels for a given country
	shp_list_by_country = [s for s in shp_list if s['iso3'] == l]
	shp_list_by_country_sorted = sorted(shp_list_by_country, key=lambda k: k['level'])

	# check if all levels are provided
	levels_provided = sorted(set([int(a['level']) for a in shp_list_by_country]))
	lev_check = 0
	check_all_lev = 1
	for lp in levels_provided:
		if lp != lev_check:
			check_all_lev = 0
		lev_check = lev_check + 1
	layer_status = "Processing"
	if check_all_lev == 0:
		printlog("Country {} update skipped! Incorrect list of levels provided.".format(l))
		layer_status = "Skipping"
	# TODO: change status of all previous locations to "Archived" + change dates

	for shp in shp_list_by_country_sorted:
		printlog("{} {}/{} - {}".format(layer_status, counter, len(shp_list), shp["shp"]))


		###########################
		# UPLOAD NEW LOCATIONS
		###########################
		outCountryISO2 = shp["iso2"]
		outCountryISO3 = shp["iso3"]
		out_admin_level = shp["level"]
		out_boundary_type_name = shp["def_lev_type"]
		out_data_type = "COD"
		dic_iso3[outCountryISO3] = outCountryISO2


		if layer_status == "Processing":

			append_layer = os.path.join(base_folder, shp["shp"] + ".shp")
			fields = ['SHAPE@' if f.type == 'Geometry' else f.name for f in arcpy.ListFields(append_layer)]

			adm_inputs.append(shp["shp"])

			adm_field_maps.append(shp)

			with arcpy.da.SearchCursor(append_layer, fields) as sCursor, \
				arcpy.da.InsertCursor(target_layer,
									  ['SHAPE@', 'uuid', 'country_iso2', 'country_iso3', 'admin_level', 'boundary_type_name', 'name', 'name_en', 'name_fr',
									   'name_es', 'name_ar', 'name_lo', 'p_code', 'parent_pcode', 'parent_uuid', 'all_fields', 'status', 'data_type', 'version', 'upload_uuid']) as insertCursor:
				ex_fields = sCursor.fields
				field_dic = {}
				i = 0
				for f in ex_fields:
					field_dic[f] = i
					i+=1


				out_status = "PA"  # PA - Pending Approval
				out_version = current_version
				out_upload_uuid = upload_uuid

				fcount = 0
				for row in sCursor:
					outShape = row[1]
					out_uuid = str(uuid.uuid4()).upper()
					out_name = None
					if shp['f_name'] and shp['f_name'] in field_dic:
						out_name = row[field_dic[shp['f_name']]]

					out_name_en = None
					if shp['f_name_en'] and shp['f_name_en'] in field_dic:
						out_name_en = row[field_dic[shp['f_name_en']]]

					out_name_fr = None
					if shp['f_name_fr'] and shp['f_name_fr'] in field_dic:
						out_name_fr = row[field_dic[shp['f_name_fr']]]

					out_name_es = None
					if shp['f_name_es'] and shp['f_name_es'] in field_dic:
						out_name_es = row[field_dic[shp['f_name_es']]]

					out_name_ar = None
					if shp['f_name_ar'] and shp['f_name_ar'] in field_dic:
						out_name_ar = row[field_dic[shp['f_name_ar']]]

					out_name_lo = None
					if shp['f_name_lo'] and shp['f_name_lo'] in field_dic:
						out_name_lo = row[field_dic[shp['f_name_lo']]]

					out_p_code = None
					if shp['f_pcode'] and shp['f_pcode'] in field_dic:
						out_p_code = row[field_dic[shp['f_pcode']]]
					if out_p_code not in list(dic_uuids.keys()):
						dic_uuids[out_p_code] = out_uuid

					if shp['f_lev_type_field'] and shp['f_lev_type_field'] in field_dic:
						if row[field_dic[shp['f_lev_type_field']]]:
							out_boundary_type_name = row[field_dic[shp['f_lev_type_field']]]

					out_parent_pcode = None
					if shp['f_parent_pcode'] and shp['f_parent_pcode'] in field_dic:
						out_parent_pcode = row[field_dic[shp['f_parent_pcode']]]

					out_parent_uuid = None
					if out_parent_pcode:
						out_parent_uuid = dic_uuids[out_parent_pcode]

					keys = fields
					values = list(row)
					all_fields_dict = dict(list(zip(fields, values)))
					del all_fields_dict['SHAPE@']
					all_fields = str(all_fields_dict)

					insertValues = [outShape, out_uuid, outCountryISO2, outCountryISO3, out_admin_level, out_boundary_type_name, out_name, out_name_en,
									out_name_fr, out_name_es, out_name_ar, out_name_lo, out_p_code, out_parent_pcode, out_parent_uuid, all_fields, out_status, out_data_type, out_version, out_upload_uuid]

					insertCursor.insertRow(insertValues)
					fcount = fcount + 1

			del sCursor
			del insertCursor

			# get number of features in a layer/admin level
			adm_counts.append(fcount)

			###########################
			# UPLOAD REMAP TABLES
			###########################
			remap_file_name = shp['remap_tbl'].rstrip()
			if remap_file_name:
				remap_file_path = os.path.join(base_folder, remap_file_name)
				remap_file = open(remap_file_path, "r")

				remap_list = []

				with arcpy.da.InsertCursor(tbl_remap_history,
										   ['country_iso3', 'upload_uuid', 'old_uuid', 'old_version', 'old_level', 'new_uuid',
											'new_version', 'new_level', 'remap_date', 'comments', 'old_pcode', 'new_pcode', 'old_name', 'new_name', 'name_sim', 'geomsim_old', 'geomsim_new', 'dis_dd', 'centr_dist_m']) as insertTblRemapCursor:
					c = 0
					for x in remap_file:
						if c != 0:
							line = re.split(r'\t+', x)
							remap_dic = {'old_uuid': line[0], 'old_pcode': line[1], 'new_pcode': line[2], 'pcode_check': line[3],
								 'old_name': line[4],
								 'new_name': line[5], 'name_sim': line[6], 'geomsim_old': line[7], 'geomsim_new': line[8],
								 'dis_dd': line[9], 'centr_dist_m': line[10], 'pCodeQC': line[11], 'NameQC': line[12],
								 'GeomQC': line[13], 'InUse': line[14]}
							remap_list.append(remap_dic)
							insertTblRemapValues = [outCountryISO2, outCountryISO3, upload_uuid, remap_dic['old_uuid'], highest_version, shp['level'], dic_uuids[remap_dic['new_pcode']], current_version, shp['level'], start_date,'', remap_dic['old_pcode'], remap_dic['new_pcode'], remap_dic['old_name'], remap_dic['new_name'], remap_dic['name_sim'], remap_dic['geomsim_old'], remap_dic['geomsim_new'], remap_dic['dis_dd'], remap_dic['centr_dist_m']]
							insertTblRemapCursor.insertRow(insertTblRemapValues)

						c = c + 1

				del insertTblRemapCursor
		counter += 1

	###########################
	# UPLOAD HISTORY
	###########################
	if layer_status == "Processing":
		adm0_input = ""
		adm1_input = ""
		adm2_input = ""
		adm3_input = ""
		adm4_input = ""
		adm5_input = ""
		adm6_input = ""
		adm0_count = 0
		adm1_count = 0
		adm2_count = 0
		adm3_count = 0
		adm4_count = 0
		adm5_count = 0
		adm6_count = 0
		adm0_field_map = ""
		adm1_field_map = ""
		adm2_field_map = ""
		adm3_field_map = ""
		adm4_field_map = ""
		adm5_field_map = ""
		adm6_field_map = ""
		is_active = 1

		if len(adm_inputs) > 0: adm0_input = adm_inputs[0]
		if len(adm_inputs) > 1: adm1_input = adm_inputs[1]
		if len(adm_inputs) > 2: adm2_input = adm_inputs[2]
		if len(adm_inputs) > 3: adm3_input = adm_inputs[3]
		if len(adm_inputs) > 4: adm4_input = adm_inputs[4]
		if len(adm_inputs) > 5: adm5_input = adm_inputs[5]
		if len(adm_inputs) > 6: adm6_input = adm_inputs[6]
		if len(adm_counts) > 0: adm0_count = adm_counts[0]
		if len(adm_counts) > 1: adm1_count = adm_counts[1]
		if len(adm_counts) > 2: adm2_count = adm_counts[2]
		if len(adm_counts) > 3: adm3_count = adm_counts[3]
		if len(adm_counts) > 4: adm4_count = adm_counts[4]
		if len(adm_counts) > 5: adm5_count = adm_counts[5]
		if len(adm_counts) > 6: adm6_count = adm_counts[6]
		if len(adm_field_maps) > 0: adm0_field_map = adm_field_maps[0]
		if len(adm_field_maps) > 1: adm1_field_map = adm_field_maps[1]
		if len(adm_field_maps) > 2: adm2_field_map = adm_field_maps[2]
		if len(adm_field_maps) > 3: adm3_field_map = adm_field_maps[3]
		if len(adm_field_maps) > 4: adm4_field_map = adm_field_maps[4]
		if len(adm_field_maps) > 5: adm5_field_map = adm_field_maps[5]
		if len(adm_field_maps) > 6: adm6_field_map = adm_field_maps[6]
		total_count = adm0_count + adm1_count + adm2_count + adm3_count + adm4_count + adm5_count + adm6_count

		with arcpy.da.InsertCursor(tbl_upload_history, ['uuid', 'country_iso2', 'country_iso3', 'version', 'upload_date', 'source', 'is_active', 'valid_from', 'adm0_input', 'adm1_input', 'adm2_input', 'adm3_input', 'adm4_input', 'adm5_input', 'adm6_input', 'adm0_count', 'adm1_count', 'adm2_count', 'adm3_count', 'adm4_count', 'adm5_count', 'adm6_count', 'total_count', 'adm0_field_map', 'adm1_field_map', 'adm2_field_map', 'adm3_field_map', 'adm4_field_map', 'adm5_field_map', 'adm6_field_map']) as insertTblHistCursor:
			insertTblHistValues = [upload_uuid, dic_iso3[country_iso3], country_iso3, current_version, upload_date, source, is_active, valid_from, adm0_input, adm1_input, adm2_input, adm3_input, adm4_input, adm5_input, adm6_input, adm0_count, adm1_count, adm2_count, adm3_count, adm4_count, adm5_count, adm6_count, total_count, str(adm0_field_map), str(adm1_field_map), str(adm2_field_map), str(adm3_field_map), str(adm4_field_map), str(adm5_field_map), str(adm6_field_map)]
			insertTblHistCursor.insertRow(insertTblHistValues)
		del insertTblHistCursor

		###########################
		# UPDATE VALID_TILL FOR PREVIOUS VERSION
		###########################
		if current_version > 1:
			expression = "{} = '{}' AND {} = {}".format(arcpy.AddFieldDelimiters(tbl_upload_history, 'country_iso3'), l, arcpy.AddFieldDelimiters(tbl_upload_history, 'version'), current_version - 1)
			fields = ['country_iso3', 'version', 'valid_till', 'is_active']
			with arcpy.da.UpdateCursor(tbl_upload_history, fields, where_clause=expression) as sTblHistoryUpdateCursor:
				for row in sTblHistoryUpdateCursor:
					row[2] = start_date
					row[3] = 0
					sTblHistoryUpdateCursor.updateRow(row)
			del sTblHistoryUpdateCursor

		###########################
		# CREATE OR UPDATE COUNTRY VIEW LAYER
		###########################
		gis = GIS("https://unicef-hq.maps.arcgis.com", username, passwd)
		# Search for Source Hosted Feature Layer
		source_search = gis.content.search("COD_Admin_Boundaries_Repository_MASTER")[0]
		source_flc = FeatureLayerCollection.fromitem(source_search)

		# Define View name
		view_name = "{}_View".format(country_iso3)

		# Check if View already exists
		view_search = gis.content.search(view_name)[0]

		# Create View from Source Hosted Feature Layer if not exists
		if not view_search:
			new_view = source_flc.manager.create_view(name=view_name)

		# Search for existing or newly created View
		view_search = gis.content.search(view_name)[0]
		view_flc = FeatureLayerCollection.fromitem(view_search)

		# The viewDefinitionQuery property appears under layers
		view_layer = view_flc.layers[0]

		# Define a SQL query to filter out locations for a given country and most recent version
		view_def = {"viewDefinitionQuery": "(country_iso3 = '{}') AND (version = {})".format(country_iso3, current_version)}

		# Update the definition to include the view definition query
		view_layer.manager.update_definition(view_def)



printlog("finished at: {}".format(datetime.datetime.now()))

