from func_service import one_rest_request


print("Starting script...")

### Constants
# TODO is it worth having a function that does this to keep it consistent in every script?
mapCanvas = iface.mapCanvas()
parent = iface.mainWindow()
projInstance = QgsProject.instance()
projCRS = mapCanvas.mapSettings().destinationCrs().authid()
ext = mapCanvas.extent()


# TODO see TODOs below..
jsonSlug = '?f=pjson'
url_lio = f"https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer/"
json_lio1 = url_lio+jsonSlug


# TODO refactor as a function in a module
## Add an incrementing pyqgis group each time the script is run
treeRoot = projInstance.layerTreeRoot()
counter = 0
group_name = 'pyqgis' + str(counter)
while (treeRoot.findGroup(group_name)):
    counter += 1
    group_name = 'pyqgis' + str(counter)
pyqgis_group = treeRoot.insertGroup(0, group_name)


class SingleTextInput(QInputDialog):
    def __init__(self):
        super().__init__()

        # Subclass not yet customized...

        
# TODO service CRS (wkid) is passed in manually here, the geohub_services.py script automates this, but it is a little clunky.
# TODO New function needed: that takes serv_sql_from_user_str appends the JSONslug (above) and parses the wkid for the service of interest...
# TODO Aidan with you Qt Dialog wizardry, how would you build out SingleTextInput to do these two inputs in one dialog?
# Lots of other ideas of how this idea could be built out to.

service_from_user_str, service_from_user_bOK= SingleTextInput().getText(parent, 'Choose Service', 'Choose the Geohub service...', text='https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer/32')

if service_from_user_bOK:
    
    serv_sql_from_user_str, serv_sql_from_user_bOK= SingleTextInput().getText(parent, 'SQL query?', 'For this service, would you like to add an SGL query? \nIf you dont have one, clear input and click OK... ', text='"STREET_TYPE_PREFIX" = \'Highway\' AND ("ROAD_CLASS"=\'Expressway / Highway\' OR "ROAD_CLASS"=\'Freeway\')')

    if serv_sql_from_user_bOK:

        #TODO I'm passing in the service wkid manully for now...

        if serv_sql_from_user_str:
            one_rest_request(service_from_user_str, '4269', pyqgis_group, serv_sql_from_user_str)
        else:
            one_rest_request(service_from_user_str, '4269', pyqgis_group)



