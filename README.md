# geohub-services
A pyqgis script to import layers from Ontario Geohub LIO

The core script is load_lyrs_from_geohub_services.py

Ensure you are using a WGS projection in your QGIS project.

Load this script into your QGIS Python Console and click "Run"
<img width="1020" alt="geohub-services-step1" src="https://github.com/user-attachments/assets/dfddbdfa-5677-4cc3-bf76-daf51fb271e1" />

You will see a warning dialog "Please make sure you are zoomed in sufficiently!... Otherwise QGIS may crash"

You can choose to use your canvas extent as the bounding box for the API Query, so if you arent zoomed in sufficiently, you will be querying a massive amount of data from the API and potentially crash QGIS.

After clicking through the warning dialog, you will see a Layer Selection dialog. Here you can choose which Ontario Geohub data layers you would like to pull in to your map. The list of data layers is stored in lio_list.py. You can choose if you would like to use your canvas as the bounding box for the query, or if you would like to use a selected layer as the bounding box. Choosing "Selected Layer as bbox" will use the bounding box of your active layer in the Layer Pane. In the example below, the "Selected Layer as bbox" is selected and the "test1" layer is the active layer, so it will use this polygon as the bbox for the query. The script will throw an error if "Selected layer as bbox" is selected and there is no active layer selected, or your active layer is not a polygon.

Press "Ok" to run the query and load in your selected Ontario Geohub data layers.

The results are automatically styled using the styles.py (a style dictionary)

<img width="1435" alt="geohub-services-step2" src="https://github.com/user-attachments/assets/d2207040-9a84-4eb5-8e71-d76df5b4cd42" />



