############################
# SCRIPT 03 - UPDATE PARENT PCODES BASED ON CENTROID LOCATION AND INTERSECTION WITH FEATURES AT UPPER LEVEL REGIONS
############################

# input variables
input_layers = ["BGD_bnda_adm0_2015", "BGD_bnda_adm1_2015", "BGD_bnda_adm2_2015"]	# input admin layers (ordered from country -> lower levels
fnames = ["adm0_en","a1code","a2code"] # fields with pcodes for every level defined in input_layers
country_iso = "BG"

import sys
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtCore import QVariant
from datetime import datetime, date, time


admin_layers = []
l = 0


print "############################"
print "UPDATE PARENT PCODES BASED ON CENTROID LOCATION"
print "############################"
print "Started: " + str(datetime.utcnow()) + "\n"


for in_lyr in input_layers:
	layerList = QgsMapLayerRegistry.instance().mapLayersByName(in_lyr)
	if layerList:

		print "ANALYSIS OF LEVEL: " + str(l) + "[" + str(in_lyr) + "]"
		admin_layers.append(layerList[0])		
		counter = 0

		caps = layerList[0].dataProvider().capabilities()
		if caps & QgsVectorDataProvider.AddAttributes:
			fields = layerList[0].dataProvider().fields()
			for field in fields:
				fnames.append(field.name())
			if "new_pcode" in fnames:
				print "skip adding field \"new_p_code\" to " + str(in_lyr)
			else:
				layerList[0].dataProvider().addAttributes([QgsField("new_pcode", QVariant.String, len=34)])
				layerList[0].updateFields()
				print "added new field \"new_p_code\" to " + str(in_lyr)
			if "new_parent" in fnames:
				print "skip adding field \"new_parent\" to " + str(in_lyr)
			else:
				layerList[0].dataProvider().addAttributes([QgsField("new_parent", QVariant.String, len=34)])
				layerList[0].updateFields()
				print "added new field \"new_parent\" to " + str(in_lyr)
		new_pcode_fid = layerList[0].dataProvider().fieldNameIndex("new_pcode")
		new_parentcode_fid = layerList[0].dataProvider().fieldNameIndex("new_parent")

		admin_layers[l].startEditing()
		fts = admin_layers[l].getFeatures()
		
		if l==0:
			count = len(list(fts))
			print "number of features in current layer: " + str(count)
			print "this is top admin level - no parent layer"
			if count != 1:
				print in_lyr + " - only 1 feature on level 0 is allowed"
			for ft in admin_layers[l].getFeatures():
				ftid = ft.id()
				admin_layers[l].changeAttributeValue(ftid, new_pcode_fid, country_iso)
		else:
			parent_fts = admin_layers[l-1].getFeatures()
			print "number of features in current layer: " + str(len(list(fts)))
			print "number of features in parent layer: " + str(len(list(parent_fts)))

			for ft in admin_layers[l].getFeatures():
				ftid = ft.id()
				admin_layers[l].changeAttributeValue(ftid, new_pcode_fid, ft[fnames[l]])
				ft_centr = ft.geometry().pointOnSurface()
				for pft in admin_layers[l-1].getFeatures():
					pft_geom = pft.geometry()
					if ft_centr.intersects(pft_geom) == True:
						parent_code = pft["new_pcode"]
						admin_layers[l].changeAttributeValue(ftid, new_parentcode_fid, parent_code)
						counter+=1
		admin_layers[l].commitChanges()
		print "number of parent pcodes updated: " + str(counter) + "\n"
		l = l+1
print "\nCompleted: " + str(datetime.utcnow())
 
