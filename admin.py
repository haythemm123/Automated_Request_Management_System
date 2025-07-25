import os
import pandas as pd
import traceback
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QLabel, QHeaderView, QDialog,
    QVBoxLayout, QScrollArea, QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt, QDate, QFile, QTextStream

class RequestDetailsDialog(QDialog):
    def __init__(self, request_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Request Details: {request_data.get('RequestID', 'N/A')} ({request_data.get('FormType', 'N/A')})")
        self.setMinimumSize(600, 700) # Give it a reasonable default size

        self.layout = QVBoxLayout(self)

        # Create a scroll area for potentially many fields
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_content = QWidget()
        self.scroll_area_content.setObjectName("scroll_area_content") # Set objectName for QSS targeting
        self.scroll_area_content_layout = QVBoxLayout(self.scroll_area_content)
        self.scroll_area_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Corrected Qt.AlignTop
        self.scroll_area.setWidget(self.scroll_area_content)

        self.layout.addWidget(self.scroll_area)

        # Always display core request information
        self.add_field_display("Request ID:", request_data.get('RequestID', 'N/A'))
        self.add_field_display("Form Type:", request_data.get('FormType', 'N/A'))
        self.add_field_display("Date Submitted:", request_data.get('DateSubmitted', 'N/A'))
        self.add_field_display("User Matricule:", request_data.get('UserMatricule', 'N/A'))
        self.add_field_display("Status:", request_data.get('Status', 'N/A'))
        
        # Only show admin decision details if they are filled
        admin_matricule = request_data.get('AdminMatricule', '').strip()
        decision_date = request_data.get('DecisionDate', '').strip()

        if admin_matricule and admin_matricule != "N/A":
            self.add_field_display("Admin Matricule:", admin_matricule)
        if decision_date and decision_date != "N/A":
            self.add_field_display("Decision Date:", decision_date)
            
        self.add_field_display("-" * 50, "") # Separator for form-specific fields

        # Iterate through all other fields and display them ONLY IF THEY HAVE A VALUE
        # Define a set of already displayed common headers to skip
        common_headers_displayed = {
            'RequestID', 'FormType', 'DateSubmitted', 'UserMatricule', 'Status', 
            'AdminMatricule', 'DecisionDate', 'index', # 'index' is pandas internal
            'DateSubmitted_obj' # Temporary column used for sorting in user_requests_manager
        }

        # Filter out empty or "N/A" values when displaying form-specific fields
        for key, value in request_data.items():
            value = str(value).strip() # Ensure value is string and strip whitespace
            # Skip common headers, empty values, or values that are just "N/A"
            if key not in common_headers_displayed and value and value != "N/A":
                # For long text fields, use QTextEdit for better display
                if '_textEdit' in key or '_motif' in key or '_besoin' in key:
                    self.add_long_text_display(key.replace('_', ' ').title(), value)
                else:
                    self.add_field_display(key.replace('_', ' ').title(), value) # Simple capitalization for display

    def add_field_display(self, label_text, value_text):
        """Helper to add a label and a value as read-only text."""
        h_layout = QHBoxLayout()
        label = QLabel(f"<b>{label_text}</b>")
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred) # Adjust size policy

        value_label = QLabel(str(value_text))
        value_label.setWordWrap(True)
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse) # Allow text selection
        value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred) # Adjust size policy

        h_layout.addWidget(label)
        h_layout.addWidget(value_label, 1) # Stretch value label
        self.scroll_area_content_layout.addLayout(h_layout)

    def add_long_text_display(self, label_text, value_text):
        """Helper to add a label and a QTextEdit for potentially long text."""
        label = QLabel(f"<b>{label_text}:</b>")
        label.setWordWrap(True)
        self.scroll_area_content_layout.addWidget(label)

        text_edit = QTextEdit(str(value_text))
        text_edit.setReadOnly(True)
        text_edit.setMinimumHeight(80) # Give it some height
        text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Fixed height, expanding width
        self.scroll_area_content_layout.addWidget(text_edit)


class AdminWindow(QMainWindow):
    def __init__(self, admin_matricule, parent=None):
        super().__init__(parent)
        self.admin_matricule = admin_matricule
        try:
            BASE_DIR = r"C:\Users\sl3ag\Desktop\polina" # Ensure this path is correct for your system
            ADMIN_UI_PATH = os.path.join(BASE_DIR, "ui", "admin.ui")
            
            uic.loadUi(ADMIN_UI_PATH, self)
            self.setWindowTitle("Administrator Dashboard")
            
            self.BASE_DIR = BASE_DIR
            self.CSV_PATH = os.path.join(self.BASE_DIR, 'requests_pending.csv')
            # Path to the specific QSS for the details dialog
            self.DETAILS_QSS_PATH = os.path.join(self.BASE_DIR, "styles", "admin_details_style.qss") 

            self.adminDataTable = self.findChild(QTableWidget, 'adminDataTable')
            self.saveChanges_pushButton = self.findChild(QPushButton, 'saveChanges_pushButton')
            self.title_label = self.findChild(QLabel, 'title_label') # Make sure this objectName exists in admin.ui

            if not self.adminDataTable:
                raise RuntimeError("QTableWidget with objectName 'adminDataTable' not found in admin.ui!")
            if not self.saveChanges_pushButton:
                raise RuntimeError("QPushButton with objectName 'saveChanges_pushButton' not found in admin.ui!")

            self.saveChanges_pushButton.clicked.connect(self.save_table_to_csv)
            
            self.ensure_csv_headers() # Call this before loading requests
            self.load_requests_to_table() # Load requests into the table

            self.status_label = self.findChild(QLabel, 'statusLabel') # Make sure this objectName exists in admin.ui
            if not self.status_label:
                print("Warning: No QLabel named 'statusLabel' found in admin.ui. Status messages won't be displayed there.")
                
            self.show_status("Administrator dashboard loaded.")

        except Exception as e:
            error_msg = f"Admin window initialization error:\n{str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Fatal Error", error_msg)
            print(error_msg)
            self.close()

    def _load_qss_file(self, qss_file_path):
        """Loads and returns the content of a QSS file."""
        if not os.path.exists(qss_file_path):
            print(f"Warning: QSS file not found: {qss_file_path}")
            return ""
        
        file = QFile(qss_file_path)
        if not file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            print(f"Warning: Could not open QSS file: {qss_file_path}")
            return ""
        
        stream = QTextStream(file)
        qss_content = stream.readAll()
        file.close()
        return qss_content

    def ensure_csv_headers(self):
        """Ensures the CSV file exists with all necessary headers."""
        # ALL possible headers from all your forms should be listed here
        expected_headers = [
            'RequestID', 'FormType', 'DateSubmitted', 'UserMatricule', 'Status', 'AdminMatricule', 'DecisionDate',
            # Access Distance fields
            'accessDistance_appSysteme_textEdit', 'accessDistance_besoin_textEdit',
            'accessDistance_cleSecurite_deviceMobile_lineEdit', 'accessDistance_cleSecurite_du_dateEdit',
            'accessDistance_cleSecurite_periodeSouhaitee_dateEdit', 'accessDistance_cleSecurite_token_lineEdit',
            'accessDistance_date_dateEdit', 'accessDistance_filiale_lineEdit', 'accessDistance_nomPrenom_lineEdit',
            'accessDistance_periodePerm_radio', 'accessDistance_periodeTemp_radio', 'accessDistance_service_lineEdit',
            'accessDistance_typeAccesPersonalise_radio', 'accessDistance_typeAccesTotal_radio',
            # Cle 3G fields
            'cle3g_anciennete_lineEdit', 'cle3g_date_dateEdit', 'cle3g_filiale_lineEdit', 'cle3g_motif_textEdit',
            'cle3g_nomPrenom_lineEdit', 'cle3g_nouvelleDemande_radio', 'cle3g_renouvellement_radio',
            'cle3g_service_lineEdit',
            # External Drive fields
            'externalDrive_cle3g_radio', 'externalDrive_engagement1_checkBox',
            'externalDrive_engagement2_checkBox', 'externalDrive_engagement3_checkBox',
            'externalDrive_filiale_lineEdit', 'externalDrive_flashDisque_radio', 'externalDrive_graveurCDDVD_radio',
            'externalDrive_lecteurCDDVD_radio', 'externalDrive_lectureEcriture_radio', 'externalDrive_lecture_radio',
            'externalDrive_service_lineEdit',
            # Gravure fields
            'gravure_cdrom_checkBox', 'gravure_date_dateEdit',
            'gravure_demandeGravure_lineEdit', 'gravure_dvdrom_checkBox', 'gravure_logiciel1_num_lineEdit',
            'gravure_logiciel2_num_lineEdit', 'gravure_logiciel3_num_lineEdit', 'gravure_logiciel4_num_lineEdit',
            'gravure_logiciel5_num_lineEdit', 'gravure_motif_textEdit', 'gravure_numFicheCD_lineEdit',
            'gravure_total_lineEdit', 'gravure_unite_lineEdit',
            # Internet fields
            'internet_anciennete_lineEdit', 'internet_date_dateEdit', 'internet_filiale_lineEdit', 'internet_motif_textEdit',
            'internet_nomPrenom_lineEdit', 'internet_nouvelleDemande_radio', 'internet_renouvellement_radio',
            'internet_service_lineEdit'
        ]

        if not os.path.exists(self.CSV_PATH) or os.stat(self.CSV_PATH).st_size == 0:
            try:
                empty_df = pd.DataFrame(columns=expected_headers)
                empty_df.to_csv(self.CSV_PATH, index=False)
            except Exception as e:
                QMessageBox.critical(self, "CSV Init Error", 
                                     f"Could not initialize CSV file with headers: {self.CSV_PATH}\nError: {str(e)}")
        else:
            try:
                current_df_headers = pd.read_csv(self.CSV_PATH, nrows=0).columns.tolist()
                
                missing_headers = [col for col in expected_headers if col not in current_df_headers]
                if missing_headers:
                    # Read all existing data first
                    temp_df = pd.read_csv(self.CSV_PATH, dtype=str, keep_default_na=False)
                    # Add new columns, initialized to empty strings
                    for col in missing_headers:
                        temp_df[col] = ''
                    # Reorder columns to match expected_headers for consistency (optional but good practice)
                    temp_df = temp_df.reindex(columns=expected_headers, fill_value='')
                    temp_df.to_csv(self.CSV_PATH, index=False)
                else:
                    pass # All expected headers are present.

            except pd.errors.EmptyDataError:
                # If it's just headers but no data, re-initialize to ensure all expected headers are there
                self.ensure_csv_headers() 
            except Exception as e:
                QMessageBox.warning(self, "CSV Header Check Error", 
                                     f"Could not verify/update headers for existing CSV: {self.CSV_PATH}\nError: {str(e)}")

    def load_requests_to_table(self):
        """Loads requests from CSV into the QTableWidget (for admin view)."""
        self.adminDataTable.setRowCount(0)
        # Added a column for "Details" button
        self.adminDataTable.setColumnCount(7) 
        self.adminDataTable.setHorizontalHeaderLabels([
            'Request ID', 'Form Type', 'Date Submitted', 'User Matricule', 'Status', 'Action', 'Details' # 'Details' column added
        ])
        # Auto-resize columns and stretch the last one ('Details') to fill available space
        self.adminDataTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.adminDataTable.horizontalHeader().setStretchLastSection(True) 
        self.adminDataTable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.adminDataTable.verticalHeader().setDefaultSectionSize(35) # Adjust row height for buttons

        try:
            # Read all columns as string to avoid mixed type warnings
            self.current_df = pd.read_csv(self.CSV_PATH, dtype=str, keep_default_na=False) 
            
            if self.current_df.empty:
                self.show_status("No pending requests found.", is_error=False)
                return

            # Check for duplicate RequestIDs
            if 'RequestID' in self.current_df.columns:
                self.current_df.drop_duplicates(subset=['RequestID'], keep='first', inplace=True)
            
            self.adminDataTable.setRowCount(len(self.current_df))

            # Define mapping from CSV column names to display column indices in the table
            csv_header_to_display_map = {
                'RequestID': 0, 
                'FormType': 1, 
                'DateSubmitted': 2, 
                'UserMatricule': 3, 
                'Status': 4,
            }
            
            for row_idx, row_series in self.current_df.iterrows(): # Use row_series for cleaner .get()
                for csv_col_name, display_col_idx in csv_header_to_display_map.items():
                    item_text = row_series.get(csv_col_name, "N/A") 
                    self.adminDataTable.setItem(row_idx, display_col_idx, QTableWidgetItem(str(item_text)))

                # Action Buttons (Accept/Reject)
                action_button_widget = QWidget()
                action_h_layout = QHBoxLayout(action_button_widget)
                action_h_layout.setContentsMargins(0, 0, 0, 0) # No margins
                action_h_layout.setSpacing(5) # Spacing between buttons

                accept_button = QPushButton("Accept")
                reject_button = QPushButton("Reject")

                # Connect buttons with lambda to pass row_idx
                accept_button.clicked.connect(lambda _, r=row_idx: self.set_status_accepted(r))
                reject_button.clicked.connect(lambda _, r=row_idx: self.set_status_rejected(r))

                action_h_layout.addWidget(accept_button)
                action_h_layout.addWidget(reject_button)
                action_button_widget.setLayout(action_h_layout)

                action_col_idx = self.get_column_index('Action') 
                if action_col_idx != -1:
                    self.adminDataTable.setCellWidget(row_idx, action_col_idx, action_button_widget)
                else:
                    pass # Warning already printed by get_column_index if it returns -1

                # Details Button
                details_button_widget = QWidget()
                details_h_layout = QHBoxLayout(details_button_widget)
                details_h_layout.setContentsMargins(0, 0, 0, 0)
                details_h_layout.setSpacing(5)

                view_details_button = QPushButton("View Details")
                # Pass the entire row_data (as a dictionary) to the handler
                view_details_button.clicked.connect(lambda _, data=row_series.to_dict(): self.show_request_details(data))

                details_h_layout.addWidget(view_details_button)
                details_button_widget.setLayout(details_h_layout)

                details_col_idx = self.get_column_index('Details') # Get index of new 'Details' column
                if details_col_idx != -1:
                    self.adminDataTable.setCellWidget(row_idx, details_col_idx, details_button_widget)
                else:
                    pass # Warning already printed by get_column_index if it returns -1

            self.show_status(f"Loaded {len(self.current_df)} pending requests.")

        except Exception as e:
            error_msg = f"Error loading requests to table: {str(e)}\n{traceback.format_exc()}"
            self.show_status(error_msg, is_error=True)
            print(error_msg) # Keep print for critical errors

    def show_request_details(self, request_data):
        """Opens a new dialog to display all details of a selected request."""
        dialog = RequestDetailsDialog(request_data, self)
        # Apply QSS to the dialog
        qss_content = self._load_qss_file(self.DETAILS_QSS_PATH) # Use DETAILS_QSS_PATH
        if qss_content:
            dialog.setStyleSheet(qss_content)
        dialog.exec() # Use exec() to make it a modal dialog

    def set_status_accepted(self, row_idx):
        current_date_str = QDate.currentDate().toString(Qt.DateFormat.ISODate)
        if row_idx < len(self.current_df): 
            self.current_df.loc[row_idx, 'Status'] = "Approved"
            self.current_df.loc[row_idx, 'AdminMatricule'] = self.admin_matricule
            self.current_df.loc[row_idx, 'DecisionDate'] = current_date_str
            
            # Update the QTableWidgetItem directly for visual feedback
            status_col_idx = self.get_column_index('Status')
            if status_col_idx != -1:
                status_item = self.adminDataTable.item(row_idx, status_col_idx)
                if status_item: 
                    status_item.setText("Approved")
                else: 
                    self.adminDataTable.setItem(row_idx, status_col_idx, QTableWidgetItem("Approved"))
            self.show_status(f"Request {row_idx+1} status set to Approved (unsaved).")
            self.save_table_to_csv() # Automatically save after action
        else: self.show_status(f"Error: Invalid row index {row_idx} for status update.", is_error=True)

    def set_status_rejected(self, row_idx):
        current_date_str = QDate.currentDate().toString(Qt.DateFormat.ISODate)
        if row_idx < len(self.current_df): 
            self.current_df.loc[row_idx, 'Status'] = "Rejected"
            self.current_df.loc[row_idx, 'AdminMatricule'] = self.admin_matricule
            self.current_df.loc[row_idx, 'DecisionDate'] = current_date_str
            
            # Update the QTableWidgetItem directly for visual feedback
            status_col_idx = self.get_column_index('Status')
            if status_col_idx != -1:
                status_item = self.adminDataTable.item(row_idx, status_col_idx)
                if status_item: 
                    status_item.setText("Rejected")
                else: 
                    self.adminDataTable.setItem(row_idx, status_col_idx, QTableWidgetItem("Rejected"))
            self.show_status(f"Request {row_idx+1} status set to Rejected (unsaved).")
            self.save_table_to_csv() # Automatically save after action
        else: self.show_status(f"Error: Invalid row index {row_idx} for status update.", is_error=True)
    
    def get_column_index(self, col_name):
        """Helper to get column index by header name."""
        for i in range(self.adminDataTable.columnCount()):
            header_item = self.adminDataTable.horizontalHeaderItem(i)
            if header_item and header_item.text() == col_name:
                return i
        return -1

    def save_table_to_csv(self):
        if not hasattr(self, 'current_df') or self.current_df.empty:
            QMessageBox.warning(self, "No Data", "No requests to save.")
            return

        try:
            if not self.current_df.empty:
                self.current_df.to_csv(self.CSV_PATH, index=False)
            QMessageBox.information(self, "Save Complete", "Changes saved successfully to requests_pending.csv!")
            self.show_status("Changes saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving changes: {e}")
            self.show_status(f"Error saving changes: {e}", is_error=True)
            print(f"ERROR: save_table_to_csv: {e}\n{traceback.format_exc()}") # Keep print for critical errors
            
    def show_status(self, message, is_error=False):
        """Displays status messages in the status label."""
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.setText(message)
            if is_error: 
                self.status_label.setStyleSheet("color: red;")
            else: 
                self.status_label.setStyleSheet("color: green;")
        else: 
            # Fallback to print if status_label is not found (useful for debugging UI issues)
            print(f"Admin Status: {message}")

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    
    # --- START GLOBAL QSS LOADING ---
    BASE_DIR_FOR_GLOBAL_QSS = r"C:\Users\sl3ag\Desktop\polina" # Confirm this is your base directory
    GLOBAL_QSS_PATH = os.path.join(BASE_DIR_FOR_GLOBAL_QSS, "styles", "app_style.qss") # Assuming your global QSS is named app_style.qss

    if os.path.exists(GLOBAL_QSS_PATH):
        file = QFile(GLOBAL_QSS_PATH)
        if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(file)
            app.setStyleSheet(stream.readAll()) # Apply the global QSS to the whole application
            file.close()
            print(f"Loaded global QSS from: {GLOBAL_QSS_PATH}")
        else:
            print(f"Warning: Could not open global QSS file: {GLOBAL_QSS_PATH}")
    else:
        print(f"Warning: Global QSS file not found at: {GLOBAL_QSS_PATH}")
    # --- END GLOBAL QSS LOADING ---

    # IMPORTANT: Change this to a valid admin matricule for testing.
    admin_window = AdminWindow(admin_matricule='05792603') 
    admin_window.show()
    sys.exit(app.exec())
