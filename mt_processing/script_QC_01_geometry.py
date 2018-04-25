# ###########################
# Geometry QC Check
# ###########################
import itertools
import os
from datetime import datetime
import time

from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import QgsMessageBar
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QVariant

#mt_processing/script_QC_01_geometry.py

class Worker(QtCore.QObject):
    def __init__(self):
        super(Worker, self).__init__()
        self.killed = False
        self.processed = 0
        self.percentage = 0

    def run(self):
        QgsMessageLog.logMessage("############################")
        QgsMessageLog.logMessage("Geometry QC Check")
        QgsMessageLog.logMessage("############################")
        startDate = datetime.utcnow()
        QgsMessageLog.logMessage("Started: {}\n".format(str(startDate)))

        # input Pcode, Parent Pcode and Name fields for all admin levels
        pc_fields = ["HRpcode", "HRpcode", "HRpcode"]
        ppc_fields = ["HRparent", "HRparent", "HRparent"]
        name_fields = ["HRname", "HRname", "HRname"]

        # set layers
        lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() != "locations_location"]
        lyrs_count = len(lyrs)

        # threshold size for intersections
        thres = 0.0000001

        # level counter
        l = 0

        # QgsMessageLog.logMessage(input settings)
        QgsMessageLog.logMessage("Input")
        QgsMessageLog.logMessage("Level\tLayer\tDateModif\tPcodeField\tPPcodeField\tCount")
        for lyr in lyrs:
            QgsMessageLog.logMessage("{}\t{}\t{}\t{}\t{}\t{}".format(l, lyr.name(), datetime.fromtimestamp(
                os.path.getmtime(lyr.dataProvider().dataSourceUri().split("|")[0])), pc_fields[l], ppc_fields[l],
                                                                     lyr.featureCount()))
            l += 1
        l = 0

        QgsMessageLog.logMessage( "Threshold size for intersections: {}".format(thres))

        def timeDiff():
            timedif = datetime.utcnow() - timeDiff.prevDate
            timeDiff.prevDate = datetime.utcnow()
            return str(timedif.seconds + float(timedif.microseconds) / 1000000)

        timeDiff.prevDate = datetime.utcnow()

        # Loop all layers
        l = 0

        results = []
        errorCount = 0
        qcstatus = ""

        QgsMessageLog.logMessage( "\nDetails")
        for lyr in lyrs:
            QgsMessageLog.logMessage( "\nAnalysing Level {}".format(l))
            geomerrors = []
            # create a memory layer for intersections
            mem_layer = QgsVectorLayer("MultiPolygon?crs=epsg:4326", "{}_overlaps".format(lyr.name()), "memory")
            mem_layer.startEditing()
            pr = mem_layer.dataProvider()
            pr.addAttributes(
                [QgsField("lyrid", QVariant.String), QgsField("fid1", QVariant.Int), QgsField("fid2", QVariant.Int)])

            # prepare a loop on the input layer
            polygons = []
            for feature in lyr.getFeatures():
                geom = feature.geometry()
                if geom:
                    err = geom.validateGeometry()
                    if not err:
                        polygons.append(feature)
                    else:
                        polygons.append(feature)
                        geomerrors.append([err, feature.id()])
                        errorCount += 1
                        for er in err:
                            QgsMessageLog.logMessage( "\t{}".format(er.what()))
            lyr.setSelectedFeatures([g[1] for g in geomerrors])
            counter = 1
            overlaps = []
            combCount = len(list(itertools.combinations(polygons, 2)))
            for feature1, feature2 in itertools.combinations(polygons, 2):
                if feature1.geometry().intersects(feature2.geometry()):
                    geom = feature1.geometry().intersection(feature2.geometry())
                    if geom.area() > thres:
                        QgsMessageLog.logMessage( "\t {}% - {} is intersecting with {} (area: {}, {}%)".format(
                            str(round((float(counter) / combCount) * 100, 2)), feature1.id(), feature2.id(),
                            geom.area(),
                            feature1.geometry().area() / geom.area() * 100))
                        feature = QgsFeature()
                        fields = mem_layer.pendingFields()
                        feature.setFields(fields, True)
                        feature.setAttributes([lyr.name(), feature1.id(), feature2.id()])
                        feature.setGeometry(geom)
                        pr.addFeatures([feature])
                        mem_layer.updateExtents()
                        mem_layer.commitChanges
                        overlaps.append([feature1.id(), feature2.id()])
                        errorCount += 1
                counter += 1

                #qthread related
                #QtCore.QThread.sleep(1)
                self.percentage = round((counter * 100) / combCount)
                self.progress.emit(self.percentage)

            mem_layer.commitChanges()
            if len(list(overlaps)) > 0:
                QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
            results.append([geomerrors, overlaps])
            l += 1

        l = 0

        QgsMessageLog.logMessage( "\nSummary")
        QgsMessageLog.logMessage( "\nLevel\tGeomErrors\tIntersections")
        for r in results:
            QgsMessageLog.logMessage( "{}\t{}\t{}".format(l, len(r[0]), len(r[1])))
            l += 1

        # update QC status
        if errorCount == 0:
            qcstatus = "OK"
        else:
            qcstatus = "MANUAL CHECK REQUIRED"

        endDate = datetime.utcnow()
        QgsMessageLog.logMessage( "\nCompleted: " + str(endDate))
        QgsMessageLog.logMessage( "Total processing time: " + str(endDate - startDate))
        QgsMessageLog.logMessage( "\nQC STATUS:\t{}".format(qcstatus))

        # qthread related
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
                duration=3
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
# gui.show()
gui.startWorker()