import os
import pandas as pd
import uuid
import traceback
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, QWidget, QVBoxLayout, QLabel, QComboBox, QMessageBox, 
    QLineEdit, QTextEdit, QDateEdit, QRadioButton, QCheckBox, QPushButton
)
from PyQt6.QtCore import Qt, QDate 

# Define the matricule column name globally for consistency across the application.
# This MUST match the exact column header you expect in your CSV files (e.g., 'UserMatricule' from your screenshot).
USER_MATRICULE_COLUMN_NAME = 'UserMatricule' 

class MainUserWindow(QMainWindow):
    def __init__(self, user_matricule, parent=None):
        super().__init__(parent)
        self.user_matricule = user_matricule # This matricule is passed from the login system
        self.requests_window = None # Initialize this here for managing the requests view window
        self.current_form_widget = None # To keep track of the currently loaded form

        try:
            # Define base and UI directories
            self.BASE_DIR = r"C:\Users\sl3ag\Desktop\polina"
            self.UI_DIR = os.path.join(self.BASE_DIR, "ui")
            MAIN_UI_PATH = os.path.join(self.UI_DIR, "user.ui") 
            
            # Load the main user UI file
            if not os.path.exists(MAIN_UI_PATH):
                QMessageBox.critical(self, "UI Error", f"Main user UI file not found: {MAIN_UI_PATH}")
                self.close()
                return

            uic.loadUi(MAIN_UI_PATH, self)
            
            # Set window title with user info
            self.setWindowTitle(f"Main Application - User: {self.user_matricule}")
            
            # Define form mappings (UI filename, submit button name, and expected fields)
            self.form_definitions = {
                "Fiche demande de grauve": {
                    'filename': 'grauve.ui',
                    'submit_button_name': 'gravure_submit_pushButton',
                    'fields': {
                        'gravure_date_dateEdit': QDateEdit,
                        'gravure_numFicheCD_lineEdit': QLineEdit,
                        'gravure_demandeGravure_lineEdit': QLineEdit,
                        'gravure_unite_lineEdit': QLineEdit,
                        'gravure_cdrom_checkBox': QCheckBox,
                        'gravure_dvdrom_checkBox': QCheckBox,
                        'gravure_logiciel1_num_lineEdit': QLineEdit,
                        'gravure_logiciel2_num_lineEdit': QLineEdit,
                        'gravure_logiciel3_num_lineEdit': QLineEdit,
                        'gravure_logiciel4_num_lineEdit': QLineEdit,
                        'gravure_logiciel5_num_lineEdit': QLineEdit,
                        'gravure_total_lineEdit': QLineEdit,
                        'gravure_motif_textEdit': QTextEdit,
                    }
                },
                "Fiche d'engagement clé 3g": { 
                    'filename': 'cle3g.ui',
                    'submit_button_name': 'cle3g_submit_pushButton',
                    'fields': {
                        'cle3g_filiale_lineEdit': QLineEdit,
                        'cle3g_date_dateEdit': QDateEdit,
                        'cle3g_renouvellement_radio': QRadioButton,
                        'cle3g_nouvelleDemande_radio': QRadioButton,
                        'cle3g_nomPrenom_lineEdit': QLineEdit,
                        'cle3g_service_lineEdit': QLineEdit,
                        'cle3g_anciennete_lineEdit': QLineEdit,
                        'cle3g_motif_textEdit': QTextEdit,
                    }
                },
                "Fiche d'engagement d'accés internet": { 
                    'filename': 'internet.ui',
                    'submit_button_name': 'internet_submit_pushButton',
                    'fields': {
                        'internet_filiale_lineEdit': QLineEdit,
                        'internet_date_dateEdit': QDateEdit,
                        'internet_renouvellement_radio': QRadioButton,
                        'internet_nouvelleDemande_radio': QRadioButton,
                        'internet_nomPrenom_lineEdit': QLineEdit,
                        'internet_service_lineEdit': QLineEdit,
                        'internet_anciennete_lineEdit': QLineEdit,
                        'internet_motif_textEdit': QTextEdit,
                    }
                },
                "Demande d'octroi d'un accés a distance": { 
                    'filename': 'fishe.ui',
                    'submit_button_name': 'accessDistance_submit_pushButton',
                    'fields': {
                        'accessDistance_filiale_lineEdit': QLineEdit,
                        'accessDistance_date_dateEdit': QDateEdit,
                        'accessDistance_nomPrenom_lineEdit': QLineEdit,
                        'accessDistance_service_lineEdit': QLineEdit,
                        'accessDistance_periodeTemp_radio': QRadioButton,
                        'accessDistance_periodePerm_radio': QRadioButton,
                        'accessDistance_typeAccesTotal_radio': QRadioButton,
                        'accessDistance_typeAccesPersonalise_radio': QRadioButton,
                        'accessDistance_besoin_textEdit': QTextEdit,
                        'accessDistance_appSysteme_textEdit': QTextEdit,
                        'accessDistance_cleSecurite_token_lineEdit': QLineEdit,
                        'accessDistance_cleSecurite_periodeSouhaitee_dateEdit': QDateEdit,
                        'accessDistance_cleSecurite_deviceMobile_lineEdit': QLineEdit,
                        'accessDistance_cleSecurite_du_dateEdit': QDateEdit,
                    }
                },
                "Engagement pour déverrouillage d'un lecteru disc": { 
                    'filename': 'externaldrive.ui',
                    'submit_button_name': 'externalDrive_submit_pushButton',
                    'fields': {
                        'externalDrive_filiale_lineEdit': QLineEdit,
                        'externalDrive_service_lineEdit': QLineEdit,
                        'externalDrive_lecture_radio': QRadioButton,
                        'externalDrive_lectureEcriture_radio': QRadioButton,
                        'externalDrive_flashDisque_radio': QRadioButton,
                        'externalDrive_lecteurCDDVD_radio': QRadioButton,
                        'externalDrive_graveurCDDVD_radio': QRadioButton,
                        'externalDrive_cle3g_radio': QRadioButton,
                        'externalDrive_engagement1_checkBox': QCheckBox,
                        'externalDrive_engagement2_checkBox': QCheckBox,
                        'externalDrive_engagement3_checkBox': QCheckBox,
                    }
                }
            }
            
            # Find and setup common widgets (combo box, form container, status label)
            self.setup_widgets()
            
            # Initial status message
            self.show_status(f"Welcome, user {self.user_matricule}!")
            
        except Exception as e:
            error_msg = f"Main window initialization error:\n{str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Fatal Error", error_msg)
            print(error_msg)
            self.close()

    def show_my_requests_window(self):
        """Displays the UserRequestsView in a new, separate window."""
        # Local import to avoid potential circular dependencies
        from user_requests_manager import UserRequestsView 
        try:
            # If the window exists and is visible, bring it to front and refresh
            if self.requests_window and self.requests_window.isVisible():
                self.requests_window.activateWindow()
                self.requests_window.raise_()
                self.requests_window.load_user_requests() # Reload data to show latest changes
                print("My Requests window already open, bringing to front and refreshing.")
                return

            # Create a new instance of the UserRequestsView (top-level window)
            self.requests_window = UserRequestsView(self.user_matricule, self.BASE_DIR, parent=None)
            self.requests_window.show() 
            self.show_status("Opened 'My Submitted Requests' window.", is_error=False)
        except Exception as e:
            error_msg = f"Error opening 'My Submitted Requests' window: {str(e)}\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Error", error_msg)
            print(error_msg)
    
    def setup_widgets(self):
        """Finds and sets up the main UI widgets and connects signals."""
        try:
            # Find the QComboBox for form selection - revert to more direct lookup first
            self.combo_accessType = self.findChild(QComboBox, "formType_comboBox")
            if not self.combo_accessType:
                # If "formType_comboBox" is not found, try a more generic lookup for QComboBox
                combos = self.findChildren(QComboBox)
                if combos:
                    self.combo_accessType = combos[0]
                    print(f"Warning: 'formType_comboBox' not found. Using first available QComboBox: {self.combo_accessType.objectName()}")
                else:
                    raise RuntimeError("No QComboBox widget found in user.ui! Cannot load forms.")
            
            print(f"Found combo box: {self.combo_accessType.objectName()}")
            
            # Populate the combo box with form names from form_definitions
            self.combo_accessType.clear()
            for form_name in self.form_definitions.keys():
                self.combo_accessType.addItem(form_name)
            print("✓ Populated combo box from form definitions")

            # Find the QWidget that will act as a container for dynamic forms
            self.form_container = self.findChild(QWidget, "form_container")
            if not self.form_container:
                # Fallback: find any QWidget that might serve as a container
                widgets = self.findChildren(QWidget)
                # Filter out standard QMainWindow components
                candidate_containers = [w for w in widgets if w.objectName() not in 
                                        ['centralwidget', 'menubar', 'statusbar', 'toolBar'] and
                                        isinstance(w.layout(), type(None))] # Prefer widgets without an existing layout
                if candidate_containers:
                    self.form_container = candidate_containers[0]
                    print(f"Warning: 'form_container' not found. Using first suitable QWidget as container: {self.form_container.objectName()}")
                else:
                    raise RuntimeError("No suitable form container widget found in user.ui!")
            
            print(f"Found form container: {self.form_container.objectName()}")

            # Set up the layout for the form container
            self.setup_form_container()
            
            # Connect the combo box's signal to load the appropriate form
            self.combo_accessType.currentTextChanged.connect(self.load_form_for_type)
            print("✓ Connected combo box signal")
            
            # Find the QLabel for status messages
            self.status_label = self.findChild(QLabel, "status_label")
            if not self.status_label:
                # Fallback: find any QLabel that might serve as a status label
                labels = self.findChildren(QLabel)
                status_labels = [l for l in labels if 'status' in l.objectName().lower() or not l.objectName()] 
                if status_labels:
                    self.status_label = status_labels[0]
                    print(f"Warning: 'status_label' not found. Using first suitable QLabel as status label: {self.status_label.objectName()}")
                else:
                    print("Warning: No status label found in user.ui. Status messages will only print to console.")
            print(f"Found status label: {self.status_label.objectName() if self.status_label else 'N/A'}")
            
            print("✓ Widget setup complete")
            
            # Load the first form defined in the combo box initially
            if self.combo_accessType.count() > 0:
                self.load_form_for_type(self.combo_accessType.currentText())
            else:
                self.show_status("No forms loaded. Please check form_definitions.", is_error=True)

            # Find and connect the 'View My Requests' button
            self.view_requests_button = self.findChild(QPushButton, 'viewMyRequests_pushButton')
            if self.view_requests_button:
                self.view_requests_button.clicked.connect(self.show_my_requests_window)
                print("✓ Connected 'viewMyRequests_pushButton' to show_my_requests_window()")
            else:
                print("WARNING: 'viewMyRequests_pushButton' not found in user.ui. Cannot connect 'My Requests' button.")
                QMessageBox.warning(self, "UI Missing", "The 'View My Requests' button was not found in the main UI.")
            
        except Exception as e:
            print(f"Widget setup error: {str(e)}")
            QMessageBox.critical(self, "Setup Error", f"Critical error during UI setup: {str(e)}\n{traceback.format_exc()}")
            raise # Re-raise to be caught by the main __init__ handler

    def setup_form_container(self):
        """Sets up the QVBoxLayout for the form_container to dynamically load forms."""
        try:
            # Clear any existing layout and its widgets from the container
            if self.form_container.layout():
                print("Clearing existing layout from form container")
                old_layout = self.form_container.layout()
                while old_layout.count():
                    child = old_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater() # Properly delete widgets
                old_layout.deleteLater() # Delete the old layout object itself
            
            # Create a new QVBoxLayout and set it on the container
            self.form_layout = QVBoxLayout()
            self.form_container.setLayout(self.form_layout)
            
            # Set layout properties for better appearance
            self.form_layout.setContentsMargins(5, 5, 5, 5)
            self.form_layout.setSpacing(5)
            self.form_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft) # Align content to top-left

            self.form_container.setVisible(True)
            
            print("✓ Form container layout setup complete")
            
        except Exception as e:
            print(f"Form container setup error: {str(e)}")
            raise
    
    def load_form_for_type(self, form_display_name):
        """Loads the appropriate UI form based on the selected item in the combo box."""
        try:
            print(f"\n=== ATTEMPTING TO LOAD FORM FOR: '{form_display_name}' ===")

            if not form_display_name or form_display_name.strip() == "":
                self.clear_current_form_display()
                self.show_status("Veuillez sélectionner un type de formulaire.")
                print("Form display name is empty or whitespace.")
                return

            form_info = self.form_definitions.get(form_display_name)
            if not form_info:
                self.show_status("Aucune définition de formulaire trouvée pour cette sélection.", is_error=True)
                print(f"Error: No mapping found in form_definitions for: '{form_display_name}'")
                print(f"Available mappings: {list(self.form_definitions.keys())}")
                return

            ui_filename = form_info['filename']
            form_path = os.path.join(self.UI_DIR, ui_filename)
            print(f"Attempting to load form UI from: {form_path}")

            if not os.path.exists(form_path):
                self.show_status(f"Fichier UI du formulaire introuvable: {ui_filename}", is_error=True)
                print(f"ERROR: Form UI file not found at: {form_path}")
                return

            # Clear any previously loaded form
            self.clear_current_form_display()

            # Create a new QWidget to load the form UI into
            print(f"Loading form: {ui_filename}")
            form_widget = QWidget()
            uic.loadUi(form_path, form_widget)

            form_widget.setVisible(True) 

            # Add the new form widget to the container's layout
            if self.form_layout.count() > 0: 
                self.clear_current_form_display() 
            self.form_layout.addWidget(form_widget)
            self.current_form_widget = form_widget 

            # Force updates to ensure UI refreshes immediately
            self.form_container.update()
            self.form_layout.update()
            self.form_container.setVisible(True) 
            self.form_container.show() 

            self.show_status(f"Formulaire chargé: {form_display_name}")

            print(f"✓ Form '{ui_filename}' loaded successfully!")
            print(f"   - Form widget size: {form_widget.size()} | Visible: {form_widget.isVisible()}")
            print(f"   - Container size: {self.form_container.size()} | Visible: {self.form_container.isVisible()}")

            # Connect the submit button for the newly loaded form
            submit_btn = self.current_form_widget.findChild(QPushButton, form_info['submit_button_name'])
            if submit_btn:
                try:
                    submit_btn.clicked.disconnect() 
                except TypeError:
                    pass 
                submit_btn.clicked.connect(self.send_request)
                print(f"✓ Connected '{form_info['submit_button_name']}' to send_request()")
            else:
                print(f"WARNING: Submit button '{form_info['submit_button_name']}' not found on {ui_filename}. Cannot submit this form.")
                QMessageBox.warning(self, "Button Missing", f"Submit button '{form_info['submit_button_name']}' not found on {ui_filename}. Request submission for this form type will not work.")

        except Exception as e:
            error_msg = f"Error loading form '{form_display_name}':\n{str(e)}\n\n{traceback.format_exc()}"
            self.show_status(error_msg, is_error=True)
            print(error_msg)
            
    def clear_current_form_display(self):
        """Removes and deletes the currently displayed form widget from the container."""
        if self.current_form_widget:
            print(f"Clearing previous form: {self.current_form_widget.objectName() if hasattr(self.current_form_widget, 'objectName') else 'Unknown'}")
            self.form_layout.removeWidget(self.current_form_widget)
            self.current_form_widget.hide()
            self.current_form_widget.deleteLater()
            self.current_form_widget = None 
            print("Previous form cleared.")


    def send_request(self):
        """
        Collects data from the currently displayed form, adds metadata, and saves it to a CSV file.
        This method is connected to the 'clicked' signal of each form's submit button.
        """
        current_form_name = self.combo_accessType.currentText()
        current_form_widget = self.current_form_widget
        form_info = self.form_definitions.get(current_form_name)

        print("\n--- Starting send_request ---")
        print(f"Current form name: {current_form_name}")
        
        if not form_info or not current_form_widget:
            QMessageBox.warning(self, "Submission Error", "No form is currently selected or loaded. Cannot submit.")
            print("Error: No form_info or current_form_widget found.")
            return

        # Basic request metadata
        request_data = {
            'RequestID': str(uuid.uuid4()), 
            'FormType': current_form_name,
            'DateSubmitted': QDate.currentDate().toString('yyyy-MM-dd'),
            USER_MATRICULE_COLUMN_NAME: self.user_matricule, 
            'Status': 'Pending' 
        }
        print(f"Initial request_data (metadata): {request_data}")

        # Collect data from form fields based on the definition
        print("Collecting form field data...")
        for field_name, field_type in form_info['fields'].items():
            widget = current_form_widget.findChild(field_type, field_name)
            if widget:
                if isinstance(widget, QLineEdit):
                    request_data[field_name] = widget.text()
                    print(f"  - Field '{field_name}' (QLineEdit): '{widget.text()}'")
                elif isinstance(widget, QTextEdit):
                    request_data[field_name] = widget.toPlainText()
                    print(f"  - Field '{field_name}' (QTextEdit): '{widget.toPlainText()}'")
                elif isinstance(widget, QDateEdit):
                    request_data[field_name] = widget.date().toString('yyyy-MM-dd')
                    print(f"  - Field '{field_name}' (QDateEdit): '{widget.date().toString('yyyy-MM-dd')}'")
                elif isinstance(widget, QRadioButton): 
                    request_data[field_name] = "Checked" if widget.isChecked() else "Unchecked" 
                    print(f"  - Field '{field_name}' (QRadioButton): '{request_data[field_name]}'")
                elif isinstance(widget, QCheckBox): 
                    request_data[field_name] = "Checked" if widget.isChecked() else "Unchecked" 
                    print(f"  - Field '{field_name}' (QCheckBox): '{request_data[field_name]}'")
                else:
                    request_data[field_name] = None 
                    print(f"  - Field '{field_name}' (Unsupported Type {field_type.__name__}): None")
            else:
                print(f"  - Warning: Widget '{field_name}' of type {field_type.__name__} NOT FOUND on '{current_form_name}' form. Setting to None.")
                request_data[field_name] = None

        print(f"Collected request_data: {request_data}")
        
        try:
            new_request_df = pd.DataFrame([request_data])
            print(f"new_request_df created. Columns: {new_request_df.columns.tolist()}")

            # Determine all possible columns to ensure consistent CSV schema
            all_possible_columns = set()
            for f_info in self.form_definitions.values():
                all_possible_columns.update(f_info['fields'].keys())
            # Add standard metadata columns
            all_possible_columns.update(['RequestID', 'FormType', 'DateSubmitted', USER_MATRICULE_COLUMN_NAME, 'Status', 'AdminMatricule', 'DecisionDate'])
            print(f"All possible columns identified: {sorted(list(all_possible_columns))}")

            # Define a desired column order, with other columns appended alphabetically
            fixed_order_cols = ['RequestID', 'FormType', 'DateSubmitted', USER_MATRICULE_COLUMN_NAME, 'Status', 'AdminMatricule', 'DecisionDate']
            other_cols = sorted(list(all_possible_columns - set(fixed_order_cols)))
            final_columns_order = fixed_order_cols + other_cols
            print(f"Final columns order for CSV: {final_columns_order}")

            # *****************************************************************
            # CRITICAL FIX: Change CSV path to be directly in BASE_DIR, not a 'data' subfolder
            csv_path = os.path.join(self.BASE_DIR, 'requests_pending.csv') 
            # We no longer need os.makedirs for a 'data' folder, as it's directly in BASE_DIR.
            # If 'polina' folder might not exist, that's handled by your startup checks for BASE_DIR.
            # *****************************************************************

            print(f"CSV file path for saving: {csv_path}")
            
            if os.path.exists(csv_path):
                print(f"CSV file exists. Reading existing data from: {csv_path}")
                existing_df = pd.read_csv(csv_path, dtype=str)
                print(f"Existing DataFrame columns: {existing_df.columns.tolist()}")
                print(f"Existing DataFrame head:\n{existing_df.head()}")
                
                print("Concatenating new request with existing data...")
                combined_df = pd.concat([existing_df, new_request_df], ignore_index=True)
                print(f"Combined DataFrame columns before reindex: {combined_df.columns.tolist()}")
                
                print("Reindexing combined DataFrame to ensure consistent columns...")
                combined_df = combined_df.reindex(columns=final_columns_order, fill_value='')
            else:
                print(f"CSV file does NOT exist. Creating new CSV at: {csv_path}")
                combined_df = new_request_df.reindex(columns=final_columns_order, fill_value='')

            print(f"Combined DataFrame head before saving:\n{combined_df.head()}")
            print(f"Combined DataFrame columns before saving: {combined_df.columns.tolist()}")
            
            # Save the combined DataFrame back to CSV
            combined_df.to_csv(csv_path, index=False)
            print(f"SUCCESS: Request data successfully written to CSV at: {csv_path}")
            
            QMessageBox.information(self, "Demande Soumise", "Votre demande a été soumise avec succès et est en attente de traitement.")

            self.show_status("Demande soumise avec succès.", is_error=False)
            print(f"Request submitted successfully for matricule: {self.user_matricule}.")
            
            # Optionally clear the form after submission
            self.clear_current_form_display() 
            self.load_form_for_type(self.combo_accessType.currentText()) 
            print("Form cleared and reloaded for new submission.")

        except Exception as e:
            error_msg = f"FATAL ERROR during submission process:\n{str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Erreur de Soumission Fatale", error_msg)
            print(error_msg)
            self.show_status("Échec de la soumission. Voir la console pour les détails.", is_error=True)

        print("--- send_request finished ---")


    def show_status(self, message, is_error=False):
        """Displays status messages in the UI's status label and prints to console."""
        try:
            if not hasattr(self, 'status_label') or not self.status_label:
                status_candidates = [obj for obj in self.findChildren(QLabel) if "status" in obj.objectName().lower()]
                if status_candidates:
                    self.status_label = status_candidates[0]
            
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(message)
                if is_error:
                    self.status_label.setStyleSheet("color: red;")
                else:
                    self.status_label.setStyleSheet("color: green;")
            print(f"Status: {message}")
        except Exception as e:
            print(f"Failed to update status label (widget might be missing or invalid): {message}. Error: {e}")

# Main application entry point for testing this specific window
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    test_user_matricule = "09844926" 
    
    main_window = MainUserWindow(user_matricule=test_user_matricule)
    main_window.show()
    sys.exit(app.exec())