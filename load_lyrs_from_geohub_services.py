import urllib.request
import json
import time
from styles import layer_styles
from lio_list import lio_list

# Start Timer
start_time = time.time() 
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

# get the users active layer
active_layer = iface.activeLayer()

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
    layer_name = layer.name()

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
    else:
        print(f"Layer '{layer_name}' not in style sheet")


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
    destCrs = QgsCoordinateReferenceSystem(int(crs_string)) # Service CRS
    tform = QgsCoordinateTransform(sourceCrs, destCrs, projInstance)

    minPoint = tform.transform(QgsPointXY(xmin, ymin))
    maxPoint = tform.transform(QgsPointXY(xmax, ymax))

    return f"{minPoint.x()},{minPoint.y()},{maxPoint.x()},{maxPoint.y()}"

def layer_bbox_for_service(service_crs):
    """
    Returns a list of bounding boxes from the active layer's feature geometries,
    ensuring they are in EPSG:4269
    params: crs_string: A string representing the ESRI REST Service CRS
    """
    bbox_list = []
    tform = None

    destCrs = QgsCoordinateReferenceSystem(int(service_crs))
    # Get the CRS of the active layer
    activeCrs = active_layer.crs()

    # if the active layers crs doesnt match the ESRI REST Service CRS, make a transformation
    if activeCrs.authid() != f"EPSG:{service_crs}":
        print("Tranformation needed...")
        tform = QgsCoordinateTransform(activeCrs, destCrs, QgsProject.instance())

    # reproject each feature
    for feature in active_layer.getFeatures():
        geometry = feature.geometry()

        # Reproject if necessary
        if tform:
            geometry.transform(tform)

        # Get bounding box in ESRI REST Service CRS
        bbox = geometry.boundingBox()
        # print(bbox)
        bbox_list.append(bbox)

    return bbox_list
        
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

            # added a count of how many features are added to the map
            feature_count = layer.featureCount()
            print(f"{feature_count} feature(s) within {layer.name()} were added to the map.")

        elif layer.isValid() and layer.featureCount() == 0:
            print(f"No features exist: skipped layer {l}")

        else:
            print(f"Invalid layer: failed to add layer {l}")

    [print("Loading", x[1], "layer...") for x in layer_list]

# function for when the user queries by an active layer
# it takes a list of bboxs from the features geometries
def layer_rest_request(bbox_list, layer_list):
    """
    Sends REST requests for each layer in the given list and flag invalid geometries to the user
    :param bbox_list: A list of bboxes returned from the layer_for_bbox_service function.
    :param layer_list: A list of layer ids and names.
    :returns: the list of layers to be clipped and loaded in.
    """
    loaded_layer_list = []
    invalid_flag = None
    for l in layer_list:
        for str_bbox in bbox_list:
            # Prepare bbox for the request
            str_bbox = f"{str_bbox.xMinimum()},{str_bbox.yMinimum()},{str_bbox.xMaximum()},{str_bbox.yMaximum()}"
            
            # Prepare URI for layer
            uri = QgsDataSourceUri()
            uri.setParam('crs', f"EPSG:{service_crs}")
            uri.setParam('bbox', str_bbox)
            uri.setParam('url', f"https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open{l[2]}/MapServer/{l[0]}")
            
            # Initialize layer from URI
            layer = QgsVectorLayer(uri.uri(), f"{l[1]}", 'arcgisfeatureserver')

            if layer.isValid() and layer.featureCount() > 0:
                # Check for invalid geometries
                for feature in layer.getFeatures():
                    geometry = feature.geometry()
                    if not geometry.isGeosValid():
                        invalid_flag = True
                        print(f"Invalid geometry found in feature {feature.id()} in layer {l[1]}.")
                loaded_layer_list.append(layer)
            elif layer.isValid() and layer.featureCount() == 0:
                print(f"No features exist: skipped layer {l}")
                loaded_layer_list.append(layer)
            else:
                print(f"Invalid layer: failed to add layer {l}")
                loaded_layer_list.append(layer)

    return loaded_layer_list, invalid_flag



# function to clip the resulting layer(s) (from the layer_bbox query function) with the active polygon(s) layer
# it takes a list of the loaded layers (from layer_bbox query), the active layer is the overlay layer and a list of their names (layer_id_list)
def clipping(loaded_layer_list, overlay_layer_list, layer_id_list, invalid_flag):
    
    """
    Fixes invalid geometries and clips each loaded layer from the bbox_query function against the temporary overlay_layers
    Renames the clipped layers based on their feature id, counts the resulting features and adds the clipped layers to the pyqgis group
    :param loaded_layer_list: A list of QgsVector layers from the layer_rest_request function
    :param overlay_layer_list: A list of temporary overlay layers (one for each feature from the active layer)
    :param layer_id_list: A list layer ids (one for each feature in the active layer)
    """
    # make sure the overlay_layer_lists and layer_id_lists are the same length as the loaded_layer_list
    # this ensures that each of the features has an overlay to be clipped and named to
    # the loaded_layer_list will have [selected_layers x number of features] items.
    # whereas the overlay_list will only have [number of features] items, so we use the modulo operator to match their lengths
    overlay_layer_list = [overlay_layer_list[i % len(overlay_layer_list)] for i in range(len(loaded_layer_list))]
    layer_id_list = [layer_id_list[i % len(layer_id_list)] for i in range(len(loaded_layer_list))]

    for loaded_layer, overlay_layer, layer_id in zip(loaded_layer_list, overlay_layer_list, layer_id_list):

        if invalid_flag:
            print("Fixing geometries...")
            # Fix invalid geometries before clipping
            fixed_layer = processing.run('qgis:fixgeometries', 
                {'INPUT': loaded_layer, 'OUTPUT': 'memory:'},
            )["OUTPUT"]

            # Clipping each of the selected layers to each feature in the active layer
            layer_clip = processing.run('qgis:clip',
                {'INPUT': fixed_layer,
                'OVERLAY': overlay_layer,
                'OUTPUT': "memory:"},
            )["OUTPUT"]

        else:

            # Clipping each of the selected layers to each feature in the active layer
            layer_clip = processing.run('qgis:clip',
                {'INPUT': loaded_layer,
                'OVERLAY': overlay_layer,
                'OUTPUT': "memory:"},
            )["OUTPUT"]

        layer_clip_result = QgsProject.instance().addMapLayer(layer_clip, False)

        # naming the clipped layers based on feature id so they can be styled
        layer_name = f"{loaded_layer.name()}"
        layer_clip.setName(layer_name)

        # style the layers
        set_layer_style(layer_clip_result)

        # # renaming again so you know what layer is associated to which feature
        layer_name = f"{loaded_layer.name()}_ID_{layer_id}"
        layer_clip.setName(layer_name)

        if layer_clip_result.isValid() and layer_clip_result.featureCount() > 0:
            # count the resulting features in each of the polygon features
            feature_count = layer_clip.featureCount()
            print(f"{feature_count} feature(s) within {layer_name} were added to the map.")
            pyqgis_group.addLayer(layer_clip_result)

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

service_crs = str(data['spatialReference']['latestWkid'])
# print("Service CRS: ", service_crs)

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
        
        # make a list to hold the temporary layers
        temp_layers = []
        if dialog.get_bbox_function() == "layer_bbox_for_service":
            print("Querying by Active Layer")


            # if no active layer, raise a value error and notify the user
            # exiting out of the script with 'return' is really slow for some reason
            # so raise a ValueError instead
            if not active_layer:
                print("No layer selected!")
                iface.messageBar().pushMessage("Error", "No layer selected!", level=Qgis.Critical)
                raise ValueError("No layer selected!")
                # return

            # If the active layer is a raster, throw an error
            elif active_layer.type() == QgsMapLayer.RasterLayer:
                print("The selected layer is a raster!")
                iface.messageBar().pushMessage("Error", "Selected layer is a raster!", level=Qgis.Critical)
                raise ValueError("Selected layer is a raster!")

            # If the active layer is a multi-polygon or polygon, keep going!
            elif QgsWkbTypes.displayString(active_layer.wkbType()) in ["MultiPolygon", "Polygon"]:
                pass

            # If the active layer is not a Polygon or MultiPolygon, throw an error
            else:
                print("The selected layer needs to be a polygon!")
                iface.messageBar().pushMessage("Error", "Selected layer is not a polygon!", level=Qgis.Critical)
                raise ValueError("Selected layer is not a polygon!")
                
            # get a list of the bboxes for each of these geometries
            bbox_list = layer_bbox_for_service(service_crs)

            layer_id_list = []
            overlay_layer_list = []

            for feature in active_layer.getFeatures():
                layer_id = feature.id()
                layer_id_list.append(layer_id)
                geometry = feature.geometry()

                # make temp layers of each feature in the active layer for the clipping function
                temp_layer_name = f"temp_clip_{layer_id}"
                # load the temp layers in memory
                temp_layer = QgsVectorLayer("Polygon?crs=" + active_layer.crs().authid(), temp_layer_name, "memory")
                temp_layer_provider = temp_layer.dataProvider()

                # # Add the feature geometry to the temporary layer
                temp_feature = QgsFeature()
                temp_feature.setGeometry(geometry)
                temp_layer_provider.addFeature(temp_feature)
                temp_layer.updateExtents()

                # Add the temporary layer to the project (for visibility in processing)
                QgsProject.instance().addMapLayer(temp_layer)
                temp_layers.append(temp_layer)
                # Now that the layer is in the project, use it in the processing tool as the overlay for clipping
                overlay_source = QgsProcessingFeatureSourceDefinition(temp_layer.id(), selectedFeaturesOnly=False)

                overlay_layer_list.append(overlay_source)

            # query the API using the bboxes from each geometry
            loaded_layer_list, invalid_flag = layer_rest_request(bbox_list, selected_layers)
                
            # call the clipping function
            # print(bbox_list)
            # print(loaded_layer_list)
            # print(invalid_flag)
            # print("done")
            clipping(loaded_layer_list, overlay_layer_list, layer_id_list, invalid_flag)

            # Remove the temporary layers after processing
            for temp_layer in temp_layers:
                QgsProject.instance().removeMapLayer(temp_layer)

        # otherwise the user selected the canvas bbox for query
        elif dialog.get_bbox_function() == "canvas_bbox_for_service":
            print("Querying by Canvas")
            # get the canvas bbox and query the api
            str_bbox = canvas_bbox_for_service(service_crs)
            rest_request(selected_layers)

        print("Script complete")
    else:
        treeRoot.removeChildNode(pyqgis_group)
        print("User clicked Cancel. Stopping script.")
else:
    treeRoot.removeChildNode(pyqgis_group)
    print("User clicked Cancel. Stopping script.")

# End Timer
end_time = time.time() 
elapsed_time = end_time - start_time
print(f"Script execution time: {elapsed_time:.2f} seconds")