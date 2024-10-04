# Make a dialog box that accepts two user inputs. 1 - the layout name. 2 - the map title.
# Could expand this to include more user input - scale, extent?
class MultiInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle('Input Layout and Map Names')
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add layout name input field
        self.layout_label = QLabel("Enter the layout name:")
        self.layout_input = QLineEdit(self)
        layout.addWidget(self.layout_label)
        layout.addWidget(self.layout_input)
        
        # Add map title input field
        self.map_label = QLabel("Enter the map title:")
        self.map_input = QLineEdit(self)
        layout.addWidget(self.map_label)
        layout.addWidget(self.map_input)
        
        # Add buttons (OK and Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        self.setLayout(layout)
        
    # get and return the input values
    def getInputs(self):
        return self.layout_input.text(), self.map_input.text()

# Function to get user inputs
def getLayoutAndMapNames():
    dialog = MultiInputDialog()
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        layout_name, map_title = dialog.getInputs()
        print(f"Your {map_title} map is ready in 'Layouts' ")
        if not layout_name or not map_title:
            raise Exception("Both layout name and map title must be provided!")
        return layout_name, map_title
    else:
        raise Exception("User cancelled the dialog!")

# Get layout name and map title from user input
try:
    layout_name, map_title = getLayoutAndMapNames()
except Exception as e:
    layout_name, map_title = 'Unknown'


# Check for duplicate layouts
project = QgsProject.instance()
manager = project.layoutManager()
layouts_list = manager.printLayouts()

for layout in layouts_list:
    if layout.name() == layout_name:
        QMessageBox.critical(iface.mainWindow(), 'Error', f"A layout with the name '{layout_name}' already exists!")
        raise Exception(f"Duplicate layout name: {layout_name}")

# Create layout if no duplicate layout found
layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName(layout_name)
manager.addLayout(layout)

# Set layout size to landscape 8.5 x 11 inches (215.9 mm x 279.4 mm)
# layout.pageCollection().page(0).setPageSize(QgsLayoutSize(279.4, 215.9, QgsUnitTypes.LayoutMillimeters))



# Get all visible layers in the layer pane
layers = []
root = QgsProject.instance().layerTreeRoot()

for layer in QgsProject.instance().mapLayers().values():
    node = root.findLayer(layer.id())
    if node and node.isVisible():  # Check if the layer is visible in the layer tree
        layers.append(layer)

if not layers:
    print("No visible layers to map.")
    exit()


# Get the current map canvas extent
canvas = iface.mapCanvas()
extent = canvas.extent()

# MAP ITEM
map_item = QgsLayoutItemMap(layout)
map_item.setRect(60,60,60,60)
map_item.setExtent(extent)
layout.addLayoutItem(map_item)

map_item.attemptMove(QgsLayoutPoint(5.3, 2.85, QgsUnitTypes.LayoutMillimeters))
map_item.attemptResize(QgsLayoutSize(286, 204, QgsUnitTypes.LayoutMillimeters))


# MAP TITLE
title = QgsLayoutItemLabel(layout)
title.setText(map_title)
title.setFont(QFont('Arial', 16))
title.adjustSizeToText()
layout.addLayoutItem(title)
title.attemptMove(QgsLayoutPoint(95, 3, QgsUnitTypes.LayoutMillimeters))
title.attemptResize(QgsLayoutSize(196, 17, QgsUnitTypes.LayoutMillimeters))
title.setFrameEnabled(True)
title.setBackgroundEnabled(True)
title.setFrameStrokeColor(QColor('black'))
title.setHAlign(Qt.AlignCenter)
title.setVAlign(Qt.AlignCenter)

# LEGEND
legend = QgsLayoutItemLegend(layout)
layer_tree = QgsLayerTree()
for layer in layers:
    layer_tree.addLayer(layer)
legend.model().setRootGroup(layer_tree)
layout.addLayoutItem(legend)
legend.setFrameEnabled(True)
legend.setFrameStrokeColor(QColor('black'))
legend.attemptMove(QgsLayoutPoint(27, 183, QgsUnitTypes.LayoutMillimeters))

# SCALE BAR
# scalebar = QgsLayoutItemScaleBar(layout)
# scalebar.setStyle('Single Box')
# scalebar.setUnits(QgsUnitTypes.DistanceMeters)
# scalebar.setNumberOfSegments(3)
# scalebar.setNumberOfSegmentsLeft(0)
# scalebar.setUnitsPerSegment(1000)
# scalebar.setLinkedMap(map_item)
# scalebar.setUnitLabel('m')
# scalebar.update()
# layout.addLayoutItem(scalebar)
# scalebar.attemptMove(QgsLayoutPoint(137, 194, QgsUnitTypes.LayoutMillimeters))

# MAP INFO
map_info = QgsLayoutItemLabel(layout)
map_info.setText('Prepared on $CURRENT_DATE(yyyy-MM-dd). For illustrative purposes only. Some data may be omitted.')
map_info.setFont(QFont('Arial', 7))
map_info.adjustSizeToText()
layout.addLayoutItem(map_info)
map_info.attemptMove(QgsLayoutPoint(226, 197, QgsUnitTypes.LayoutMillimeters))
map_info.attemptResize(QgsLayoutSize(56.645, 9.398, QgsUnitTypes.LayoutMillimeters))
map_info.setBackgroundEnabled(True)
map_info.setFrameEnabled(True)

# # NORTH ARROW
# north = QgsLayoutItemPicture(layout)
# north.setPicturePath("C:/PROGRA~1/QGIS3~1.16/apps/qgis/./svg//arrows/NorthArrow_04.svg")
# layout.addLayoutItem(north)
# north.attemptResize(QgsLayoutSize(17, 14, QgsUnitTypes.LayoutMillimeters))
# north.attemptMove(QgsLayoutPoint(102, 192, QgsUnitTypes.LayoutMillimeters))


# # Add organization logo
# logo = QgsLayoutItemPicture(layout)
# logo.setPicturePath("C:/Users/Aidan/Desktop/logo.jpg")
# layout.addLayoutItem(logo)
# logo.attemptResize(QgsLayoutSize(81, 17, QgsUnitTypes.LayoutMillimeters))
# logo.attemptMove(QgsLayoutPoint(5.5, 2.850, QgsUnitTypes.LayoutMillimeters))
