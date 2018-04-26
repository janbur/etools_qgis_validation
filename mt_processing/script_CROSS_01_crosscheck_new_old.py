# ###########################
# CROSS-CHECK CASE A/B/C + LIST GEOM DUPLICATES IN CASE A FOR MANUAL CHECK
# ###########################

import sys
import os
import time
import requests
from datetime import datetime, date, time
from difflib import SequenceMatcher

from qgis.core import *
from qgis.gui import QgsMessageBar
from PyQt4 import QtCore, QtGui
#from PyQt4.QtCore import QVariant
from PyQt4.QtGui import *

#mt_processing/script_CROSS_01_crosscheck_new_old.py

class Worker(QtCore.QObject):
	def __init__(self):
		super(Worker, self).__init__()
		self.killed = False
		self.processed = 0
		self.percentage = 0

	def run(self):
		QgsMessageLog.logMessage("############################")
		QgsMessageLog.logMessage("CROSS-CHECK CASE A/B/C")
		QgsMessageLog.logMessage("############################")
		startDate = datetime.utcnow()
		QgsMessageLog.logMessage("Started: " + str(startDate) + "\n")

		new_pcfnames = ["admin0Pcod", "admin1Pcod", "admin2Pcod"]
		new_namefnames = ["COUNTRY", "ADMIN2", "ADMIN3"]
		# new_pcfnames = ["HRpcode", "HRpcode", "HRpcode"]
		# new_namefnames = ["HRname", "HRname", "HRname"]

		# set layers
		new_layers = [layer for layer in qgis.utils.iface.legendInterface().layers() if
					  layer.name() <> "locations_location"]

		old_layer = "locations_location"
		old_pcfname = "p_code"
		old_namefname = "name"
		old_layerList = QgsMapLayerRegistry.instance().mapLayersByName(old_layer)
		old_ft_pcode_fid = old_layerList[0].dataProvider().fieldNameIndex(old_pcfname)
		old_gateway_ids = [1, 2, -99]  # use -99 if no gateway id is available for a given admin level
		old_pcodes = []

		geomsim_treshold = 95
		textsim_treshold = 0.8

		old_gateway_fname = "gateway_id"
		old_ft_gateway_fid = old_layerList[0].dataProvider().fieldNameIndex(old_gateway_fname)

		results = []
		remaps = []
		remaps_missing = []
		remaps_multi = []
		l = 0

		# QgsMessageLog.logMessage(input settings
		QgsMessageLog.logMessage("Input")
		QgsMessageLog.logMessage("Level\tGatewayID\tLayer\tDateModif\tPcodeField\tNameField\tCount")
		for lyr in new_layers:
			QgsMessageLog.logMessage("{}\t{}\t{}\t{}\t{}\t{}\t{}".format(l, old_gateway_ids[l], lyr.name(), datetime.fromtimestamp(
				os.path.getmtime(lyr.dataProvider().dataSourceUri().split("|")[0])), new_pcfnames[l], new_namefnames[l],
													  lyr.featureCount()))
			l += 1
		l = 0

		# list old pcodes --> API GetPcodes
		for old_ft in old_layerList[0].getFeatures():
			old_ft_pc = str(old_ft[old_pcfname]).strip()
			if old_ft_pc:
				old_pcodes.append(old_ft_pc)

		#probably this is unnecessary performance overload.. it is used for more precise progressbar
		perc_nr = 0
		perc_count = 0
		for new_lyr in new_layers:
			if new_lyr and old_layerList:
				perc_count = len(new_lyr.getFeatures())
				expr = QgsExpression("\"gateway_id\"=" + str(old_gateway_ids[l]))
				perc_count = perc_count + len(old_layerList[0].getFeatures(QgsFeatureRequest(expr)))
			l += 1
		l = 0

		QgsMessageLog.logMessage("\nDetails")
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

				QgsMessageLog.logMessage("Level: " + str(l) + "\n")

				# list new pcodes
				for new_ft in new_fts:
					new_ft_pc = str(new_ft[new_pcfnames[l]]).strip()
					new_ft_name = str(new_ft[new_namefnames[l]]).strip()
					new_ft_geom = new_ft.geometry()
					if new_ft_pc:
						new_pcodes.append(new_ft_pc)
						if new_ft_pc in old_pcodes:  # CASE A

							for old_ft in old_layerList[0].getFeatures():
								old_ft_pc = str(old_ft[old_pcfname]).strip()
								if old_ft_pc == new_ft_pc:
									old_ft_name = old_ft[old_namefname].encode('utf-8').strip()
									old_ft_geom = old_ft.geometry()
									old_fts_caseA.append([old_ft.id(), old_ft_pc, old_ft_name])
									new_fts_caseA.append([new_ft.id(), new_ft_pc, new_ft_name])
									if not old_ft_geom.equals(new_ft_geom):  # CASE A - diff geom
										# Algorithm for measuring similarity of geometry
										intersect_geom = new_ft_geom.intersection(old_ft_geom)
										geomsim_old = (intersect_geom.area() / old_ft_geom.area() * 100)
										geomsim_new = (intersect_geom.area() / new_ft_geom.area() * 100)
										if (geomsim_old < geomsim_treshold) and (geomsim_new < geomsim_treshold):
											old_fts_caseA_modif_geom.append([old_ft.id(), old_ft_pc, old_ft_name])
											new_fts_caseA_modif_geom.append([new_ft.id(), new_ft_pc, new_ft_name])
											fts_caseA_modif_geom.append(
												[old_ft_pc, new_ft_pc, old_ft.id(), new_ft.id(), old_ft_name,
												 new_ft_name,
												 geomsim_old, geomsim_new])
									if new_ft_name <> old_ft_name:  # CASE A - diff name
										# Algorithm for measuring similarity of names
										textsim = SequenceMatcher(None, old_ft_name, new_ft_name).ratio()
										if textsim < textsim_treshold:
											old_fts_caseA_modif_name.append([old_ft.id(), old_ft_pc, old_ft_name])
											new_fts_caseA_modif_name.append([new_ft.id(), new_ft_pc, new_ft_name])
											fts_caseA_modif_name.append(
												[old_ft_pc, new_ft_pc, old_ft.id(), new_ft.id(), old_ft_name,
												 new_ft_name,
												 textsim])
						else:  # CASE C
							new_fts_caseC.append([new_ft.id(), new_ft_pc, new_ft_name])

					# Qthread specific
					perc_nr += 1
					self.percentage = round((perc_nr * 100) / perc_count)
					self.progress.emit(self.percentage)

				expr = QgsExpression("\"gateway_id\"=" + str(old_gateway_ids[l]))

				for old_ft in old_layerList[0].getFeatures(QgsFeatureRequest(expr)):
					old_ft_pc = str(old_ft[old_pcfname]).strip()
					old_ft_name = old_ft[old_namefname].encode('utf-8').strip()
					old_ft_geom = old_ft.geometry()
					if old_ft_pc:
						if old_ft_pc not in new_pcodes:  # CASE B
							old_fts_caseB.append([old_ft.id(), old_ft_pc, old_ft_name])
							# try to match removed location with new location
							remapflag = 0
							for new_ft in new_lyr.getFeatures():
								if new_ft.geometry().contains(old_ft.geometry().pointOnSurface()):
									new_ft_pc = str(new_ft[new_pcfnames[l]]).strip()
									new_ft_name = str(new_ft[new_namefnames[l]]).strip()
									new_ft_geom = new_ft.geometry()
									textsim = SequenceMatcher(None, old_ft_name, new_ft_name).ratio()
									intersect_geom = new_ft_geom.intersection(old_ft_geom)
									geomsim_old = (intersect_geom.area() / old_ft_geom.area() * 100)
									geomsim_new = (intersect_geom.area() / new_ft_geom.area() * 100)
									remaps.append(
										[l, old_ft.id(), new_ft.id(), old_ft_pc, new_ft_pc, old_ft_name, new_ft_name,
										 textsim,
										 geomsim_old, geomsim_new])
									remapflag += 1
								# QgsMessageLog.logMessage("Suggested remap from old ft: {}-{}-{} to new ft: {}-{}-{}".format(old_ft.id(),old_ft_pc,old_ft_name,new_ft.id(),new_ft_pc,new_ft_name)
							if remapflag == 0:
								remaps_missing.append([l, old_ft.id(), old_ft_pc, old_ft_name])
							elif remapflag > 1:
								remaps_multi.append([old_ft.id(), old_ft_pc, old_ft_name])

					# Qthread specific
					perc_nr += 1
					self.percentage = round((perc_nr * 100) / perc_count)
					self.progress.emit(self.percentage)

				old_fts_modif = [x[0] for x in old_fts_caseA_modif_geom] + [x[0] for x in old_fts_caseA_modif_name] + [
					x[0] for
					x in
					old_fts_caseB]
				new_fts_modif = [x[0] for x in new_fts_caseA_modif_geom] + [x[0] for x in new_fts_caseA_modif_name] + [
					x[0] for
					x in
					new_fts_caseC]

				old_layerList[0].setSelectedFeatures(old_fts_modif)
				new_lyr.setSelectedFeatures(new_fts_modif)
				QgsMessageLog.logMessage("CASE\tOLD PCODE\tNEW PCODE\tOLD FID\tNEW FID\tOLD NAME\tNEW NAME\tSIMILARITY")
				if len(list(fts_caseA_modif_geom)) > 0:
					for a_geom in fts_caseA_modif_geom:
						QgsMessageLog.logMessage("A-geom\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a_geom[0], a_geom[1], a_geom[2], a_geom[3],
																		  a_geom[4],
																		  a_geom[5],
																		  str(round(a_geom[6], 1)) + "/" + str(
																			  round(a_geom[7], 1))))
				if len(list(fts_caseA_modif_name)) > 0:
					for a_name in fts_caseA_modif_name:
						QgsMessageLog.logMessage("A-name\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(a_name[0], a_name[1], a_name[2], a_name[3],
																		  a_name[4],
																		  a_name[5], str(round(a_name[6], 1))))
				if len(list(old_fts_caseB)) > 0:
					for b in old_fts_caseB:
						QgsMessageLog.logMessage("B-remov\t{}\t\t{}\t\t{}\t".format(b[0], b[1], b[2]))
				if len(list(new_fts_caseC)) > 0:
					for c in new_fts_caseC:
						QgsMessageLog.logMessage("C-added\t\t{}\t\t{}\t\t{}".format(c[0], c[1], c[2]))
				results.append(
					[len(list(old_layerList[0].getFeatures(QgsFeatureRequest(expr)))), new_lyr.featureCount(),
					 len(list(new_fts_caseA)), len(list(old_fts_caseA_modif_geom)),
					 len(list(new_fts_caseA_modif_name)), len(list(old_fts_caseB)), len(list(new_fts_caseC))])
				QgsMessageLog.logMessage("\n")
			l += 1

		l = 0
		QgsMessageLog.logMessage("Summary")
		QgsMessageLog.logMessage("\nLev\tOld\tNew\tA\tAG\tAN\tB\tC")
		for res in results:
			QgsMessageLog.logMessage("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(l, res[0], res[1], res[2], res[3], res[4], res[5], res[6]))
			l += 1

		QgsMessageLog.logMessage("\nRemap Summary")
		# QgsMessageLog.logMessage(suggested remap table
		if len(list(remaps)) > 0:
			QgsMessageLog.logMessage("\nSuggested Remap Table")
			QgsMessageLog.logMessage("Lev\tOldFid\tNewFid\tOldFtPcode\tNewFtPcode\tOldFtName\tNewFtName\tNameSim\tGeomSimOld\tGeomSimNew")
			for remap in remaps:
				QgsMessageLog.logMessage("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(remap[0], remap[1], remap[2], remap[3], remap[4],
																	  remap[5], remap[6], round(remap[7], 2),
																	  round(remap[8], 2), round(remap[9], 2)))
		if len(list(remaps_missing)) > 0:
			QgsMessageLog.logMessage("\nMissing Locations without suggested match")
			for remap_mis in remaps_missing:
				QgsMessageLog.logMessage("{}\t{}\t{}\t{}".format(remap_mis[0], remap_mis[1], remap_mis[2], remap_mis[3]))
		if len(list(remaps_multi)) > 0:
			QgsMessageLog.logMessage("\nMissing Locations with multiple suggested matches")
			for remap_mis in remaps_multi:
				QgsMessageLog.logMessage("{}\t{}\t{}\t{}".format(remap_mis[0], remap_mis[1], remap_mis[2], remap_mis[3]))
		if len(list(old_fts_caseB)) == 0:
			QgsMessageLog.logMessage("Remap is not required - no removed Locations")
		endDate = datetime.utcnow()
		QgsMessageLog.logMessage("\nCompleted: " + str(endDate))
		QgsMessageLog.logMessage("Total processing time: " + str(endDate - startDate))

		#Qthread specific
		self.finished.emit(True)

	def kill(self):
		self.killed = True

	progress = QtCore.pyqtSignal(int)
	error = QtCore.pyqtSignal(Exception, basestring)
	killed = QtCore.pyqtSignal()
	finished = QtCore.pyqtSignal(object)
	status = QtCore.pyqtSignal(basestring)


class GisGui(QDialog):
	def __init__(self):
		"""Constructor."""
		super(GisGui, self).__init__()

		self.iface = qgis.utils.iface
		self.bar = QgsMessageBar()
		self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
		self.setLayout(QGridLayout())
		self.layout().setContentsMargins(0, 0, 0, 0)
		self.layout().addWidget(self.bar, 0, 0, 1, 1)

	def startWorker(self):
		# create a new worker instance
		worker = Worker()

		# configure the QgsMessageBar
		messageBar = self.iface.messageBar().createMessage('Processing data...', )
		progressBar = QtGui.QProgressBar()
		progressBar.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		QgsMessageLog.logMessage('Adding buttons...', )
		cancelButton = QtGui.QPushButton()
		cancelButton.setText('Cancel')
		cancelButton.clicked.connect(worker.kill)
		messageBar.layout().addWidget(progressBar)
		messageBar.layout().addWidget(cancelButton)
		self.iface.messageBar().pushWidget(messageBar, self.iface.messageBar().INFO)
		self.messageBar = messageBar

		# messageBar.layout.

		QgsMessageLog.logMessage('Starting threads...', )

		# start the worker in a new thread
		thread = QtCore.QThread(self)
		worker.moveToThread(thread)
		worker.finished.connect(self.workerFinished)
		worker.error.connect(self.workerError)
		worker.progress.connect(progressBar.setValue)
		thread.started.connect(worker.run)
		# worker.status.connect(self.iface.messageBar().pushMessage)
		# worker.status.connect(self.displaystatus)

		self.thread = thread
		self.worker = worker

		self.thread.start()

	def workerFinished(self, ret):
		# clean up the worker and thread
		QgsMessageLog.logMessage('Cleaning up...')

		self.worker.deleteLater()
		self.thread.quit()
		self.thread.wait()
		self.thread.deleteLater()

		# remove widget from message bar
		self.iface.messageBar().popWidget(self.messageBar)

		if ret is not None:
			# report the result
			self.iface.messageBar().pushMessage('Done...')
		else:
			# notify the user that something went wrong
			self.iface.messageBar().pushMessage(
				'Something went wrong! See the message log for more information.',
				level=QgsMessageBar.CRITICAL,
				duration=5
			)

	def workerError(self, e, exception_string):
		QgsMessageLog.logMessage(
			'Worker thread raised an exception:\n'.format(exception_string),
			 level=QgsMessageLog.CRITICAL
		)
		qgis.utils.iface.clearWidgets()

	def displaystatus(self, msg):
		self.iface.messageBar().pushMessage(msg, level=QgsMessageBar.INFO, duration=1)


gui = GisGui()
gui.startWorker()