import urllib.request
import json
from styles import layer_styles
from lio_list import lio_list

print("Starting script...")


######### FUNCTIONS #############
# Constants

jsonSlug = '?f=pjson'
url_lio = f"https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer/"
json_lio1 = url_lio+jsonSlug

# Initializing qgis params
mapCanvas = iface.mapCanvas()
parent = iface.mainWindow()
projInstance = QgsProject.instance()
projCRS = mapCanvas.mapSettings().destinationCrs().authid()
ext = mapCanvas.extent()

treeRoot = QgsProject.instance().layerTreeRoot()
counter = 0
group_name = 'pyqgis' + str(counter)
while (treeRoot.findGroup(group_name)):
    counter += 1
    group_name = 'pyqgis' + str(counter)
pyqgis_group = treeRoot.insertGroup(0, group_name)


# Make the bounding box based on the map canvas for the service to query
## TODO Make a function that extracts the bounding box from a layer

def bbox_for_service(service_wkid_string, 
                     qgis_QgsProject=QgsProject, qgis_iface=iface, qgis_QgsCoordinateReferenceSystem=QgsCoordinateReferenceSystem, 
                     qgis_QgsPointXY=QgsPointXY, qgis_QgsCoordinateTransform=QgsCoordinateTransform):
    """
    This function returns a bounding box in the CRS of the service, to be passed to the REST call.

    Parameters:
        service_wkid_string (str): A string representing the ESRI REST Service CRS wkid (number).
        qgis_QgsProject (QgsProject): The QgsProject object. Default is QgsProject.
        qgis_iface (QgisInterface): The QGIS interface object. Default is iface.
        qgis_QgsCoordinateReferenceSystem (QgsCoordinateReferenceSystem): The QgsCoordinateReferenceSystem object. Default is QgsCoordinateReferenceSystem.
        qgis_QgsPointXY (QgsPointXY): The QgsPointXY object. Default is QgsPointXY.
        qgis_QgsCoordinateTransform (QgsCoordinateTransform): The QgsCoordinateTransform object. Default is QgsCoordinateTransform.

    Returns:
        str: A string representing the bounding box coordinates in the CRS of the service, formatted as "xmin,ymin,xmax,ymax".
    """
    mapCanvas = qgis_iface.mapCanvas()
    projCRS = mapCanvas.mapSettings().destinationCrs().authid()
    projInstance = qgis_QgsProject.instance()
    ext = mapCanvas.extent()

    # Get the map extent. Remember to zoom in to area of interest before running script
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()

    # Setup the transform
    sourceCrs = qgis_QgsCoordinateReferenceSystem(int(projCRS.split(':')[1])) #  Project CRS
    destCrs = qgis_QgsCoordinateReferenceSystem(int(service_wkid_string)) # Service CRS
    tform = qgis_QgsCoordinateTransform(sourceCrs, destCrs, projInstance)

    minPoint = tform.transform(qgis_QgsPointXY(xmin, ymin))
    maxPoint = tform.transform(qgis_QgsPointXY(xmax, ymax))

    return f"{minPoint.x()},{minPoint.y()},{maxPoint.x()},{maxPoint.y()}"

# define the REST API request by constructing the URL for each selected from the layer_list
def one_rest_request(url_string, service_wkid_string, treeLocation_to_add_layer, sql_string=None, qgis_QgsProject=QgsProject, qgis_QgsDataSourceUri=QgsDataSourceUri,
                     qgis_QgsVectorLayer=QgsVectorLayer):
    """
    Sends a REST request for one service URL and adds the resulting layer to the map canvas.

    Parameters:
        url_string (str): The REST URL string.
        service_wkid_string (str): The WKID (well-known ID) of the service's coordinate reference system (CRS) as a string.
        treeLocation_to_add_layer: The location in the layer tree where the layer should be added.
        sql_string (str, optional): The SQL query string to filter data. Default is None.
        qgis_QgsProject (QgsProject): The QgsProject object. Default is QgsProject.
        qgis_QgsDataSourceUri (QgsDataSourceUri): The QgsDataSourceUri object. Default is QgsDataSourceUri.
        qgis_QgsVectorLayer (QgsVectorLayer): The QgsVectorLayer object. Default is QgsVectorLayer.

    Returns:
        None
    """

    projInstance = qgis_QgsProject.instance()
    uri = qgis_QgsDataSourceUri()

    #TODO does the service wkid need to be an int?
    #TODO what if the service wkid is not EPSG?
    uri.setParam('crs', f"EPSG:{service_wkid_string}")
    uri.setParam('bbox', bbox_for_service(service_wkid_string))
    uri.setParam('url', f'{url_string}')
    # TODO some sort of try/catch for this since it can easily cause a failure...
    # TODO ask user for the name? Or get from the url.json?
    if sql_string:
        uri.setSql(f'{sql_string}')
    layer = qgis_QgsVectorLayer(uri.uri(), 'Layer from service' , 'arcgisfeatureserver')

    if layer.isValid():
        # set_layer_style(layer)
        projInstance.addMapLayer(layer, False)
        treeLocation_to_add_layer.addLayer(layer)

    else:
        print(f"Invalid layer: failed to add layer")

[print("Loading layer...")]

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
            print(f"No features exist: skipped layer {l}")

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
        
        # Make it scrollable
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
## END of CLASSES #####################################################################################

# open the url request
# TODO this could be hardcoded for simplicity, this logic was used to write v1 of this script but the response service crs shouldn't change...
with urllib.request.urlopen(json_lio1) as url:
    data = json.loads(url.read().decode())
# construct the url request for each selected crs
# TODO Delete next line if everything still working after testing
# layers = data['layers']
# get the service crs from the response
service_crs = str(data['spatialReference']['latestWkid'])

# pass the service crs into the bbox function created above
str_bbox = bbox_for_service(service_crs)

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
        # pass the selected layers into the rest request - i.e query for each of the selected layers
        rest_request(selected_layers)
        print("Script complete")
    else:
        print("User clicked Cancel. Stopping script.")
else:
    print("User clicked Cancel. Stopping script.")









