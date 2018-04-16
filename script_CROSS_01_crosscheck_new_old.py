# ###########################
# CROSS-CHECK CASE A/B/C + LIST GEOM DUPLICATES IN CASE A FOR MANUAL CHECK
# ###########################

import sys
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time
from difflib import SequenceMatcher

import requests

new_pcfnames = ["admin0Pcod","admin1Pcod","admin2Pcod"]
new_namefnames = ["Country","ADMIN2","ADMIN3"]

# set layers
new_layers = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() <> "locations_location"]

old_layer = "locations_location"
old_pcfname = "p_code"
old_namefname = "name"
old_layerList = QgsMapLayerRegistry.instance().mapLayersByName(old_layer)
old_ft_pcode_fid = old_layerList[0].dataProvider().fieldNameIndex(old_pcfname)
old_gateway_ids = [1,2,99]
old_pcodes = []

geomsim_treshold = 95
textsim_treshold = 0.8

old_gateway_fname = "gateway_id"
old_ft_gateway_fid = old_layerList[0].dataProvider().fieldNameIndex(old_gateway_fname)

results = []
l = 0

print "############################"
print "CROSS-CHECK CASE A/B/C + LIST GEOM DUPLICATES IN CASE A FOR MANUAL CHECK"
print "############################"
startDate = datetime.utcnow()
print "Started: " + str(startDate) + "\n"

# list old pcodes --> API GetPcodes
for old_ft in old_layerList[0].getFeatures():
	old_ft_pc = str(old_ft[old_pcfname]).strip()
	if old_ft_pc:
		old_pcodes.append(old_ft_pc)


for new_lyr in new_layers:
	if new_lyr and old_layerList:
		new_pcode_fid = new_lyr.dataProvider().fieldNameIndex(new_pcfnames[l])
		new_fts = new_lyr.getFeatures()
		
		new_pcodes = []
		
		old_fts_caseA = []
		old_fts_caseA_modif_geom = []
		old_fts_caseA_modif_name = []
		new_fts_caseA = []
		new_fts_caseA_modif_geom = []
		new_fts_caseA_modif_name = []
		old_fts_caseB = []
		new_fts_caseC = []

		old_fts_modif = []
		new_fts_modif = []
		
		fts_caseA_modif_geom = []
		fts_caseA_modif_name = []
		
		
		print "Level: " + str(l) + "\n"
		
		# list new pcodes
		for new_ft in new_fts:
			new_ft_pc = str(new_ft[new_pcfnames[l]]).strip()
			new_ft_name = str(new_ft[new_namefnames[l]]).strip()
			new_ft_geom = new_ft.geometry()
			if new_ft_pc:
				new_pcodes.append(new_ft_pc)
				if new_ft_pc in old_pcodes:	#CASE A
					
					for old_ft in old_layerList[0].getFeatures():
						old_ft_pc = str(old_ft[old_pcfname]).strip()
						if old_ft_pc == new_ft_pc:
							old_ft_name = old_ft[old_namefname].encode('utf-8').strip()
							old_ft_geom = old_ft.geometry()
							old_fts_caseA.append([old_ft.id(),old_ft_pc,old_ft_name])
							new_fts_caseA.append([new_ft.id(),new_ft_pc,new_ft_name])
							if not old_ft_geom.equals(new_ft_geom):	#CASE A - diff geom
								# Algorithm for measuring similarity of geometry
								intersect_geom = new_ft_geom.intersection(old_ft_geom)
								geomsim_old = (intersect_geom.area() / old_ft_geom.area() * 100)
								geomsim_new = (intersect_geom.area() / new_ft_geom.area() * 100)
								if (geomsim_old < geomsim_treshold) and (geomsim_new < geomsim_treshold):
									old_fts_caseA_modif_geom.append([old_ft.id(),old_ft_pc,old_ft_name])
									new_fts_caseA_modif_geom.append([new_ft.id(),new_ft_pc,new_ft_name])
									fts_caseA_modif_geom.append([new_ft_pc, geomsim_old, geomsim_new])
							if new_ft_name <> old_ft_name:	#CASE A - diff name
								# Algorithm for measuring similarity of names
								textsim = SequenceMatcher(None, old_ft_name, new_ft_name).ratio()
								if textsim < textsim_treshold:
									old_fts_caseA_modif_name.append([old_ft.id(),old_ft_pc,old_ft_name])
									new_fts_caseA_modif_name.append([new_ft.id(),new_ft_pc,new_ft_name])
									fts_caseA_modif_name.append([new_ft_pc, str(old_ft_name), str(new_ft_name), textsim])
				else:	#CASE C
					new_fts_caseC.append([new_ft.id(),new_ft_pc,new_ft_name])
		# list removed pcodes
		
		expr = QgsExpression( "\"gateway_id\"=" + str(old_gateway_ids[l]) )

		
		for old_ft in old_layerList[0].getFeatures(QgsFeatureRequest( expr )):
			old_ft_pc = str(old_ft[old_pcfname]).strip()
			old_ft_name = old_ft[old_namefname].encode('utf-8').strip()
			if old_ft_pc:
				if old_ft_pc not in new_pcodes:	#CASE B
					old_fts_caseB.append([old_ft.id(),old_ft_pc,old_ft_name])

		old_fts_modif = [x[0] for x in old_fts_caseA_modif_geom] + [x[0] for x in old_fts_caseA_modif_name] + [x[0] for x in old_fts_caseB]
		new_fts_modif = [x[0] for x in new_fts_caseA_modif_geom] + [x[0] for x in new_fts_caseA_modif_name] + [x[0] for x in new_fts_caseC]
		
		old_layerList[0].setSelectedFeatures(old_fts_modif)
		new_lyr.setSelectedFeatures(new_fts_modif)
		
		if len(list(fts_caseA_modif_geom)) > 0:
			for a_geo in fts_caseA_modif_geom:
				print "Case A-geom:\tpcode:\t" + a_geo[0] + "\tGeom similarity (old/new): " + str(round(a_geo[1],1)) + "/" + str(round(a_geo[2],1))
		if len(list(fts_caseA_modif_name)) > 0:
			for a_name in fts_caseA_modif_name:
				print "Case A-name:\tpcode:\t" + a_name[0] + "\t" + str(a_name[1]) + "\t" + str(a_name[2]) + "\tText similarity: " + str(round(a_name[3],1))
		if len(list(old_fts_caseB)) > 0:
			for b in old_fts_caseB:
				# ToDo: add check if Location in use -> suggest remap Location based on centroid location & geom / name similarity
				print "Case B-remov:\tpcode:\t" + str(b[1]) + "\tfid:\t" + str(b[0]) + "\t\tname:\t" + str(b[2])
		if len(list(new_fts_caseC)) > 0:
			for c in new_fts_caseC:
				print "Case C-added:\tpcode:\t" + str(c[1]) + "\tfid:\t" + str(c[0]) + "\t\tname:\t" + str(c[2])
		results.append([len(list(old_layerList[0].getFeatures(QgsFeatureRequest( expr )))), new_lyr.featureCount(), len(list(new_fts_caseA)), len(list(old_fts_caseA_modif_geom)), len(list(new_fts_caseA_modif_name)), len(list(old_fts_caseB)), len(list(new_fts_caseC))])
		print "\n"
	l += 1
l=0
print "\nLev\tOld\tNew\tA\tAG\tAN\tB\tC"
for res in results:
	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t".format(l,res[0],res[1],res[2],res[3],res[4],res[5],res[6])
	l+=1
endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
