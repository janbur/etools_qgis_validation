# ###########################
# QC CHECK VISUAL SNAPSHOTS
# ###########################

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import QProgressDialog, QProgressBar
from PyQt4.QtCore import QVariant
from datetime import datetime, date, time
import itertools
import os

print "############################"
print "QC CHECK VISUAL SNAPSHOTS"
print "############################"
startDate = datetime.utcnow()
print "Started: " + str(startDate) + "\n"

# input Pcode and Parent Pcode field names for all admin levels
fnames = ["admin0Pcod","admin1Pcod","admin2Pcod","admin3Pcod"]
fpnames = ["admin0Pcod","admin0Pcod","admin1Pcod","admin2Pcod"]

# set layers
lyrs = [layer for layer in qgis.utils.iface.legendInterface().layers() if layer.name() <> "locations_location"]

lyrsids = [i.id() for i in lyrs]
errorCount = 0
qcstatus = ""

# level counter
l = 0

# print input settings
print "INPUT"
print "Level\tLayer\tDateModif\tPcodeField\tPPcodeField\tCount"
for lyr in lyrs:
	print "{}\t{}\t{}\t{}\t{}\t{}".format(l,lyr.name(),datetime.fromtimestamp(os.path.getmtime(lyr.dataProvider().dataSourceUri().split("|")[0])),fnames[l],fpnames[l],lyr.featureCount())
	l+=1
l = 0



# create image
img = QImage(QSize(600, 600), QImage.Format_ARGB32_Premultiplied)

# set image's background color
color = QColor(255, 255, 255)
img.fill(color.rgb())

render = QgsMapRenderer()
render.setLayerSet(lyrsids)

# set extent
rect = QgsRectangle(render.fullExtent())
rect.scale(1.1)
render.setExtent(rect)

# Loop all layers
l = 0

print "\nDETAILS"
for lyr in lyrs:
	lst = []
	lst.append(lyr.id())
	render.setLayerSet(lst)
	
	render.setOutputSize(img.size(), img.logicalDpiX())
	# create painter
	p = QPainter()
	p.begin(img)
	p.setRenderHint(QPainter.Antialiasing)
	
	# do the rendering
	render.render(p)
	
	p.end()
	
	outdir = os.path.join(os.path.dirname(os.path.dirname(lyr.dataProvider().dataSourceUri())), "PNG")
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	filename = str(lyr.name()) + ".png"
	path = os.path.join(outdir, filename)
	
	#save image
	b = img.save(path,"png")
	print "Snapshot for level {} created at {}".format(l, path)

	l += 1


# update QC status
if errorCount == 0:
	qcstatus = "OK"
else:
	qcstatus = "MANUAL CHECK REQUIRED"

endDate = datetime.utcnow()
print "\nCompleted: " + str(endDate)
print "Total processing time: " + str(endDate - startDate)
print "\nQC STATUS:\t{}".format(qcstatus)
