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