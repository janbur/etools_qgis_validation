# ###########################
# SCRIPT 01A - CHECK NULL PCODES
# ###########################

# input variables
input_layers = ["BGD_bnda_adm0_2015", "BGD_bnda_adm1_2015", "BGD_bnda_adm2_2015"]	# input admin layers (ordered from country -> lower levels
fnames = ["adm0_en","a1code","a2code"] # fields with pcodes for every level defined in input_layers

import sys
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time


nullids = []
ftsaffected = []
l = 0

print "############################"
print "CHECK NULL PCODES"
print "############################"
print "Started: " + str(datetime.utcnow()) + "\n"


for in_lyr in input_layers:
	layerList = QgsMapLayerRegistry.instance().mapLayersByName(in_lyr)
	if layerList:
		fts = layerList[0].getFeatures()
		# check pcodes
		tempnullids = []
		for ft in layerList[0].getFeatures():
			ftn = str(ft[fnames[l]]).strip()
			if ftn is 'NULL' or ftn =='':
				tempnullids.append(ft.id())
				ftsaffected.append(ft)
		layerList[0].setSelectedFeatures(tempnullids)
		nullids.append([in_lyr, tempnullids])
	l += 1
	
print "Tested layers: " + str(input_layers)
print "Tested pcode fields: " + str(fnames)
print "\nNumber of features with empty pcodes:\t" + str(len(list(ftsaffected)))
print "\nLayer\tCountFeaturesWithEmptyPcodes\tFeaturesIds"

for i in nullids:
	print i[0] + "\t" + str(len(list(i[1]))) + "\t" + str(list(i[1]))
print "\nCompleted: " + str(datetime.utcnow())
