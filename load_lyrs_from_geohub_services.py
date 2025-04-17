import urllib.request
import json
import time
from styles import layer_styles
from lio_list import lio_list

# # Start Timer
# start_time = time.time() 

QgsMessageLog.logMessage("Starting script...", "Geohub-Services", level=Qgis.Info)
print("Starting script...")

### Constants
mapCanvas = iface.mapCanvas()
parent = iface.mainWindow()
projInstance = QgsProject.instance()
projCRS = mapCanvas.mapSettings().destinationCrs().authid()
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


# ---------- Network connection test -------

def internet_on():
    try:
        urllib.request.urlopen('https://geohub.lio.gov.on.ca/', timeout=1)  # Open URL
        return True
    except urllib.error.URLError as err:  # Handle errors
        return False

# ----------- API Progress Bar -----------
def create_progress_dialog(total_estimate):
    progress = QProgressDialog("Fetching data from the Ontario Geohub...", "Cancel", 0, total_estimate)
    progress.setMinimumWidth(500)
    progress.setWindowModality(Qt.WindowModal)  # Modal window so user cannot interact with the map while loading
    progress.setMinimumDuration(0)  # Show dialog immediately
    progress.setValue(0)
    return progress

# ----------- Clipping Progress Bar --------

def clipping_progress_dialog(total_estimate):
    progress = QProgressDialog("Clipping features...", "Cancel", 0, total_estimate)
    progress.setMinimumWidth(500)
    progress.setWindowModality(Qt.WindowModal)  # Modal window so user cannot interact with the map while loading
    progress.setMinimumDuration(0)  # Show dialog immediately
    progress.setValue(0)
    return progress

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
        iface.messageBar().pushMessage("Style Error", f"Layer '{layer_name}' not in style sheet", level=Qgis.Info)
        QgsMessageLog.logMessage("Layer not in style sheet", "Geohub-Services", level=Qgis.Info)
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

def layer_bbox_for_service(service_crs, selected_polygon_layer):
    """
    Returns a list of bounding boxes from the active layer's feature geometries,
    ensuring they are in EPSG:4269
    params: crs_string: A string representing the ESRI REST Service CRS
    """
    bbox_list = []
    tform = None

    destCrs = QgsCoordinateReferenceSystem(int(service_crs))
    # Get the CRS of the selected polygon layer
    activeCrs = selected_polygon_layer.crs()

    # if the selected polygon layers crs doesnt match the ESRI REST Service CRS, make a transformation
    if activeCrs.authid() != f"EPSG:{service_crs}":
        QgsMessageLog.logMessage("Transformation needed...", "Geohub-Services", level=Qgis.Info)
        print("Tranformation needed...")
        tform = QgsCoordinateTransform(activeCrs, destCrs, QgsProject.instance())

    # reproject each feature
    for feature in selected_polygon_layer.getFeatures():
        geometry = feature.geometry()

        # Reproject if necessary
        if tform:
            geometry.transform(tform)

        # Get bounding box in ESRI REST Service CRS
        bbox = geometry.boundingBox()
        bbox_list.append(bbox)

    return bbox_list
        
# define the REST API request by constructing the URL for each selected from the layer_list
def rest_request(layer_list, str_bbox):
    """
    Sends REST requests for each layer in the given list.
    :param layer_list: A list of layer ids and names.
    """
    for l in layer_list:
        user_cancelled = False

        #Use this if you want to filter by more than bounding box
        #https://gis.stackexchange.com/questions/456167/pyqgis-add-arcgis-feature-service-layer-to-qgis-including-a-query
        uri = QgsDataSourceUri()
        # TODO 'EPSG' handcoded here makes this function less generalizable than it could be
        uri.setParam('crs', f"EPSG:{service_crs}")
        uri.setParam('bbox', str_bbox)
        uri.setParam('url', f"https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open{l[2]}/MapServer/{l[0]}")
        layer = QgsVectorLayer(uri.uri(), f"{l[1]}" , 'arcgisfeatureserver')

        if layer.isValid() and layer.featureCount() > 0:

            # count how many features are added to the map
            total_estimate = layer.featureCount()
            added_records = 0
            
            progress = create_progress_dialog(total_estimate)
            progress.setWindowTitle(f"Fetching data for {layer.name()} layer...")
            progress.show()

            for i, feature in enumerate(layer.getFeatures()):
                if progress.wasCanceled():
                    QgsMessageLog.logMessage(f"Cancelled loading for {l[1]}", "Geohub-Services", level=Qgis.Info)
                    print(f"User cancelled loading for {l[1]}")
                    treeRoot.removeChildNode(pyqgis_group)
                    user_cancelled = True
                    return user_cancelled

                added_records += 1
                progress.setValue(added_records)
                progress.setLabelText(f"Fetching {layer.name()} data for canvas... {added_records} / {total_estimate}")
                QApplication.processEvents()
            
            progress.setValue(total_estimate)

            if user_cancelled:
                break
                
            set_layer_style(layer)
            projInstance.addMapLayer(layer, False)
            pyqgis_group.addLayer(layer)

            iface.messageBar().pushMessage("Features added", f"{total_estimate} feature(s) within {layer.name()} were added to the map.", level=Qgis.Info)
            QgsMessageLog.logMessage(f"{total_estimate} feature(s) within {layer.name()} were added to the map.", "Geohub-Services", level=Qgis.Info)
            print(f"{total_estimate} feature(s) within {layer.name()} were added to the map.")


        elif layer.isValid() and layer.featureCount() == 0:
            iface.messageBar().pushMessage("No features", f"No features exist: skipped layer {l}", level=Qgis.Info)
            QgsMessageLog.logMessage(f"No features exist: skipped layer {l}", "Geohub-Services", level=Qgis.Info)
            print(f"No features exist: skipped layer {l}")

        else:
            iface.messageBar().pushMessage("Invalid layer", f"Invalid layer: failed to add layer {l}", level=Qgis.Info)
            QgsMessageLog.logMessage(f"Invalid layer: failed to add layer {l}", "Geohub-Services", level=Qgis.Info)
            print(f"Invalid layer: failed to add layer {l}")

    for x in layer_list:
        QgsMessageLog.logMessage(f"Loading", x[1], "layer...", "Geohub-Services", level=Qgis.Info)
        print("Loading", x[1], "layer...")

# function for when the user queries by a selected layer
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
        user_cancelled = False
        layer_num = 0
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

                total_estimate = layer.featureCount()
                added_records = 0
                
                progress = create_progress_dialog(total_estimate)
                progress.setWindowTitle(f"Fetching data for {layer.name()} layer...")
                progress.show()

                # Check for invalid geometries
                for i, feature in enumerate(layer.getFeatures()):
                    if progress.wasCanceled():

                        treeRoot.removeChildNode(pyqgis_group)
                        QgsMessageLog.logMessage(f"User canceled loading for {l[1]}", "Geohub-Services", level=Qgis.Info)
                        print(f"User canceled loading for {l[1]}")
                        return None, None
                    
                    geometry = feature.geometry()

                    if not geometry.isGeosValid():
                        invalid_flag = True
                        
                        iface.messageBar().pushMessage("Invalid geometry", f"Invalid geometry found in feature {feature.id()} in layer {l[1]}.", level=Qgis.Info)
                        QgsMessageLog.logMessage(f"Invalid geometry found in feature {feature.id()} in layer {l[1]}.", "Geohub-Services", level=Qgis.Info)
                        print(f"Invalid geometry found in feature {feature.id()} in layer {l[1]}.")
                    
                    added_records += 1
                    progress.setValue(added_records)
                    progress.setLabelText(f"Fetching data for feature {layer_num} in {layer.name()} layer... {added_records} / {total_estimate}")
                    QApplication.processEvents()
                
                progress.setValue(total_estimate)

                
                loaded_layer_list.append(layer)

            elif layer.isValid() and layer.featureCount() == 0:
                
                iface.messageBar().pushMessage("No features", f"No features exist: skipped layer {l}", level=Qgis.Info)
                QgsMessageLog.logMessage(f"No features exist: skipped layer {l}", "Geohub-Services", level=Qgis.Info)
                print(f"No features exist: skipped layer {l}")
                loaded_layer_list.append(layer)

            else:
                iface.messageBar().pushMessage("Invalid layer", f"Invalid layer: failed to add layer {l}", level=Qgis.Info)
                QgsMessageLog.logMessage(f"Invalid layer: failed to add layer {l}", "Geohub-Services", level=Qgis.Info)
                print(f"Invalid layer: failed to add layer {l}")
                loaded_layer_list.append(layer)

            layer_num += 1

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
    # the loaded_layer_list will have [selected_layers multiplied by the number of features] items.
    # whereas the overlay_list will only have [number of features] items, so we use the modulo operator to match their lengths
    overlay_layer_list = [overlay_layer_list[i % len(overlay_layer_list)] for i in range(len(loaded_layer_list))]
    layer_id_list = [layer_id_list[i % len(layer_id_list)] for i in range(len(loaded_layer_list))]

    for loaded_layer, overlay_layer, layer_id in zip(loaded_layer_list, overlay_layer_list, layer_id_list):

        if invalid_flag:
            QgsMessageLog.logMessage("Fixing geometries...", "Geohub-Services", level=Qgis.Info)
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

            iface.messageBar().pushMessage("Layers added", f"{feature_count} feature(s) within {layer_name} were added to the map.", level=Qgis.Info)
            QgsMessageLog.logMessage(f"{feature_count} feature(s) within {layer_name} were added to the map.", "Geohub-Services", level=Qgis.Info)
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

# Make the layer selection dropdown dialog
class PolygonDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Select Layer for Query")
        self.setMinimumWidth(500)
        self.setMinimumHeight(100)

        self.map_layer_combo_box = QgsMapLayerComboBox()
        self.map_layer_combo_box.setCurrentIndex(-1)
        self.map_layer_combo_box.setFilters(QgsMapLayerProxyModel.PolygonLayer)

        layout = QFormLayout()
        layout.addWidget(self.map_layer_combo_box)
        self.setLayout(layout)
        self.show() 

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        selected_layer = self.map_layer_combo_box.currentLayer()
        if selected_layer:
            self.accept()
        else:
            iface.messageBar().pushMessage("Error", "No layer selected!", level=Qgis.Critical)
            QgsMessageLog.logMessage("No layer selected", "Geohub-Services", level=Qgis.Critical)
            print("No layer selected!")
            raise ValueError("No layer selected!")

    def get_selected_layer(self):
        layer = self.map_layer_combo_box.currentLayer()
        if layer:
            return layer, layer.name()
        return None, None


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
if internet_on():
    with urllib.request.urlopen(json_lio1) as url:
        data = json.loads(url.read().decode())


service_crs = str(data['spatialReference']['latestWkid'])

# make the warning dialog string and pass it to the class above
warn_str = (
    "Please note:\n\n"
    "- When querying by canvas, ensure you are sufficiently zoomed in to avoid performance issues \n"
    "- When querying by selected layer, avoid using an excessive number of features or very large polygons \n\n"
    "Otherwise, QGIS may become unresponsive or crash."
)

warn_dialog = WarningDialog(warn_str)

# pass the lio list to the layer selection dialog class made above
dialog = LayerSelectionDialog(lio_list)

## Wrap the main dialog window in the warning dialog window and communicate to the user based on the selections
## the main dialog passes the selected layers from the checkboxes into the rest_request function above which actually hits the API to load the selected layers


def main():
    if internet_on():
        if warn_dialog.exec_() == QDialog.Accepted:
            QgsMessageLog.logMessage("Zoom warning accepted. Selecting layers of interest", "Geohub-Services", level=Qgis.Info)
            print("Zoom warning accepted. Selecting layers of interest")
            if dialog.exec_() == QDialog.Accepted:
                selected_layers = dialog.selected_layers()
                
                # make a list to hold the temporary layers
                temp_layers = []
                if dialog.get_bbox_function() == "layer_bbox_for_service":
                    QgsMessageLog.logMessage("Querying by selected layer", "Geohub-Services", level=Qgis.Info)
                    print("Querying by selected layer")

                    polygon_dialog = PolygonDialog()

                    if polygon_dialog.exec_() == QDialog.Accepted:
                        selected_polygon_layer, layer_name = polygon_dialog.get_selected_layer()
                        QgsMessageLog.logMessage(f"User selected polygon layer: {layer_name}", "Geohub-Services", level=Qgis.Info)
                        print(f"User selected polygon layer: {layer_name}")

                        # if no selected layer, raise a value error and notify the user
                        if not selected_polygon_layer:
                            treeRoot.removeChildNode(pyqgis_group)
                            iface.messageBar().pushMessage("Error", "No layer selected!", level=Qgis.Critical)
                            QgsMessageLog.logMessage("No layer selected!", "Geohub-Services", level=Qgis.Critical)
                            print("No layer selected!")
                            return

                        # If the selected layer is a raster, throw an error
                        # this shouldnt ever be possible with the new layer selection filter, but just in case
                        elif selected_polygon_layer.type() == QgsMapLayer.RasterLayer:
                            treeRoot.removeChildNode(pyqgis_group)
                            iface.messageBar().pushMessage("Error", "Selected layer is a raster!", level=Qgis.Critical)
                            QgsMessageLog.logMessage("The selected layer is a raster!", "Geohub-Services", level=Qgis.Critical)
                            print("The selected layer is a raster!")
                            return

                        # If the selected layer is a multi-polygon or polygon, keep going!
                        elif QgsWkbTypes.displayString(selected_polygon_layer.wkbType()) in ["MultiPolygon", "Polygon"]:
                            pass

                        # If the selected layer is not a Polygon or MultiPolygon, throw an error
                        # again, this shouldnt even be possible with the new layer selection filter, but just in case
                        else:
                            treeRoot.removeChildNode(pyqgis_group)
                            iface.messageBar().pushMessage("Error", "Selected layer is not a polygon!", level=Qgis.Critical)
                            QgsMessageLog.logMessage("The selected layer needs to be a polygon!", "Geohub-Services", level=Qgis.Critical)
                            print("The selected layer needs to be a polygon!")
                            return
                            
                        # get a list of the bboxes for each of the selected layers geometries
                        bbox_list = layer_bbox_for_service(service_crs, selected_polygon_layer)

                        layer_id_list = []
                        overlay_layer_list = []

                        for feature in selected_polygon_layer.getFeatures():
                            layer_id = feature.id()
                            layer_id_list.append(layer_id)
                            geometry = feature.geometry()

                            # make temp layers of each feature in the active layer for the clipping function
                            temp_layer_name = f"temp_clip_{layer_id}"
                            # load the temp layers in memory
                            temp_layer = QgsVectorLayer("Polygon?crs=" + selected_polygon_layer.crs().authid(), temp_layer_name, "memory")
                            temp_layer_provider = temp_layer.dataProvider()

                            # # Add the feature geometry to the temporary layer
                            temp_feature = QgsFeature()
                            temp_feature.setGeometry(geometry)
                            temp_layer_provider.addFeature(temp_feature)
                            temp_layer.updateExtents()

                            # Add the temporary layer to the project (for visibility in processing)
                            # TODO - do we need to show these temporary layers in the layers pane?
                            QgsProject.instance().addMapLayer(temp_layer)
                            temp_layers.append(temp_layer)
                            # Now that the layer is in the project, use it in the processing tool as the overlay for clipping
                            overlay_source = QgsProcessingFeatureSourceDefinition(temp_layer.id(), selectedFeaturesOnly=False)

                            overlay_layer_list.append(overlay_source)

                        # query the API using the bboxes from each geometry
                        loaded_layer_list, invalid_flag = layer_rest_request(bbox_list, selected_layers)

                        if loaded_layer_list is None and invalid_flag is None:
                            QgsMessageLog.logMessage("Script was cancelled", "Geohub-Services", level=Qgis.Info)
                            print("Script was cancelled by user.")
                            # Clean up temp layers even if cancelled
                            for temp_layer in temp_layers:
                                QgsProject.instance().removeMapLayer(temp_layer)
                            return
                            
                        clipping(loaded_layer_list, overlay_layer_list, layer_id_list, invalid_flag)

                        # Remove the temporary layers after processing
                        for temp_layer in temp_layers:
                            QgsProject.instance().removeMapLayer(temp_layer)

                    else:
                        treeRoot.removeChildNode(pyqgis_group)
                        QgsMessageLog.logMessage("Cancelled polygon selection", "Geohub-Services", level=Qgis.Info)
                        print("User cancelled polygon selection")
                        return

                # otherwise the user selected the canvas bbox for query
                elif dialog.get_bbox_function() == "canvas_bbox_for_service":
                    QgsMessageLog.logMessage("Querying by Canvas", "Geohub-Services", level=Qgis.Info)
                    print("Querying by Canvas")
                    # get the canvas bbox and query the api
                    str_bbox = canvas_bbox_for_service(service_crs)
                    rest_request(selected_layers, str_bbox)

            else:
                treeRoot.removeChildNode(pyqgis_group)
                QgsMessageLog.logMessage("Script cancelled", "Geohub-Services", level=Qgis.Info)
                print("User clicked Cancel. Stopping script.")
        else:
            treeRoot.removeChildNode(pyqgis_group)
            QgsMessageLog.logMessage("Script cancelled", "Geohub-Services", level=Qgis.Info)
            print("User clicked Cancel. Stopping script.")

        # # End Timer
        # end_time = time.time() 
        # elapsed_time = end_time - start_time
        # print(f"Script execution time: {elapsed_time:.2f} seconds")
    else:
        treeRoot.removeChildNode(pyqgis_group)
        iface.messageBar().pushMessage("Error", "Cannot establish connection to the network", level=Qgis.Critical)
        QgsMessageLog.logMessage("Cannot establish connection to the network", "Geohub-Services", level=Qgis.Critical)
        print("Cannot establish connection to the network. Please check your internet and try again.")

main()