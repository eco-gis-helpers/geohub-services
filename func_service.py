
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsDataSourceUri, QgsPointXY, QgsVectorLayer
from qgis.utils import iface


# For the following functions to work within a module, params from the QGIS env have to be passed in

# TODO split functions into sub-directories or multiple clearly named .py scripts, will be useful as more functions are used in this repo.
# Build this repo out like a package?

jsonSlug = '?f=pjson'
url_lio = f"https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer/"
json_lio1 = url_lio+jsonSlug

# initialize the map canvas, QGIS window, project, etc

def init_project():
    mapCanvas = iface.mapCanvas()
    parent = iface.mainWindow()
    projInstance = QgsProject.instance()
    projCRS = mapCanvas.mapSettings().destinationCrs().authid()
    ext = mapCanvas.extent()

init_project()


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


