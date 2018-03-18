# ###########################
# SCRIPT 01B - CHECK DUPLICATE PCODES AGAINST MULTIPLE LAYERS
# ###########################

# input variables
input_layers = ["BGD_bnda_adm0_2015", "BGD_bnda_adm1_2015", "BGD_bnda_adm2_2015"]	# input admin layers (ordered from country -> lower levels
fnames = ["adm0_en","a1code","a2code"] # fields with pcodes for every level defined in input_layers


import sys
from qgis.core import *
from PyQt4.QtCore import *
import collections
from datetime import datetime, date, time


pcodes = []
duplids = []
duplpcodes = []
l = 0

print "############################"
print "CHECK DUPLICATE PCODES AGAINST MULTIPLE LAYERS"
print "############################"
print "Started: " + str(datetime.utcnow()) + "\n"


for in_lyr in input_layers:
	layerList = QgsMapLayerRegistry.instance().mapLayersByName(in_lyr)
	if layerList:
		fts = layerList[0].getFeatures()
		# check pcodes
		for ft in layerList[0].getFeatures():
			ftn = str(ft[fnames[l]]).strip()
			if ftn is not 'NULL':
				pcodes.append(ftn)
	l += 1
duplpcodes = [item for item, count in collections.Counter(pcodes).items() if count > 1]
duplquery = ''

for d in duplpcodes:
	duplquery = ",".join(list(duplpcodes))

duplpcodesperlyr = []
ftsaffected = []
l = 0
for in_lyr in input_layers:
	layerList = QgsMapLayerRegistry.instance().mapLayersByName(in_lyr)
	tempduplpcodes = []
	tempduplpcodesids = []
	
	if layerList:
		query = '"' + str(fnames[l]) + '" in (' + str(duplquery) + ')'
		selection = layerList[0].getFeatures(QgsFeatureRequest().setFilterExpression(query))
		layerList[0].setSelectedFeatures([k.id() for k in selection])
		selection = layerList[0].getFeatures(QgsFeatureRequest().setFilterExpression(query))
		for ft in selection:
			ftpc = str(ft[fnames[l]]).strip()
			ftsaffected.append(ft)
			tempduplpcodes.append(ftpc)
		duplpcodesperlyr.append([in_lyr, tempduplpcodes])
	l += 1

print "Tested layers: " + str(input_layers)
print "Tested pcode fields: " + str(fnames)

print "\nDuplicated Pcodes: " + str(duplpcodes)
print "\nTotal Number of duplicated pcodes: " + str(len(list(duplpcodes)))
print "Total Number of features affected: " + str(len(list(ftsaffected)))

print "\nLayer\tCountFeatures\tDuplPcodes"
for i in duplpcodesperlyr:
	print i[0] + "\t" + str(len(list(i[1]))) + "\t" + str(list(i[1]))

print "\nCompleted: " + str(datetime.utcnow())

