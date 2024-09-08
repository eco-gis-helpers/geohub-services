import urllib.request
import json
from styles import layer_styles
from lio_list import lio_list
from func_service import *

print("Starting script...")

treeRoot = QgsProject.instance().layerTreeRoot()
counter = 0
group_name = 'pyqgis' + str(counter)
while (treeRoot.findGroup(group_name)):
    counter += 1
    group_name = 'pyqgis' + str(counter)
pyqgis_group = treeRoot.insertGroup(0, group_name)

## TODO Migrate these functions to the func_services method
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









