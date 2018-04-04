# ###########################
# SCRIPT 02 ver 2.0 - VALIDATE PARENT PCODES BASED ON CENTROID LOCATION AND INTERSECTION WITH FEATURES AT UPPER LEVEL REGIONS
# ###########################

# input variables

input_layers = ["BGD_bnda_adm0_2015", "BGD_bnda_adm1_2015", "BGD_bnda_adm2_2015"]	# input admin layers (ordered from country -> lower levels
fnames = ["adm0_en","a1code","a2code"] # fields with pcodes for every level defined in input_layers
fpnames = ["adm0_en","a0code","a1code"] # fields with pcodes for every level defined in input_layers

import sys
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time


errors = []
admin_layers = []
l = 0

print "############################"
print "VALIDATE PARENT PCODES BASED ON CENTROID LOCATION AND INTERSECTION WITH FEATURES AT UPPER LEVEL REGIONS"
print "############################"
print "Started: " + str(datetime.utcnow()) + "\n"

for in_lyr in input_layers:
	layerList = QgsMapLayerRegistry.instance().mapLayersByName(in_lyr)
	if layerList:
		admin_layers.append(layerList[0])		
		pcode_fid = layerList[0].dataProvider().fieldNameIndex(fnames[l])
		parentcode_fid = layerList[0].dataProvider().fieldNameIndex(fpnames[l])

		fts = admin_layers[l].getFeatures()
		ftsaffected = []
		tempwrongppc = []
		
		if l==0:
			count = len(list(fts))
			if count != 1:
				print in_lyr + " - only 1 feature on level 0 is allowed"
			for ft in admin_layers[l].getFeatures():
				ftpc = str(ft[fnames[l]]).strip()
				ftppc = str(ft[fpnames[l]]).strip()
				if ftpc is 'NULL' or ftpc =='':
					print "ERROR - Empty pcode at level 0"
		else:
			pfts = admin_layers[l-1].getFeatures()
			
			for ft in admin_layers[l].getFeatures():
				ft_centr = ft.geometry().pointOnSurface()
				ftpc = str(ft[fnames[l]]).strip()
				ftppc = str(ft[fpnames[l]]).strip()
				for pft in admin_layers[l-1].getFeatures():
					pft_geom = pft.geometry()
					if ft_centr.intersects(pft_geom) == True:
						pftn = str(pft[fnames[l-1]])
						if ftppc != pftn:
							print "Level: " + str(l) + ", pcode=" + ftpc + ", fid = " + str(ft.id()) + " has parent pcode: " + ftppc + ". Correct pcode is: " + pftn
							tempwrongppc.append(ftppc)
							ftsaffected.append(ft.id())
			errors.append([in_lyr, tempwrongppc])
			layerList[0].setSelectedFeatures(ftsaffected)
		l = l+1

print "\nLayer\tCountErrors\tWrongParentPcodes"
for i in errors:
	print i[0] + "\t" + str(len(list(i[1]))) + "\t" + str(list(i[1]))

print "\nCompleted: " + str(datetime.utcnow())
