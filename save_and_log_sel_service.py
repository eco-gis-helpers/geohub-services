import urllib.request
import json
import os
import glob
import datetime

# TODO
# Write explanation here and in a dialog box
# Explain that this only works for vector now, build out for raster/other?
# This only saves to .shp, build out for geopackage/other?
# Instead of the selected layer, add functionality to to this for all checked layers?

# Constants
mapCanvas = iface.mapCanvas()
parent = iface.mainWindow()
msgBar = iface.messageBar()
projInstance = QgsProject.instance()
projCRS = mapCanvas.mapSettings().destinationCrs().authid()
# TODO build out to work with proj CRSs not starting with EPSG
projCRSqgs = QgsCoordinateReferenceSystem(int(projCRS.strip('EPSG:')))
ext = mapCanvas.extent()

# TODO this assumes a very specific (and probably uncommon) project, layers, styles directory structure.
# Should be built out to take user input, maybe with this structure as one of the available defaults?
projGISroot = projInstance.readPath("../")
treeRoot = projInstance.layerTreeRoot()
basemap_dir = os.path.join(projGISroot, "Layers", "Basemap")
styles_dir = os.path.join(projGISroot, "Styles")


msgBar.pushMessage("Caution", "Read popup messages carefully to avoid QGIS timeout or crash.", level=Qgis.Warning, duration=10)

### FUNCTIONS ############################################################################################



def log_this_lyr_to_txt(l, path):
    """
    Function to write downloaded layers to a text file log
    """
    log_file = os.path.join(basemap_dir, '_data_sources_log.txt')
    now = datetime.datetime.now()
   

    print(l.source())
    log_string = f"\n------------------------------------- \n {now.strftime('%Y-%m-%d %H:%M')} \n Layer Acquired: \n {path} \n Acquired From: \n {l.source().split('url=')[-1]} \n -------------------------------------"
    if (os.path.isfile(log_file)):
            with open(log_file, "a") as log:
                # Writing data to a file
                log.write(log_string)
    else:
        # Create the file with heading and then append
        with open(log_file, "w") as log:
            # Writing data to a file
            log.writelines(["Data Sources Log \n", "---------------- \n", "Layers added from service using pyQGIS \n", "-------------------------------------\n"])
            log.write(log_string)

############################################################################################################

# give a warning up front where user can proceed or cancel if they aren't zoomed in:
sStr, bOK = QInputDialog.getText(parent, 'How this works', 'Save the selected vector service layer as a .shp in the basemap folder of your project', text='OK')
if (bOK):



    
    # Create a Basemap folder in 'Layers' if it doesn't exist
    # This is where shapefiles will be saved
    if not os.path.exists(basemap_dir):
        os.makedirs(basemap_dir)
    

    ### Save active layer (supposed to be vector layer from service) as local .shp

    act = iface.activeLayer()

    str_lyr_name = act.name()

    # Save style to project's style folder (if not already there)
    style_to_save =  os.path.join(styles_dir, f"{str_lyr_name}.qml")
    if (os.path.isfile(style_to_save)):
        print(f"Style {style_to_save} already exists and was not saved")
    else:
        if not os.path.exists(styles_dir):
            os.makedirs(styles_dir)
        act.saveNamedStyle(style_to_save)
    
# TODO this only saves to shapefile for now
    if isinstance(act, QgsVectorLayer):

        savePath = os.path.join(basemap_dir, f"{str_lyr_name}.shp")

        # Write the layer to local shapefile
        # check if it exists, if yes, it is not overwritten and user is told in the console
        if (os.path.isfile(savePath)):
            print(f"'{str_lyr_name}' already exists as a .shp, NOT overwriting this file")
        else:
            # Save a shapefile locally in the PROJECT CRS
            QgsVectorFileWriter.writeAsVectorFormat(act, savePath, "UTF-8", projCRSqgs, "ESRI Shapefile", onlySelected=False)
            print(f"'{str_lyr_name}' has been saved to Basemap folder")
            # Log where the local file came from
            log_this_lyr_to_txt(act, savePath)
    else:
        print('Error: Selected layer is not a QgsVectorLayer')


    ### Add the local shapefiles
    # if it doesn't exist make a group called 'basemap' in the layer panel
    if (treeRoot.findGroup("basemap")):
        basemap_group = treeRoot.findGroup("basemap")
    else:
        basemap_group = treeRoot.insertGroup(0, "basemap")
    # Load all shapefiles from the basemap directory (if they don't exist)
    in_basemap_gp = []
    for child in basemap_group.children():
        in_basemap_gp.append(child.name())

    for shp in glob.glob(basemap_dir+"/"+"*.shp" ):
        layer_name = os.path.split(shp)[-1].split('.')[0]
        
        if layer_name in in_basemap_gp:
            print(f"'{layer_name}' already exists in your basemap group")
        else:
            print("Adding:", layer_name)
            vlayer = QgsVectorLayer(shp, layer_name, "ogr")
            
            if not vlayer.isValid():
                print("Error: Layer Failed to Load!")
            else:
                projInstance.addMapLayer(vlayer, False)
                basemap_group.addLayer(vlayer)

    # Add style to each layer in the group, if the file exists
    for child in basemap_group.children():
        lyr_in_group = child.layer()
        str_lyr_name = child.name()
        style_to_load = os.path.join(styles_dir, f"{str_lyr_name}.qml")
        if (os.path.isfile(style_to_load)):
            print(f"Loading style: {style_to_load}")
            lyr_in_group.loadNamedStyle(style_to_load)
            lyr_in_group.triggerRepaint()
        else:
            print(f"No style file found for: {style_to_load}")
            
        






