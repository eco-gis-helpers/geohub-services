import urllib.request
import json
import os
import glob
import datetime






# Explain that this only works for vector now, build out for raster/other?
    # Maybe a seperate script for raster. I dont use raster layers in QGIS much. I like GEE for raster analysis.

# This only saves to .shp, build out for geopackage/other?
    # Would make sense for an additional dialog box to ask user which file type? Could be added to READ ME dialog.
    # Also worth considering there are great QGIS native tools for this like 'Package Layers' in particular for geopackage

# Instead of the selected layer, add functionality to to this for all checked layers?
    # complete


############################################

def get_web_service_layers():
    """
    Returns a list of names of all layers in the current QGIS project that come from an arcgisfeatureserver
    
    """
    web_service_layers = []
    
    for layer in QgsProject.instance().mapLayers().values():
        # Check if the layer's data provider is from esri rest service
        data_provider = layer.dataProvider().name().lower()
        if data_provider in ['arcgisfeatureserver']:
            web_service_layers.append(layer.name())
    
    return web_service_layers
# get a list of all the layers in the project
# project_layers = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
project_layers = get_web_service_layers()

# Constants
mapCanvas = iface.mapCanvas()
parent = iface.mainWindow()
msgBar = iface.messageBar()
projInstance = QgsProject.instance()
projCRS = mapCanvas.mapSettings().destinationCrs().authid()
# TODO build out to work with proj CRSs not starting with EPSG
projCRSqgs = QgsCoordinateReferenceSystem(int(projCRS.strip('EPSG:')))
ext = mapCanvas.extent()

# TODO consider this requires the user to have their QGIS project saved... but what happens if it's just a temporary 'Untitled' project that someone is working in?

projGISroot = projInstance.readPath("./")
treeRoot = projInstance.layerTreeRoot()
basemap_dir = os.path.join(projGISroot, "Layers", "Basemap")
styles_dir = os.path.join(projGISroot, "Styles")


msgBar.pushMessage("Caution", "Read popup messages carefully to avoid QGIS timeout or crash.", level=Qgis.Warning, duration=10)


## Make warning Dialog
class WarningDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Save and Log - READ ME")

        layout = QVBoxLayout()

        save_label = QLabel("Please ensure you have saved your QGIS project")
        warning_label = QLabel("In the next window you will be asked to select the vectors layers to save and log")
        warning1_label = QLabel("The selected layers will be saved as .shp in the project directory < Basemaps < Layers")
        warning2_label = QLabel("A Style .qml file will be saved in the project directory < Styles")
        warning3_label = QLabel("A .txt log file will be created")
        warning4_label = QLabel("Note: this will not work on Raster layers")
        warning5_label = QLabel("Note: saving several large layers may be slow and risks crashing QGIS")
        warning6_label = QLabel("Press 'Ok' to continue or 'Cancel' to stop the script")

        layout.addWidget(save_label)
        layout.addWidget(warning_label)
        layout.addWidget(warning1_label)
        layout.addWidget(warning2_label)
        layout.addWidget(warning3_label)
        layout.addWidget(warning4_label)
        layout.addWidget(warning5_label)
        layout.addWidget(warning6_label)


        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)


## Layer Selection Dialog
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
            checkbox = QCheckBox(layer)
            checkbox.setChecked(True)  # By default, no layers are selected
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
        for checkbox, layer in zip(self.checkboxes, project_layers):
            if checkbox.isChecked():
                selected.append(layer)
        return selected
    

    def log_lyr_to_txt(self, l, path):
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
    
    def save_and_log_layers(self, selected):

        if not os.path.exists(basemap_dir):
            
            os.makedirs(basemap_dir)

        for layer_name in selected:
            # Find the layer by name
            act = QgsProject.instance().mapLayersByName(layer_name)
            
            if act:
                act = act[0]  # First matching layer
            else:
                print(f"Layer '{layer_name}' not found.")
                continue

            # Save style to project's style folder (if not already there)
            style_to_save = os.path.join(styles_dir, f"{layer_name}.qml")
            if os.path.isfile(style_to_save):
                print(f"Style {style_to_save} already exists and was not saved")
            else:
                if not os.path.exists(styles_dir):
                    os.makedirs(styles_dir)
                act.saveNamedStyle(style_to_save)

            # TODO this only saves to shapefile for now
            ## If we want more file type options we could make buttons, and on click, run a if/else function to return the correct file writer

            if isinstance(act, QgsVectorLayer):
                savePath = os.path.join(basemap_dir, f"{layer_name}.shp")

                # Write the layer to local shapefile
                # check if it exists, if yes, it is not overwritten and user is told in the console
                if os.path.isfile(savePath):
                    print(f"'{layer_name}' already exists as a .shp, NOT overwriting this file")
                else:
                    # Save a shapefile locally in the PROJECT CRS
                    QgsVectorFileWriter.writeAsVectorFormat(act, savePath, "UTF-8", projCRSqgs, "ESRI Shapefile", onlySelected=False)
                    print(f"'{layer_name}' has been saved to Basemap folder")
                    # Log where the local file came from
                    self.log_lyr_to_txt(act, savePath)
            else:
                print(f'Error: Layer "{layer_name}" is not a QgsVectorLayer')


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
        
        # loads in all shapefiles in the layers directory.. maybe it should just load in the selected files instead?
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

# call the warning dialog class
warn_dialog = WarningDialog()

# call the layer selection dialog class and pass it the list of the project layers
dialog = LayerSelectionDialog(project_layers)


# Dialog box logic

if warn_dialog.exec_() == QDialog.Accepted:
    print("Warning Dialog Box accepted. Selecting layers to save and log...")
    if dialog.exec_() == QDialog.Accepted:
        # Define the selected layers by running the selected_layers function
        selected_layers = dialog.selected_layers()
        # save the selected layers by running the save_and_log_layers function
        dialog.save_and_log_layers(selected_layers)
        print("Script complete")
    else:
        print("User clicked Cancel. Stopping script.")
else:
    print("User clicked Cancel. Stopping script.")


