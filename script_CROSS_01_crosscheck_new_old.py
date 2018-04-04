# ###########################
# SCRIPT 04 v2.0 - CROSS-CHECK CASE A/B/C + LIST GEOM DUPLICATES IN CASE A FOR MANUAL CHECK
# ###########################

import sys
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time
from difflib import SequenceMatcher

#new_layers = ["BGD_bnda_adm0_2015","BGD_bnda_adm1_2015","BGD_bnda_adm2_2015","BDG_bnda_adm3_2015"]
#old_layers = ["bd_admin_0","bd_admin_1","bd_admin_2","bd_admin_3"]
#
#new_pcfnames = ["adm0_en","a1code","a2code","a3code"]
#old_ft_pcfnames = ["p_code","p_code","p_code","p_code"]
#
#new_namefnames = ["adm0_en","adm1_en","adm2_en","adm3_en"]
#old_namefnames = ["name","name","name","name"]

new_layers = ["bd_admin_2_new"]
old_layers = ["bd_admin_2_old"]

new_pcfnames = ["p_code"]
old_ft_pcfnames = ["p_code"]

new_namefnames = ["name"]
old_namefnames = ["name"]


results = []
l = 0

print "############################"
print "CROSS-CHECK CASE A/B/C + LIST GEOM DUPLICATES IN CASE A FOR MANUAL CHECK"
print "############################"
startDate = datetime.utcnow()
print "Started: " + str(startDate) + "\n"

if len(list(new_layers)) != len(list(old_layers)):
	sys.exit()


for new_lyr in new_layers:
	new_layerList = QgsMapLayerRegistry.instance().mapLayersByName(new_lyr)
	old_layerList = QgsMapLayerRegistry.instance().mapLayersByName(old_layers[l])
	old_lyr = str(old_layers[l])

	if new_layerList and old_layerList:
		new_pcode_fid = new_layerList[0].dataProvider().fieldNameIndex(new_pcfnames[l])
		old_ft_pcode_fid = old_layerList[0].dataProvider().fieldNameIndex(old_ft_pcfnames[l])

		new_fts = new_layerList[0].getFeatures()
		old_fts = old_layerList[0].getFeatures()
		
		new_pcodes = []
		old_pcodes = []
		
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
		for new_ft in new_layerList[0].getFeatures():
			new_ft_pc = str(new_ft[new_pcfnames[l]]).strip()
			if new_ft_pc:
				new_pcodes.append(new_ft_pc)
		# list old pcodes
		for old_ft in old_layerList[0].getFeatures():
			old_ft_pc = str(old_ft[old_ft_pcfnames[l]]).strip()
			if old_ft_pc:
				old_pcodes.append(old_ft_pc)
				old_ft_name = str(old_ft[old_namefnames[l]]).strip()
				old_ft_geom = old_ft.geometry()
				if old_ft_pc in new_pcodes:	#CASE A
					for new_ft in new_layerList[0].getFeatures():
						new_ft_pc = str(new_ft[new_pcfnames[l]]).strip()
						if new_ft_pc == old_ft_pc:
							new_ft_name = str(new_ft[new_namefnames[l]]).strip()
							new_ft_geom = new_ft.geometry()
							old_fts_caseA.append([old_ft.id(),old_ft_pc,old_ft_name])
							new_fts_caseA.append([new_ft.id(),new_ft_pc,new_ft_name])
							if not old_ft_geom.equals(new_ft_geom):	#CASE A - diff geom
								old_fts_caseA_modif_geom.append([old_ft.id(),old_ft_pc,old_ft_name])
								new_fts_caseA_modif_geom.append([new_ft.id(),new_ft_pc,new_ft_name])
								# Algorithm for measuring similarity of geometry
								intersect_geom = new_ft_geom.intersection(old_ft_geom)
								fts_caseA_modif_geom.append([new_ft_pc, (intersect_geom.area() / old_ft_geom.area() * 100), (intersect_geom.area() / new_ft_geom.area() * 100)])
							if new_ft_name <> old_ft_name:	#CASE A - diff name
								old_fts_caseA_modif_name.append([old_ft.id(),old_ft_pc,old_ft_name])
								new_fts_caseA_modif_name.append([new_ft.id(),new_ft_pc,new_ft_name])
								# Algorithm for measuring similarity of names
								similarity = SequenceMatcher(None, old_ft_name, new_ft_name).ratio()
								fts_caseA_modif_name.append([new_ft_pc, str(old_ft_name), str(new_ft_name), similarity])
				else:	#CASE B
					old_fts_caseB.append([old_ft.id(),old_ft_pc,old_ft_name])
		# list new pcodes
		for new_ft in new_layerList[0].getFeatures():
			new_ft_pc = str(new_ft[new_pcfnames[l]]).strip()
			new_ft_name = str(new_ft[new_namefnames[l]]).strip()
			if new_ft_pc:
				if new_ft_pc not in old_pcodes:	#CASE C
					new_fts_caseC.append([new_ft.id(),new_ft_pc,new_ft_name])

		old_fts_modif = [x[0] for x in old_fts_caseA_modif_geom] + [x[0] for x in old_fts_caseA_modif_name] + [x[0] for x in old_fts_caseB]
		new_fts_modif = [x[0] for x in new_fts_caseA_modif_geom] + [x[0] for x in new_fts_caseA_modif_name] + [x[0] for x in new_fts_caseC]
		
		old_layerList[0].setSelectedFeatures(old_fts_modif)
		new_layerList[0].setSelectedFeatures(new_fts_modif)
		
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
		results.append([len(list(old_fts)), len(list(new_fts)), len(list(new_fts_caseA)), len(list(old_fts_caseA_modif_geom)), len(list(new_fts_caseA_modif_name)), len(list(old_fts_caseB)), len(list(new_fts_caseC))])
		print "\n"
	l += 1
l=0
print "\nLev\tOld\tNew\tA\tAG\tAN\tB\tC"
for res in results:
	print str(l) + "\t" + str(res[0]) + "\t" + str(res[1]) + "\t" +  str(res[2]) + "\t" + str(res[3]) + "\t" + str(res[4]) + "\t" + str(res[5]) + "\t" + str(res[6])
	l+=1
endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
