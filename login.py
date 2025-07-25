import sys
import os 
import traceback
import pandas as pd
from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QLineEdit, QPushButton, QLabel, QWidget)
from PyQt6.QtCore import Qt
from user import MainUserWindow      
from admin import AdminWindow 

class LoginWindow(QMainWindow):
    def __init__(self, user_csv_path, admin_excel_path, ui_path):
        super().__init__()
        try:
            uic.loadUi(ui_path, self)
            
            self.matricule_input = self.findChild(QLineEdit, "matricule_input")
            self.login_button = self.findChild(QPushButton, "login_button")
            self.status_label = self.findChild(QLabel, "status_label")

            if not self.matricule_input:
                raise RuntimeError("QLineEdit named 'matricule_input' not found in login.ui.")
            if not self.login_button:
                raise RuntimeError("QPushButton named 'login_button' not found in login.ui.")
            if not self.status_label:
                print("Warning: QLabel named 'status_label' not found in login.ui. Status messages will only appear in console.")
        
            self.user_csv_path = user_csv_path
            self.admin_excel_path = admin_excel_path 
            
            # Load datasets:
            self.user_dataset = self.load_dataset(self.user_csv_path, "regular user", 'matricule', desired_length=8)
            self.admin_dataset = self.load_dataset(self.admin_excel_path, "admin", 'Matricule_responsable', desired_length=8)
            
            self.login_button.clicked.connect(self.safe_verify_login)
            
            self.show_status("Enter your matricule (user or admin).")
            
        except Exception as e:
            error_msg = f"Login Window Initialization Error:\n{str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Fatal Error", error_msg)
            self.close()
    
    def show_status(self, message, is_error=False):
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.setText(message)
            if is_error:
                self.status_label.setStyleSheet("color: red;")
            else:
                self.status_label.setStyleSheet("color: green;")
        print(f"LOGIN STATUS: {message}")
    
    def load_dataset(self, file_path, dataset_type="", column_name='matricule', desired_length=None):
        """
        Loads a dataset from a CSV or Excel file, extracts a specific column,
        and cleans it for matricule comparison (removes .0, adds leading zeros).
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"{dataset_type.capitalize()} file not found at: {file_path}")

            df = None
            file_extension = os.path.splitext(file_path)[1].lower()

            dtype_spec = {column_name: str}

            if file_extension == '.csv':
                encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, dtype=dtype_spec)
                        print(f"Successfully loaded {dataset_type} data from CSV with {encoding} encoding.")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error reading {dataset_type} CSV with {encoding}: {str(e)}")
            elif file_extension == '.xlsx':
                try:
                    df = pd.read_excel(file_path, dtype=dtype_spec)
                    print(f"Successfully loaded {dataset_type} data from Excel.")
                except Exception as e:
                    print(f"Error reading {dataset_type} Excel file: {str(e)}")
            else:
                raise ValueError(f"Unsupported file type: {file_extension}. Only .csv and .xlsx are supported.")

            if df is None:
                raise ValueError(f"Failed to read {dataset_type} file with any supported method.")

            df.columns = [col.strip().lower() for col in df.columns]
            normalized_column_name = column_name.strip().lower() 

            if normalized_column_name not in df.columns:
                available_cols = "\n".join(df.columns)
                raise ValueError(f"Required '{column_name}' column (normalized to '{normalized_column_name}') not found in {dataset_type} file. Available columns:\n{available_cols}")
            
            extracted_series = df[normalized_column_name].astype(str).str.strip()
            
            cleaned_series = extracted_series.apply(
                lambda x: x.split('.')[0] if isinstance(x, str) and x.endswith('.0') else x
            )
            
            cleaned_series = cleaned_series[cleaned_series != 'nan']
            cleaned_series = cleaned_series[cleaned_series != '']

            if desired_length is not None:
                final_series = cleaned_series.str.zfill(desired_length)
            else:
                final_series = cleaned_series
            
            final_df = pd.DataFrame({'matricule': final_series})

            print(f"Loaded {len(final_df)} {dataset_type} records from '{file_path}'.")
            print(f"First 5 {dataset_type} matricules from '{column_name}' (cleaned): {final_df['matricule'].head().tolist()}")

            return final_df
            
        except Exception as e:
            error_msg = f"Error loading {dataset_type} data:\n{str(e)}\n\n{traceback.format_exc()}"
            self.show_status(error_msg, is_error=True)
            QMessageBox.critical(self, f"{dataset_type.capitalize()} Data Error", error_msg)
            return pd.DataFrame()
    
    def safe_verify_login(self):
        try:
            self.verify_login()
        except Exception as e:
            error_msg = f"Login Verification Error:\n{str(e)}\n\n{traceback.format_exc()}"
            self.show_status(error_msg, is_error=True)
            QMessageBox.critical(self, "System Error", error_msg)
    
    def verify_login(self):
        matricule_input = self.matricule_input.text().strip()
        
        self.show_status(f"Verifying matricule: {matricule_input}")
        
        if not matricule_input:
            QMessageBox.warning(self, "Input Required", "Please enter your matricule number.")
            return
        
        cleaned_matricule_input = matricule_input
        if cleaned_matricule_input.endswith('.0'):
            cleaned_matricule_input = cleaned_matricule_input.split('.')[0]
        if cleaned_matricule_input.isdigit() and len(cleaned_matricule_input) < 8:
            cleaned_matricule_input = cleaned_matricule_input.zfill(8)
        
        matricule_to_check = cleaned_matricule_input
        print(f"DEBUG: Cleaned matricule input for checking: '{matricule_to_check}'")

        if not self.admin_dataset.empty:
            clean_admin_series = self.admin_dataset['matricule'].str.strip()
            
            if any(clean_admin_series == matricule_to_check):
                self.show_status("Admin login successful!", is_error=False)
                QMessageBox.information(self, "Success", "Admin login successful!")
                self.open_admin_dashboard(matricule_to_check)
                return
        else:
            print("LOGIN LOGIC: Admin dataset is empty, skipping admin check.")

        if not self.user_dataset.empty:
            clean_user_series = self.user_dataset['matricule'].str.strip()
            
            if any(clean_user_series == matricule_to_check):
                self.show_status("User login successful!", is_error=False)
                QMessageBox.information(self, "Success", "Login successful!")
                self.open_user_main_window(matricule_to_check)
                return
        else:
            print("LOGIN LOGIC: User dataset is empty, skipping user check.")

        error_msg = "Matricule not found. Please check your input or contact support."
        
        if not self.user_dataset.empty:
            user_partial_matches = self.user_dataset['matricule'].str.strip()[self.user_dataset['matricule'].str.strip().str.startswith(matricule_to_check)]
            if not user_partial_matches.empty:
                matches = user_partial_matches.head(3).tolist()
                error_msg += f"\n\nSimilar user matricules:\n- " + "\n- ".join(matches)
        
        self.show_status(error_msg, is_error=True)
        QMessageBox.critical(self, "Access Denied", error_msg)
            
    def open_user_main_window(self, matricule):
        try:
            print(f"Opening MainUserWindow for user: {matricule}")
            self.main_user_window = MainUserWindow(matricule)
            self.main_user_window.show()
            self.close()
        except Exception as e:
            error_msg = f"Failed to open user main window:\n{str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Window Error", error_msg)
            print(error_msg)

    def open_admin_dashboard(self, admin_matricule):
        try:
            print(f"Opening AdminDashboard for admin: {admin_matricule}")
            self.admin_dashboard_window = AdminWindow(admin_matricule) 
            self.admin_dashboard_window.show()
            self.close()
        except Exception as e:
            error_msg = f"Failed to open admin dashboard:\n{str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Window Error", error_msg)
            print(error_msg)

if __name__ == "__main__":
    BASE_DIR = r"C:\Users\sl3ag\Desktop\polina" 
    
 
    qss_file_path = os.path.join(BASE_DIR, "styles", "app_style.qss")

    if os.path.exists(qss_file_path):
        try:
            with open(qss_file_path, "r") as f:
                _qss = f.read()
                # Apply the QSS to the QApplication instance
                app = QApplication(sys.argv) # <--- Make sure QApplication is created BEFORE applying QSS
                app.setStyleSheet(_qss) 
            print(f"Successfully loaded QSS from: {qss_file_path}")
        except Exception as e:
            print(f"Error loading QSS file: {e}")
            # If QSS fails to load, still create QApplication to allow app to run
            app = QApplication(sys.argv) 
    else:
        print(f"QSS file not found at: {qss_file_path}")
        # If QSS file not found, still create QApplication to allow app to run
        app = QApplication(sys.argv) 
    # --- END QSS APPLICATION CODE ---
    
    USER_CSV_PATH = os.path.join(BASE_DIR, "Table user.csv")
    ADMIN_EXCEL_PATH = os.path.join(BASE_DIR, "Table user.xlsx") 
    LOGIN_UI_PATH = os.path.join(BASE_DIR, "ui", "login.ui")
    
    print(f"App Startup Check: User CSV path: {USER_CSV_PATH} (exists: {os.path.exists(USER_CSV_PATH)})")
    print(f"App Startup Check: Admin Excel path: {ADMIN_EXCEL_PATH} (exists: {os.path.exists(ADMIN_EXCEL_PATH)})")
    print(f"App Startup Check: Login UI path: {LOGIN_UI_PATH} (exists: {os.path.exists(LOGIN_UI_PATH)})")
    
    # The window creation and execution remains the same
    try:
        window = LoginWindow(USER_CSV_PATH, ADMIN_EXCEL_PATH, LOGIN_UI_PATH)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"FATAL APPLICATION STARTUP ERROR: {str(e)}")
        print(traceback.format_exc())
        QMessageBox.critical(None, "Application Startup Error", 
                             f"The application failed to start:\n{str(e)}\n\n{traceback.format_exc()}")