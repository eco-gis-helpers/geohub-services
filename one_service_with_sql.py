from func_service import *

print("Starting script...")

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
            one_rest_request(service_str, '4269', pyqgis_group, sql_str)
        else:
            one_rest_request(service_str, '4269', pyqgis_group)
        
run_dialog()

        
# TODO service CRS (wkid) is passed in manually here, the geohub_services.py script automates this, but it is a little clunky.
# TODO New function needed: that takes serv_sql_from_user_str appends the JSONslug (above) and parses the wkid for the service of interest...
# TODO how can we build out SingleTextInput to do these two inputs in one dialog?
    # complete?
# Lots of other ideas of how this idea could be built out to.

