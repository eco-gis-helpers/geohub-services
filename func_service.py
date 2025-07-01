
from qgis.utils import iface

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsVectorLayer,
    QgsDataSourceUri,
    QgsPointXY,
    
    
)



# For the following functions to work within a module, params from the QGIS env have to be passed in
class QgisContext:
    def __init__(self, iface, QgsProject, QgsCoordinateReferenceSystem, QgsPointXY, QgsCoordinateTransform, QgsDataSourceUri):
        self.iface = iface
        self.QgsProject = QgsProject
        self.QgsCoordinateReferenceSystem = QgsCoordinateReferenceSystem
        self.QgsPointXY = QgsPointXY
        self.QgsCoordinateTransform = QgsCoordinateTransform
        self.QgsDataSourceUri = QgsDataSourceUri
        self.QgsVectorLayer = QgsVectorLayer

# FM: I only managed to get this working by passing this context as a default arg, not working when context was created and passed in on the caller script. 
qcontext = QgisContext(
    iface=iface,
    QgsProject=QgsProject,
    QgsCoordinateReferenceSystem=QgsCoordinateReferenceSystem,
    QgsPointXY=QgsPointXY,
    QgsCoordinateTransform=QgsCoordinateTransform,
    QgsDataSourceUri=QgsDataSourceUri,
    QgsVectorLayer=QgsVectorLayer
)


# TODO split functions into sub-directories or multiple clearly named .py scripts, will be useful as more functions are used in this repo.

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



def bbox_for_service(service_wkid_string, qgis_context=qcontext):
# def bbox_for_service(service_wkid_string, 
#                      qgis_QgsProject=QgsProject, qgis_iface=iface, qgis_QgsCoordinateReferenceSystem=QgsCoordinateReferenceSystem, 
#                      qgis_QgsPointXY=QgsPointXY, qgis_QgsCoordinateTransform=QgsCoordinateTransform):
    """
    This function returns a bounding box in the CRS of the service, to be passed to the REST call.

    Parameters:
        service_wkid_string (str): A string representing the ESRI REST Service CRS wkid (number).
        qgis_context(QgisContext): The required QGIS globals available when the UI is running.

    Returns:
        str: A string representing the bounding box coordinates in the CRS of the service, formatted as "xmin,ymin,xmax,ymax".
    """
    mapCanvas = qgis_context.iface.mapCanvas()
    projCRS = mapCanvas.mapSettings().destinationCrs().authid()
    projInstance = qgis_context.QgsProject.instance()
    ext = mapCanvas.extent()

    # Get the map extent. Remember to zoom in to area of interest before running script
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()

    # Setup the transform
    sourceCrs = qgis_context.QgsCoordinateReferenceSystem(int(projCRS.split(':')[1])) #  Project CRS
    destCrs = qgis_context.QgsCoordinateReferenceSystem(int(service_wkid_string)) # Service CRS
    tform = qgis_context.QgsCoordinateTransform(sourceCrs, destCrs, projInstance)

    minPoint = tform.transform(qgis_context.QgsPointXY(xmin, ymin))
    maxPoint = tform.transform(qgis_context.QgsPointXY(xmax, ymax))

    return f"{minPoint.x()},{minPoint.y()},{maxPoint.x()},{maxPoint.y()}"

# define the REST API request by constructing the URL for each selected from the layer_list
def one_rest_request(url_string, service_wkid_string, treeLocation_to_add_layer, sql_string=None, qgis_context=qcontext):
    """
    Sends a REST request for one service URL and adds the resulting layer to the map canvas.

    Parameters:
        url_string (str): The REST URL string.
        service_wkid_string (str): The WKID (well-known ID) of the service's coordinate reference system (CRS) as a string.
        treeLocation_to_add_layer: The location in the layer tree where the layer should be added.
        sql_string (str, optional): The SQL query string to filter data. Default is None.
        qgis_context(QgisContext): The required QGIS globals available when the UI is running.


    Returns:
        None
    """

    projInstance = qgis_context.QgsProject.instance()
    uri = qgis_context.QgsDataSourceUri()

    #TODO does the service wkid need to be an int?
    #TODO what if the service wkid is not EPSG?
    uri.setParam('crs', f"EPSG:{service_wkid_string}")
    uri.setParam('bbox', bbox_for_service(service_wkid_string))
    uri.setParam('url', f'{url_string}')
    # TODO some sort of try/catch for this since it can easily cause a failure...
    # TODO ask user for the name? Or get from the url.json?
    if sql_string:
        uri.setSql(f'{sql_string}')
    layer = qgis_context.QgsVectorLayer(uri.uri(), 'Layer from service' , 'arcgisfeatureserver')

    if layer.isValid():
        # set_layer_style(layer)
        projInstance.addMapLayer(layer, False)
        treeLocation_to_add_layer.addLayer(layer)

    else:
        print(f"Invalid layer: failed to add layer")

[print("Loading layer...")]


