print("Starting script...")


"""
TODO: Add GitHUb issue for feature that includes this logic (on the new plugin version), think cheat code that allows you to pull data for a broad geographic region
- E.g. after lyr selection dialogue, layers are listed with option to enter a filter string (with a useful example at the top)
- The example could be one that I like using, like the roads below, or: 
  - https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer/25 WITH "WATERBODY_TYPE"='Lake' OR "WATERBODY_TYPE"='River'


TODO how to move this comment to a branch since I'm likely on the MAIN

"""



treeRoot = QgsProject.instance().layerTreeRoot()
counter = 0
group_name = 'pyqgis' + str(counter)
while (treeRoot.findGroup(group_name)):
    counter += 1
    group_name = 'pyqgis' + str(counter)
pyqgis_group = treeRoot.insertGroup(0, group_name)

class SingleTextInput(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Geohub Service and SQL")
        layout = QVBoxLayout()

        # Service Input
        self.service_label = QLabel('Choose the Geohub service:')
        layout.addWidget(self.service_label)

        self.service_input = QLineEdit(self)
        self.service_input.setText('https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer/32')
        layout.addWidget(self.service_input)

        # SQL Input
        self.sql_label = QLabel('For this service, would you like to add an SQL query?\nIf you don\'t have one, clear input and click OK...')
        layout.addWidget(self.sql_label)

        # provide the example
        self.sql_input = QLineEdit(self)
        self.sql_input.setText('"STREET_TYPE_PREFIX" = \'Highway\' AND ("ROAD_CLASS"=\'Expressway / Highway\' OR "ROAD_CLASS"=\'Freeway\')')
        layout.addWidget(self.sql_input)

        # Ok and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def getInputs(self):
        """ Returns the user inputs for service and SQL query. """

        # if the user presses okay
        if self.exec_() == QDialog.Accepted:
            # get the service they entered
            service_str = self.service_input.text()
            # get the sql entered
            sql_str = self.sql_input.text()
            # return everything, along with True (meaning user pressed okay). False is returned when user presses Cancel.
            return service_str, sql_str, True
        else:
            return None, None, False

# Function to run the dialog box
def run_dialog():
    dialog = SingleTextInput()
    service_str, sql_str, ok = dialog.getInputs()

    # If user presses okay
    if ok:
        # Check if user provided an SQL query
        if sql_str:
            ## TODO The EPSG is hardcoded here at 4269??
            ## TO DO - what if no pyqgis group has been made yet?
            one_rest_request(service_str, '4269', pyqgis_group, sql_str)
        else:
            one_rest_request(service_str, '4269', pyqgis_group)
        

# FM I pasted this back in from a different script since I think this used to work...modular structure was working? I forget and don't see the imports. Pasted back in from func_service.py ##########

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

#########################################################################################################################################################



run_dialog()

        
# TODO service CRS (wkid) is passed in manually here, the geohub_services.py script automates this, but it is a little clunky.
# TODO New function needed: that takes serv_sql_from_user_str appends the JSONslug (above) and parses the wkid for the service of interest...
# TODO how can we build out SingleTextInput to do these two inputs in one dialog?
    # complete?
# Lots of other ideas of how this idea could be built out to.