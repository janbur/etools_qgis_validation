# ###########################
# Create Pcodes - Add New Fields, Generate New Pcodes and Assign Parent Pcodes
# ###########################

import sys
import os
from qgis.core import *
from PyQt4.QtCore import *
from datetime import datetime, date, time

print "############################"
print "Create Pcodes - Add New Fields, Generate New Pcodes and Assign Parent Pcodes"
print "############################"
startDate = datetime.utcnow()
print "Started: " + str(startDate) + "\n"

# input new Pcode and Parent Pcode field names for all admin levels

class AdminLevel:
	def __init__(self, level, lyr_name, lyr, new_pc_f, new_n_f, old_pc_f, old_n_f, new_pc_fields, new_n_fields, fts):
		self.level = level
		self.lyr_name = lyr_name
		self.lyr = lyr
		self.new_pc_f = new_pc_f
		self.new_n_f = new_n_f
		self.old_pc_f = old_pc_f
		self.old_n_f = old_n_f
		self.new_pc_fields = new_pc_fields
		self.new_n_fields = new_n_fields
		self.fts = fts


admin_levels = []
admin_levels.append(AdminLevel(0, "BOL_adm0", None, None, None, None, "NAME_ENGLI", [], [], []))
admin_levels.append(AdminLevel(1, "BOL_adm1", None, None, None, None, "NAME_1", [], [], []))
admin_levels.append(AdminLevel(2, "BOL_adm2", None, None, None, None, "NAME_2", [], [], []))
admin_levels.append(AdminLevel(3, "BOL_adm3", None, None, None, None, "NAME_3", [], [], []))

country_iso2 = "BO"

NEW_PCODES = 1  # 1 - generate new Pcodes, 0 - map Pcodes from existing fields
UPDATE_NAMES = 1  # 1 - update names based on existing name field
UPDATE_PPCODES = 1  # 1 - update Parent Pcodes, 0 - do not update Parent Pcodes

# set layers and field names
for al in admin_levels:
	# set field names
	al.new_pc_f = "ADM{}_PCODE".format(al.level)
	al.new_n_f = "ADM{}_EN".format(al.level)

	# add layer
	temp_lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() == al.lyr_name]
	if len(temp_lyrs) == 1:
		al.lyr = temp_lyrs[0]
		al.fts = [ft for ft in temp_lyrs[0].getFeatures()]
	else:
		print "Two or more layers with the same name!"

errorCount = 0
qcstatus = ""


# print input settings
print "Input"
print "Level\tLayer\tDateModif\tNewPcodeField\tNewNameField\tOldPcodeField\tOldNameField\tFtCount"
for al in admin_levels:
	print "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(al.level,al.lyr_name, datetime.fromtimestamp(os.path.getmtime(al.lyr.dataProvider().dataSourceUri().split("|")[0])),al.new_pc_f, al.new_n_f, al.old_pc_f, al.old_n_f, al.lyr.featureCount())
print "\nSettings"
print "NEW_PCODES: {}".format(NEW_PCODES)
print "UPDATE_PPCODES: {}\n".format(UPDATE_PPCODES)


# Add new fields and assign Pcodes
for al in admin_levels:
	caps = al.lyr.dataProvider().capabilities()
	fnames = []
	if caps & QgsVectorDataProvider.AddAttributes:
		fields = al.lyr.dataProvider().fields()
		for field in fields:
			fnames.append(field.name())
		i = 0
		while i <= al.level:
			# add pcode field
			pc_fname = "ADM{}_PCODE".format(i)
			name_fname = "ADM{}_EN".format(i)
			if pc_fname in fnames:
				print "Level {} - field {} already exists in {}".format(al.level, pc_fname, al.lyr.name())
			else:
				al.lyr.dataProvider().addAttributes([QgsField(pc_fname, QVariant.String, len=50)])
				al.lyr.updateFields()
				al.new_pc_fields.append(pc_fname)
				print "Level {} - added field {} to {}".format(al.level, pc_fname, al.lyr.name())
			# add new name field
			if name_fname in fnames:
				print "Level {} - field {} already exists in {}".format(al.level, name_fname, al.lyr.name())
			else:
				al.lyr.dataProvider().addAttributes([QgsField(name_fname, QVariant.String, len=50)])
				al.lyr.updateFields()
				al.new_n_fields.append(name_fname)
				print "Level {} - added field {} to {}".format(al.level, name_fname, al.lyr.name())
			i += 1

	# Generate Pcodes
	new_pcode_fid = al.lyr.dataProvider().fieldNameIndex(al.new_pc_f)
	new_name_fid = al.lyr.dataProvider().fieldNameIndex(al.new_n_f)

	al.lyr.startEditing()
	resetCounter = 0
	if al.level == 0:
		count = len(al.fts)
		if count != 1:
			errorCount += 1
			print "{} - only 1 feature on level 0 is allowed".format(al.level)
		for ft in al.lyr.getFeatures():
			if NEW_PCODES == 1:
				al.lyr.changeAttributeValue(ft.id(), new_pcode_fid, country_iso2)
				if resetCounter == 0:
					print "Level {} - sample Pcode generated: {}".format(al.level,country_iso2)
					resetCounter += 1
			else:
				old_pcode = ft[al.old_pc_f]
				al.lyr.changeAttributeValue(ft.id(), new_pcode_fid, old_pcode)
				if resetCounter == 0:
					print "Level {} - sample Pcode generated: {}".format(al.level,old_pcode)
					resetCounter += 1
			if UPDATE_NAMES == 1:
				nameStr = ft[al.old_n_f]
				al.lyr.changeAttributeValue(ft.id(), new_name_fid, nameStr)
	else:
		parent_fts = admin_levels[al.level - 1].lyr.getFeatures()
		for pft in parent_fts:
			pcode = 1
			ppcodeStr = "{}".format(pft[admin_levels[al.level - 1].new_pc_f])
			for ft in al.lyr.getFeatures():
				if pft.geometry().contains(ft.geometry().pointOnSurface()):
					# Create New Pcodes or copy from existing Pcode field
					if NEW_PCODES == 1:
						pcodeStr = "{}{:02d}".format(ppcodeStr, pcode)
						al.lyr.changeAttributeValue(ft.id(), new_pcode_fid, pcodeStr)
						if resetCounter == 0:
							print "Level {} - sample Pcode generated: {}".format(al.level, pcodeStr)
							resetCounter += 1
						pcode += 1
					# Copy Pcode from existing field
					else:
						pcodeStr = ft[al.old_pc_f]
						al.lyr.changeAttributeValue(ft.id(), new_pcode_fid, pcodeStr)
						if resetCounter == 0:
							print "Level {} - sample Pcode generated: {}".format(al.level, pcodeStr)
							resetCounter += 1
					if UPDATE_NAMES == 1:
						nameStr = ft[al.old_n_f]
						al.lyr.changeAttributeValue(ft.id(), new_name_fid, nameStr)
	al.lyr.commitChanges()

# Update Parent Pcodes and Names
for al in admin_levels:
	# Update Parent Pcodes using string manipulation (works for new Pcodes generated by this script)
	print "{} - updating parents".format(al.level)
	al.lyr.startEditing()
	for ft in al.lyr.getFeatures():
		i = al.level - 1
		while i >= 0:
			pfts = admin_levels[i].lyr.getFeatures()
			new_ppcode_fid = al.lyr.dataProvider().fieldNameIndex("ADM{}_PCODE".format(i))
			new_pname_fid = al.lyr.dataProvider().fieldNameIndex("ADM{}_EN".format(i))
			for pft in pfts:
				if pft.geometry().contains(ft.geometry().pointOnSurface()):
					if UPDATE_PPCODES == 1:
						ppc = pft["ADM{}_PCODE".format(i)]
						# print "i:{},level:{},pcodeStr:{},ppc_temp:{}".format(i,al.level,pcodeStr,ppc_temp)
						al.lyr.changeAttributeValue(ft.id(), new_ppcode_fid, ppc)
						# print "Level {} - fid: {}, ppcode assigned: {}".format(l, ft.id(),ppcodeStr)
					if UPDATE_NAMES == 1:
						pn = pft["ADM{}_EN".format(i)]
						# print "i:{},level:{},pcodeStr:{},ppc_temp:{}".format(i,al.level,pcodeStr,ppc_temp)
						al.lyr.changeAttributeValue(ft.id(), new_pname_fid, pn)
						# print "Level {} - fid: {}, ppcode assigned: {}".format(l, ft.id(),ppcodeStr)
			i = i - 1
	al.lyr.commitChanges()

# update QC status
if errorCount == 0:
	qcstatus = "OK"
else:
	qcstatus = "MANUAL CHECK REQUIRED"


endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
print "\nQC STATUS:\t{}".format(qcstatus)
