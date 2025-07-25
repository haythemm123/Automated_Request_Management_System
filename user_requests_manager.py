import os
import pandas as pd
import traceback
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView, QPushButton
from PyQt6.QtCore import Qt, QDate 


# This MATRICULE_COLUMN_NAME must match the exact column name
# in your requests_pending.csv and requests_archive.csv that stores the
# matricule of the USER WHO SUBMITTED THE REQUEST.
MATRICULE_COLUMN_NAME = 'UserMatricule' 
ADMIN_MATRICULE_COLUMN_NAME = 'AdminMatricule' # Consistent name for admin matricule in requests CSVs

class UserRequestsView(QWidget):
    def __init__(self, user_matricule, base_dir, parent=None):
        super().__init__(parent)
        self.user_matricule = user_matricule
        self.BASE_DIR = base_dir
        self.UI_DIR = os.path.join(self.BASE_DIR, "ui")
        
        self.CSV_PATH = os.path.join(self.BASE_DIR, "requests_pending.csv")
        self.ARCHIVE_CSV_PATH = os.path.join(self.BASE_DIR, "requests_archive.csv")
        self.USERS_CSV_PATH = os.path.join(self.BASE_DIR, "Table user.csv") # Path to the user data CSV

        # Define all expected headers for requests CSVs, using consistent casing
        self.expected_request_headers = [
            'RequestID', 'FormType', 'DateSubmitted', MATRICULE_COLUMN_NAME, 
            'Status', ADMIN_MATRICULE_COLUMN_NAME, 'DecisionDate', 'FormData'
        ]

        # Ensure both requests CSVs exist with correct headers
        self._ensure_request_csv_headers(self.CSV_PATH)
        self._ensure_request_csv_headers(self.ARCHIVE_CSV_PATH)


        self.setWindowTitle(f"My Submitted Requests - User: {self.user_matricule}")
        self.resize(900, 600) # Slightly larger default size for the table view

        self.init_ui()
        # Load requests immediately after UI initialization
        self.load_user_requests()

    def _standardize_dataframe_headers(self, df):
        """
        Converts DataFrame headers to a consistent casing and removes duplicate columns
        that arise from inconsistent casing (e.g., 'RequestID' and 'requestID').
        Prioritizes the first encountered version of a column if casing varies.
        """
        # Mapping for core columns. Keys are lowercase, values are desired casing.
        standard_mapping = {
            'requestid': 'RequestID',
            'formtype': 'FormType',
            'datesubmitted': 'DateSubmitted',
            'usermatricule': 'UserMatricule',
            'status': 'Status',
            'adminmatricule': 'AdminMatricule',
            'decisiondate': 'DecisionDate',
            'formdata': 'FormData'
            # Add other common form fields if their casing varies and causes issues
        }
        
        new_columns_map = {} # Maps old column names (original casing) to new standardized names
        standardized_names_seen = set() # Tracks standardized names to avoid duplicates

        # Iterate through original columns to build the mapping and identify duplicates
        for col in df.columns:
            standardized_col_name = standard_mapping.get(col.lower(), col) # Get standardized name

            # If this standardized name (lowercase) has already been processed,
            # it means we have a casing duplicate in the original CSV.
            # We will keep the first one encountered and discard subsequent ones.
            if standardized_col_name.lower() in standardized_names_seen:
                # This column will be dropped later
                print(f"DEBUG (User_RM - Header Standardization): Detected and will drop duplicate column '{col}' (standardized to '{standardized_col_name}').")
                new_columns_map[col] = None # Mark for dropping
            else:
                new_columns_map[col] = standardized_col_name
                standardized_names_seen.add(standardized_col_name.lower())

        # Rename columns in the DataFrame
        df.rename(columns={k: v for k, v in new_columns_map.items() if v is not None}, inplace=True)
        
        # Drop columns that were marked for dropping (i.e., duplicates due to casing)
        cols_to_drop = [k for k, v in new_columns_map.items() if v is None]
        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True, errors='ignore')

        # Ensure all expected headers are present after standardization and reorder
        current_cols = df.columns.tolist()
        for header in self.expected_request_headers:
            if header not in current_cols:
                df[header] = '' # Add missing columns
        
        # Reorder columns to match expected_headers, placing other columns at the end
        final_columns_order = self.expected_request_headers + [col for col in df.columns if col not in self.expected_request_headers]
        df = df.reindex(columns=final_columns_order, fill_value='')
        
        return df


    def _ensure_request_csv_headers(self, file_path):
        """Ensures a specific requests CSV file exists with all expected headers."""
        if not os.path.exists(file_path):
            df = pd.DataFrame(columns=self.expected_request_headers)
            df.to_csv(file_path, index=False)
        else:
            try:
                df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
                # Standardize headers of the loaded DataFrame before checking for missing ones
                df = self._standardize_dataframe_headers(df)

                missing_headers = [h for h in self.expected_request_headers if h not in df.columns]
                if missing_headers:
                    print(f"Warning: Missing headers {missing_headers} in {file_path}. Adding them.")
                    for header in missing_headers:
                        df[header] = '' # Add missing columns as empty strings
                    # Reorder columns to match expected_headers for consistency
                    df = df.reindex(columns=self.expected_request_headers + [col for col in df.columns if col not in self.expected_request_headers], fill_value='')
                    df.to_csv(file_path, index=False) # Rewrite the CSV with updated headers
            except pd.errors.EmptyDataError:
                # If file is empty but exists, rewrite with full headers
                df = pd.DataFrame(columns=self.expected_request_headers)
                df.to_csv(file_path, index=False)
            except Exception as e:
                print(f"Error checking/ensuring headers for {file_path}: {e}")


    def init_ui(self):
        """Loads the UI from my_requests_view.ui and sets up widgets."""
        ui_file_path = os.path.join(self.UI_DIR, "my_requests_view.ui")
        if not os.path.exists(ui_file_path):
            QMessageBox.critical(self, "UI Error", f"UI file not found: {ui_file_path}")
            return

        uic.loadUi(ui_file_path, self)

        # Find the table widget and refresh button by their objectNames
        self.requests_table = self.findChild(QTableWidget, 'userRequests_tableWidget')
        self.refresh_button = self.findChild(QPushButton, 'refreshUserRequests_pushButton')

        if self.requests_table:
            # Update table headers: 'Admin Matricule' changes to 'Admin Name'
            self.requests_table.setColumnCount(6) 
            self.requests_table.setHorizontalHeaderLabels(['Request Date', 'Form Type', 'Status', 'Admin Name', 'Decision Date', 'Request ID']) # Changed header
            
            # Auto-resize columns and stretch the last one to fill available space
            self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.requests_table.horizontalHeader().setStretchLastSection(True)
        else:
            QMessageBox.critical(self, "UI Error", "Table widget 'userRequests_tableWidget' not found in my_requests_view.ui")
            return

        if self.refresh_button:
            self.refresh_button.clicked.connect(self.load_user_requests)
        else:
            QMessageBox.critical(self, "UI Error", "Refresh button 'refreshUserRequests_pushButton' not found in my_requests_view.ui")

    def load_admin_names(self):
        """Loads admin matricules and names from the Table user.csv."""
        print(f"DEBUG (User_RM - Admin Names): Attempting to load from: {self.USERS_CSV_PATH}")
        if not os.path.exists(self.USERS_CSV_PATH):
            print(f"DEBUG (User_RM - Admin Names): {self.USERS_CSV_PATH} NOT FOUND.")
            return pd.DataFrame(columns=['Matricule_Responsable', 'Nom_Prenom_Responsable']) 

        try:
            users_df = pd.read_csv(self.USERS_CSV_PATH, dtype=str, keep_default_na=False)
            print(f"DEBUG (User_RM - Admin Names): Columns in {self.USERS_CSV_PATH}: {users_df.columns.tolist()}")
            
            required_cols = ['Matricule_Responsable', 'Nom_Prenom_Responsable']
            if all(col in users_df.columns for col in required_cols):
                # CRITICAL FIX: Convert Matricule_Responsable to integer first to remove '.0', then to string, then pad with leading zeros
                # This ensures '5792603.0' becomes '05792603' if it's an 8-digit matricule
                users_df['Matricule_Responsable'] = users_df['Matricule_Responsable'].apply(
                    lambda x: str(int(float(x))).zfill(8) if pd.notna(x) and str(x).replace('.', '').isdigit() else str(x)
                ).str.strip()
                
                # NEW FIX: Drop duplicates based on Matricule_Responsable to ensure unique admin entries for merge
                initial_admin_rows = len(users_df)
                users_df.drop_duplicates(subset=['Matricule_Responsable'], keep='first', inplace=True)
                if len(users_df) < initial_admin_rows:
                    print(f"DEBUG (User_RM - Admin Names): Removed {initial_admin_rows - len(users_df)} duplicate Matricule_Responsable entries from Table user.csv data.")
                else:
                    print("DEBUG (User_RM - Admin Names): No duplicate Matricule_Responsable entries found in Table user.csv data.")

                print(f"DEBUG (User_RM - Admin Names): First 5 rows of relevant admin data (Matricule_Responsable cleaned and de-duplicated):\n{users_df[required_cols].head()}")
                return users_df[required_cols]
            else:
                print(f"DEBUG (User_RM - Admin Names): Error: Required columns {required_cols} not found in {self.USERS_CSV_PATH}.")
                return pd.DataFrame(columns=required_cols)
        except Exception as e:
            print(f"Error loading admin names from {self.USERS_CSV_PATH}: {e}")
            print(f"Traceback for load_admin_names:\n{traceback.format_exc()}")
            return pd.DataFrame(columns=['Matricule_Responsable', 'Nom_Prenom_Responsable'])


    def load_user_requests(self):
        """Loads requests from CSVs, filters for the current user, and populates the table."""
        self.requests_table.setRowCount(0) # Clear existing rows before loading new data
        print(f"Loading requests for matricule: {self.user_matricule}")

        list_of_dfs = [] # Use a list to collect DataFrames before concatenating

        try:
            # Load pending requests if the file exists
            if os.path.exists(self.CSV_PATH):
                try:
                    df_pending = pd.read_csv(self.CSV_PATH, dtype=str, keep_default_na=False)
                    df_pending = self._standardize_dataframe_headers(df_pending) # Standardize headers and remove duplicates
                    print(f"DEBUG (User_RM): requests_pending.csv loaded. Shape: {df_pending.shape}, Columns: {df_pending.columns.tolist()}")
                    print(f"DEBUG (User_RM): requests_pending.csv head:\n{df_pending.head()}")
                    if not df_pending.empty:
                        list_of_dfs.append(df_pending)
                except pd.errors.EmptyDataError:
                    print(f"Pending requests CSV is empty: {self.CSV_PATH}")
                except Exception as e:
                    print(f"Error reading pending requests CSV {self.CSV_PATH}: {e}")
            else:
                print(f"Pending requests CSV not found at: {self.CSV_PATH}")
            
            # Load archived requests if the file exists
            if os.path.exists(self.ARCHIVE_CSV_PATH):
                try:
                    df_archive = pd.read_csv(self.ARCHIVE_CSV_PATH, dtype=str, keep_default_na=False)
                    df_archive = self._standardize_dataframe_headers(df_archive) # Standardize headers and remove duplicates
                    print(f"DEBUG (User_RM): requests_archive.csv loaded. Shape: {df_archive.shape}, Columns: {df_archive.columns.tolist()}")
                    print(f"DEBUG (User_RM): requests_archive.csv head:\n{df_archive.head()}")
                    if not df_archive.empty:
                        list_of_dfs.append(df_archive)
                    else: # If archive is empty, create a dummy DataFrame with expected headers to avoid concat issues
                        print(f"DEBUG (User_RM): Archive requests CSV is empty, creating dummy DataFrame for concat.")
                        dummy_archive_df = pd.DataFrame(columns=self.expected_request_headers)
                        list_of_dfs.append(dummy_archive_df)
                except pd.errors.EmptyDataError:
                    print(f"Archive requests CSV is empty: {self.ARCHIVE_CSV_PATH}")
                    dummy_archive_df = pd.DataFrame(columns=self.expected_request_headers)
                    list_of_dfs.append(dummy_archive_df)
                except Exception as e:
                    print(f"Error reading archive requests CSV {self.ARCHIVE_CSV_PATH}: {e}")
            else:
                print(f"Archive requests CSV not found at: {self.ARCHIVE_CSV_PATH}")
                dummy_archive_df = pd.DataFrame(columns=self.expected_request_headers)
                list_of_dfs.append(dummy_archive_df)


            if not list_of_dfs: # If both are empty or not found
                QMessageBox.information(self, "No Requests", "You have no submitted requests yet or the request files are empty.")
                return 
            
            # Concatenate all loaded DataFrames
            # Use 'outer' join to keep all columns from all DataFrames, filling missing with NaN
            df_all_requests = pd.concat(list_of_dfs, ignore_index=True, sort=False) 
            # Fill NaN values in 'FormData' with empty strings to avoid issues later
            if 'FormData' in df_all_requests.columns:
                df_all_requests['FormData'] = df_all_requests['FormData'].fillna('')

            print(f"DEBUG (User_RM): Combined DataFrame BEFORE duplicate removal. Shape: {df_all_requests.shape}")
            # Remove duplicates based on RequestID (after standardization, this should be reliable)
            if 'RequestID' in df_all_requests.columns:
                initial_rows_combined = len(df_all_requests)
                df_all_requests.drop_duplicates(subset=['RequestID'], keep='first', inplace=True)
                if len(df_all_requests) < initial_rows_combined:
                    print(f"DEBUG (User_RM): Removed {initial_rows_combined - len(df_all_requests)} duplicate RequestIDs from combined DataFrame.")
                else:
                    print("DEBUG (User_RM): No duplicate RequestIDs found in combined DataFrame.")
            else:
                print("DEBUG (User_RM): 'RequestID' column not found in combined DataFrame, cannot check for duplicates.")

            print(f"DEBUG (User_RM): Combined DataFrame AFTER duplicate removal. Shape: {df_all_requests.shape}")
            print(f"DEBUG (User_RM): Combined DataFrame columns: {df_all_requests.columns.tolist()}")
            print(f"DEBUG (User_RM): First 5 rows of combined DataFrame:\n{df_all_requests.head()}")

            # Ensure MATRICULE_COLUMN_NAME exists before filtering
            if MATRICULE_COLUMN_NAME not in df_all_requests.columns:
                print(f"DEBUG (User_RM): ERROR! Column '{MATRICULE_COLUMN_NAME}' is MISSING in combined requests DataFrame.")
                QMessageBox.warning(self, "Data Error", f"Column '{MATRICULE_COLUMN_NAME}' (User Matricule) not found in requests CSVs. Cannot filter requests for user.")
                self.requests_table.setRowCount(0)
                return
            else:
                print(f"DEBUG (User_RM): Values in '{MATRICULE_COLUMN_NAME}' column (first 10, stripped):")
                print(df_all_requests[MATRICULE_COLUMN_NAME].astype(str).str.strip().head(10))
                print(f"DEBUG (User_RM): Unique values in '{MATRICULE_COLUMN_NAME}' column: {df_all_requests[MATRICULE_COLUMN_NAME].astype(str).str.strip().unique().tolist()}")
                print(f"DEBUG (User_RM): User matricule to filter by: '{self.user_matricule}' (type: {type(self.user_matricule)})")
                print(f"DEBUG (User_RM): Stripped user matricule for comparison: '{str(self.user_matricule).strip()}'")

            user_requests = df_all_requests[
                df_all_requests[MATRICULE_COLUMN_NAME].astype(str).str.strip() == str(self.user_matricule).strip()
            ].copy()
            
            print(f"DEBUG (User_RM): User requests DataFrame after filtering (head):\n{user_requests.head()}")
            print(f"DEBUG (User_RM): Number of user requests found AFTER FILTERING: {len(user_requests)}")

            # Debugging for Admin Name Merge - Modified to be robust for single-row DataFrames
            if ADMIN_MATRICULE_COLUMN_NAME in user_requests.columns and not user_requests.empty:
                admin_matricule_series = user_requests[ADMIN_MATRICULE_COLUMN_NAME].astype(str).str.strip()
                print(f"DEBUG (User_RM - Admin Name Merge): User requests '{ADMIN_MATRICULE_COLUMN_NAME}' column (first 5, stripped):\n{admin_matricule_series.head()}")
                print(f"DEBUG (User_RM - Admin Name Merge): Unique '{ADMIN_MATRICULE_COLUMN_NAME}' values in user_requests: {admin_matricule_series.unique().tolist()}")
            else:
                print(f"DEBUG (User_RM - Admin Name Merge): '{ADMIN_MATRICULE_COLUMN_NAME}' column not found or user_requests DataFrame is empty.")


            admin_names_df = self.load_admin_names()
            
            if not admin_names_df.empty and ADMIN_MATRICULE_COLUMN_NAME in user_requests.columns and not user_requests.empty:
                # Ensure both matricule columns are treated as strings and stripped before merging
                user_requests['adminMatricule_str_cleaned'] = user_requests[ADMIN_MATRICULE_COLUMN_NAME].astype(str).str.strip()
                admin_names_df['matricule_str_cleaned'] = admin_names_df['Matricule_Responsable'].astype(str).str.strip() 

                user_requests = pd.merge(
                    user_requests,
                    admin_names_df,
                    left_on='adminMatricule_str_cleaned', 
                    right_on='matricule_str_cleaned',
                    how='left'
                )
                user_requests.rename(columns={'Nom_Prenom_Responsable': 'Admin Name'}, inplace=True)
                
                # Drop the temporary and redundant matricule columns
                user_requests.drop(columns=['adminMatricule_str_cleaned', 'matricule_str_cleaned'], inplace=True, errors='ignore')
                
                print(f"DEBUG (User_RM - Admin Name Merge): User requests AFTER merge (first 5 rows with Admin Name):\n{user_requests[['RequestID', 'Status', ADMIN_MATRICULE_COLUMN_NAME, 'Admin Name']].head()}")
                print(f"DEBUG (User_RM - Admin Name Merge): Unique Admin Names after merge: {user_requests['Admin Name'].astype(str).unique().tolist()}")
                if 'Admin Name' in user_requests.columns and user_requests['Admin Name'].isnull().any():
                    print("DEBUG (User_RM - Admin Name Merge): WARNING! Some 'Admin Name' values are still NaN/empty after merge. Check for non-matching matricules.")
            else:
                user_requests['Admin Name'] = '' 
                print(f"DEBUG (User_RM - Admin Name Merge): Admin names DataFrame is empty or '{ADMIN_MATRICULE_COLUMN_NAME}' column is missing in user_requests, or user_requests is empty. 'Admin Name' will be empty.")
            # --- END DETAILED DEBUGGING PRINTS ---

            if 'DateSubmitted' in user_requests.columns:
                user_requests['DateSubmitted_obj'] = pd.to_datetime(user_requests['DateSubmitted'], errors='coerce') 
                user_requests = user_requests.sort_values(by='DateSubmitted_obj', ascending=False, na_position='last')
            else:
                user_requests['DateSubmitted_obj'] = pd.NaT 
                print("Warning: 'DateSubmitted' column not found for sorting.")


            self.requests_table.setRowCount(len(user_requests))

            for row_idx, row_series in user_requests.iterrows():
                request_date_obj = row_series.get('DateSubmitted_obj', pd.NaT)
                request_date = request_date_obj.strftime('%Y-%m-%d') if pd.notna(request_date_obj) else "N/A"
                
                form_type = row_series.get('FormType', "N/A") 
                request_status = row_series.get('Status', "Pending") 
                
                # CRITICAL FIX: Ensure admin_name is always a string for QTableWidgetItem
                admin_name = str(row_series.get('Admin Name', "N/A")) 
                
                decision_date = row_series.get('DecisionDate', "N/A") 
                request_id = row_series.get('RequestID', "N/A") 

                self.requests_table.setItem(row_idx, 0, QTableWidgetItem(request_date))
                self.requests_table.setItem(row_idx, 1, QTableWidgetItem(form_type))
                self.requests_table.setItem(row_idx, 2, QTableWidgetItem(request_status))
                self.requests_table.setItem(row_idx, 3, QTableWidgetItem(admin_name)) 
                self.requests_table.setItem(row_idx, 4, QTableWidgetItem(decision_date))
                self.requests_table.setItem(row_idx, 5, QTableWidgetItem(str(request_id)))

            self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.requests_table.horizontalHeader().setStretchLastSection(True)
            
            print(f"Successfully loaded {len(user_requests)} requests for user {self.user_matricule}.")

        except FileNotFoundError:
            self.requests_table.setRowCount(0)
            QMessageBox.information(self, "No Requests", "One or more requests CSV files were not found.")
        except pd.errors.EmptyDataError:
            self.requests_table.setRowCount(0)
            QMessageBox.information(self, "No Requests", "One of the requests CSV files is empty (contains only headers).")
        except Exception as e:
            error_msg = f"An unexpected error occurred while loading user requests: {str(e)}\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Error", error_msg)
            print(error_msg)

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    test_base_dir = r"C:\Users\sl3ag\Desktop\polina" 
    test_user_matricule = "09844926" 

    viewer = UserRequestsView(test_user_matricule, test_base_dir)
    viewer.show()
    sys.exit(app.exec())
