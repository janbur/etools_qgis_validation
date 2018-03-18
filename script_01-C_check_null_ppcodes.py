############################
# SCRIPT 01C - CHECK NULL PARENT PCODES
############################

# input variables
input_layers = ["BGD_bnda_adm0_2015", "BGD_bnda_adm1_2015", "BGD_bnda_adm2_2015", "BDG_bnda_adm3_2015", "BGD_bnda_adm4_2015"]	# input admin layers (ordered from country -> lower levels
fpnames = ["adm0_en","a0code","a1code","a2code","a3code"] # fields with pcodes for every level defined in input_layers

import sys
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time


nullids = []
ftsaffected = []
l = 0

print "############################"
print "CHECK NULL PARENT PCODES"
print "############################"
print "Started: " + str(datetime.utcnow()) + "\n"


for in_lyr in input_layers:
	layerList = QgsMapLayerRegistry.instance().mapLayersByName(in_lyr)
	if layerList:
		if l>0:
			fts = layerList[0].getFeatures()
			# check pcodes
			tempnullids = []
			for ft in layerList[0].getFeatures():
				ftppc = str(ft[fpnames[l]]).strip()
				if ftppc is 'NULL' or ftppc =='':
					tempnullids.append(ft.id())
					ftsaffected.append(ft)
			layerList[0].setSelectedFeatures(tempnullids)
			nullids.append([in_lyr, tempnullids])
	l += 1
	
print "Tested layers: " + str(input_layers)
print "Tested parent pcode fields: " + str(fpnames)
print "\nNumber of features with empty parent pcodes:\t" + str(len(list(ftsaffected)))
print "\nLayer\tCountFeaturesWithEmptyPPcodes\tFeaturesIds"

for i in nullids:
	print i[0] + "\t" + str(len(list(i[1]))) + "\t" + str(list(i[1]))
print "\nCompleted: " + str(datetime.utcnow())