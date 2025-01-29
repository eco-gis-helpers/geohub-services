import urllib.request
import json
from styles import layer_styles
from lio_list import lio_list

print("Starting script...")

### Constants
mapCanvas = iface.mapCanvas()
parent = iface.mainWindow()
projInstance = QgsProject.instance()
projCRS = mapCanvas.mapSettings().destinationCrs().authid()
# ext = mapCanvas.extent() # the extent will change based on if the user selects "canvas" or "layer"
jsonSlug = '?f=pjson'
url_lio = f"https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer/"
json_lio1 = url_lio+jsonSlug


## Add an incrementing pyqgis group each time the script is run
treeRoot = projInstance.layerTreeRoot()

counter = 0
group_name = 'pyqgis' + str(counter)

# go through each group and increment the counter until it doesnt find a group with that name / number
while (treeRoot.findGroup(group_name)):
    counter += 1
    group_name = 'pyqgis' + str(counter)
pyqgis_group = treeRoot.insertGroup(0, group_name)

### FUNCTIONS ############################################################################################

# define the styles of the selected layers, from the style.py dictionary
def set_layer_style(layer):

    # Check if the layer name exists in the styles dictionary
    if layer.name() in layer_styles:

        # extract the style, renderer (point, fill, line), and opacity values from the dictionary in styles.py
        style = layer_styles[layer.name()]
        renderer = style['renderer']
        opacity = style['opacity']
        
        # have to use different QgsSymbol functions based on whether it is a point, fill or line
        if renderer == 'point':
            point_symbol = QgsMarkerSymbol.createSimple(style) ## QgsMarkerSymbol for points (aka markers)
            renderer = QgsSingleSymbolRenderer(point_symbol)
            layer.setRenderer(renderer)
            layer.setOpacity(opacity)
            layer.triggerRepaint()

        elif renderer == 'line':
            line_symbol = QgsLineSymbol.createSimple(style) ## QgsLineSymbol for lines
            renderer = QgsSingleSymbolRenderer(line_symbol)
            layer.setRenderer(renderer)
            layer.setOpacity(opacity)
            layer.triggerRepaint()

        elif renderer == 'fill':
            fill_symbol = QgsFillSymbol.createSimple(style) ## QgsFillSymbol for polygon fill colour
            renderer = QgsSingleSymbolRenderer(fill_symbol)
            layer.setRenderer(renderer)
            layer.setOpacity(opacity)
            layer.triggerRepaint()



# define the bounding box to query
def canvas_bbox_for_service(crs_string):
    """
    This is a function that returns a bounding box in the CRS of the service, to be passed to the REST call.
    :param crs_string: A string representing the ESRI REST Service CRS.
    """

    ext = mapCanvas.extent()

    # Get the map extent. Remember to zoom in to area of interest before running script
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()

    # Setup the transform
    # sourceCrs = QgsCoordinateReferenceSystem(int(projCRS.strip('EPSG:'))) #  Project CRS (initial method)
    sourceCrs = QgsCoordinateReferenceSystem(int(projCRS.split(':')[1])) #  Project CRS
    # print(sourceCrs)
    destCrs = QgsCoordinateReferenceSystem(int(crs_string)) # Service CRS
    # print(destCrs)
    tform = QgsCoordinateTransform(sourceCrs, destCrs, projInstance)

    minPoint = tform.transform(QgsPointXY(xmin, ymin))
    maxPoint = tform.transform(QgsPointXY(xmax, ymax))

    return f"{minPoint.x()},{minPoint.y()},{maxPoint.x()},{maxPoint.y()}"

# define the bounding box from an active layer to query
# And with multi polygons it creates a bounding box from all features
# having issues with this when the project projection is in UTM and not WGS

# does it have to use a bounding box, or could it use the exact geometry?
# TODO make it use the exact geometry vs. creating a bounding box around the feature
# In that case, maybe it should just use the "selected feature" as opposed to the "active layer"?
# If so, how to deal with multiple selected features? Might have to parse their geometries and make x calls to the API? Seems like a pain
def layer_bbox_for_service(crs_string):
    """
    This is a function that returns a bounding box in the CRS of the service, to be passed to the REST call.
    :param crs_string: A string representing the ESRI REST Service CRS.
    """

   # Get the active layer
    active_layer = iface.activeLayer()

    # if no active layer, raise a value error and notify the user
    # exiting out of the script with return is really slow for some reason, so I raise a ValueError
    if not active_layer:
        print("No layer selected!")
        iface.messageBar().pushMessage("Error", "No layer selected!", level=Qgis.Critical)
        raise ValueError("No layer selected!")
        # return

    # otherwise get the extent of the active layer
    else:

        ext = active_layer.extent()  # Get the extent of the active layer

        # here is where we'd have to change to use the geometry instead of the extent?
        # Get the active layer extent
        xmin = ext.xMinimum()
        xmax = ext.xMaximum()
        ymin = ext.yMinimum()
        ymax = ext.yMaximum()

        # Setup the transform as per usual
        # sourceCrs = QgsCoordinateReferenceSystem(int(projCRS.strip('EPSG:'))) #  Project CRS (initial method)
        sourceCrs = QgsCoordinateReferenceSystem(int(projCRS.split(':')[1])) #  Project CRS
        # print(sourceCrs)
        destCrs = QgsCoordinateReferenceSystem(int(crs_string)) # Service CRS
        # print(destCrs)
        tform = QgsCoordinateTransform(sourceCrs, destCrs, projInstance)

        minPoint = tform.transform(QgsPointXY(xmin, ymin))
        maxPoint = tform.transform(QgsPointXY(xmax, ymax))

        return f"{minPoint.x()},{minPoint.y()},{maxPoint.x()},{maxPoint.y()}"

# define the REST API request by constructing the URL for each selected from the layer_list
def rest_request(layer_list):
    """
    Sends REST requests for each layer in the given list.
    :param layer_list: A list of layer ids and names.
    """
    for l in layer_list:

        #Use this if you want to filter by more than bounding box
        #https://gis.stackexchange.com/questions/456167/pyqgis-add-arcgis-feature-service-layer-to-qgis-including-a-query
        uri = QgsDataSourceUri()
        # TODO 'EPSG' handcoded here makes this function less generalizable than it could be
        uri.setParam('crs', f"EPSG:{service_crs}")
        uri.setParam('bbox', str_bbox)
        uri.setParam('url', f"https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open{l[2]}/MapServer/{l[0]}")
        layer = QgsVectorLayer(uri.uri(), f"{l[1]}" , 'arcgisfeatureserver')

        if layer.isValid() and layer.featureCount() > 0:

            set_layer_style(layer)
            projInstance.addMapLayer(layer, False)
            pyqgis_group.addLayer(layer)

        elif layer.isValid() and layer.featureCount() == 0:
            print(f"No features exist: skipped layer {l}. Check your projection")

        else:
            print(f"Invalid layer: failed to add layer {l}")

    [print("Loading", x[1], "layer...") for x in layer_list]

### END of FUNCTIONS #######################################################################################

## CLASSES #################################################################################################
# Make the layer selection dialog box and checkboxes        
class WarningDialog(QDialog):
    def __init__(self, warn_str):
        super().__init__()
        
        self.setWindowTitle("Zoom Warning")
        layout = QVBoxLayout()
        
        warning_label = QLabel(warn_str)
        layout.addWidget(warning_label)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)
        
        
        #return_value = layout.exec()


# TODO it would be great to discuss how this works exactly and how challenging it would be to implement select multiple functionality


class LayerSelectionDialog(QDialog):
    def __init__(self, layers):
        super().__init__()

        self.setWindowTitle("Layer Selection")
        layout = QVBoxLayout()

        # Radio buttons to choose between bbox functions
        self.radio_layer_bbox = QRadioButton("Use selected layer for bbox")
        self.radio_canvas_bbox = QRadioButton("Use canvas for bbox")
        
        # Set default selection
        self.radio_canvas_bbox.setChecked(True)

        # Add radio buttons to the layout
        layout.addWidget(self.radio_layer_bbox)
        layout.addWidget(self.radio_canvas_bbox)

        # Make it scrollable for layers
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a widget for the checkboxes (a scroll layout within a layout)
        widget = QWidget()
        scroll_layout = QVBoxLayout()
        widget.setLayout(scroll_layout)

        # Create checkboxes for each layer
        self.checkboxes = []
        for layer in layers:
            checkbox = QCheckBox(layer[1])
            checkbox.setChecked(False)  # By default, no layers are selected
            scroll_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        scroll_area.setWidget(widget)
        layout.addWidget(scroll_area)

        # Add the OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)

    def selected_layers(self):
        selected = []
        for checkbox, layer in zip(self.checkboxes, lio_list):
            if checkbox.isChecked():
                selected.append(layer)
        return selected

    def get_bbox_function(self):
        # Return the selected bounding box function
        if self.radio_layer_bbox.isChecked():
            return "layer_bbox_for_service"
        else:
            return "canvas_bbox_for_service"

## END of CLASSES #####################################################################################

# open the url request
# TODO this could be hardcoded for simplicity, this logic was used to write v1 of this script but the response service crs shouldn't change...
with urllib.request.urlopen(json_lio1) as url:
    data = json.loads(url.read().decode())
# construct the url request for each selected crs
# TODO Delete next line if everything still working after testing
# layers = data['layers']
# get the service crs from the response

## dont think these are needed here anymore - we call the service_crs and bbox once the user selects which bbox they want to use (canvas or layer)
service_crs = str(data['spatialReference']['latestWkid'])
# pass the service crs into the bbox function created above
# str_bbox = canvas_bbox_for_service(service_crs)

# make the warning dialog string and pass it to the class above
warn_str = 'Please make sure you are zoomed in sufficiently!\nOtherwise QGIS may crash...'
warn_dialog = WarningDialog(warn_str)

# pass the lio list to the layer selection dialog class made above
dialog = LayerSelectionDialog(lio_list)

## Wrap the main dialog window in the warning dialog window and communicate to the user based on the selections
## the main dialog passes the selected layers from the checkboxes into the rest_request function above which actually hits the API to load the selected layers

if warn_dialog.exec_() == QDialog.Accepted:
    print("Zoom warning accepted. Selecting layers of interest")
    if dialog.exec_() == QDialog.Accepted:
        selected_layers = dialog.selected_layers()
        
        if dialog.get_bbox_function() == "layer_bbox_for_service":
            str_bbox = layer_bbox_for_service(service_crs)
        elif dialog.get_bbox_function() == "canvas_bbox_for_service":
            str_bbox = canvas_bbox_for_service(service_crs)

        # pass the selected layers into the rest request - i.e query for each of the selected layers

        rest_request(selected_layers)

        print("Script complete")
    else:
        print("User clicked Cancel. Stopping script.")
else:
    print("User clicked Cancel. Stopping script.")

