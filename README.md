# PyQt6 Internal Request Management System

A desktop application built with Python and PyQt6 for managing internal company requests. The system provides separate interfaces for standard users to submit requests and for administrators to review and process them.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
  - [User Features](#user-features)
  - [Admin Features](#admin-features)
- [Application Flow](#application-flow)
- [Project Structure](#project-structure)
- [Data Schema](#data-schema)
  - [`requests_pending.csv`](#requests_pendingcsv)
  - [`Table user.csv`](#table-usercsv)
  - [`Table user.xlsx`](#table-userxlsx)
- [Setup and Installation](#setup-and-installation)
- [How to Run](#how-to-run)
- [Dependencies](#dependencies)

## Overview

This application streamlines the process of submitting and managing internal corporate forms. It features a role-based access system that distinguishes between regular users and administrators.

- **Users** can log in, choose from a variety of request forms (e.g., access requests, hardware requests), fill them out, and submit them. They can also view a history of their own submissions and see the current status (Pending, Approved, Rejected).
- **Administrators** have a dashboard where they can view all pending requests from all users. They can inspect the full details of each request and approve or reject it with a single click.

All data is managed through local CSV and Excel files, making the system self-contained and easy to deploy in a shared folder environment.

## Features

### User Features

*   **Secure Login**: Users log in using their unique employee ID (`matricule`).
*   **Dynamic Form Loader**: A dropdown menu allows users to select from multiple types of request forms. The corresponding UI is loaded dynamically into the main window.
*   **Form Submission**: Filled forms are saved as a new request with a unique ID, timestamp, and user information.
*   **View My Requests**: Users can open a separate window to view a list of all their past and pending requests.
*   **Status Tracking**: The request history view shows the current status of each submission and, once decided, the name of the administrator who handled it and the date of the decision.

### Admin Features

*   **Admin Login**: Administrators log in using their own `matricule`, which is verified against a separate list.
*   **Central Dashboard**: A comprehensive table displays all pending requests from every user.
*   **Request Processing**: Each request in the table has "Accept" and "Reject" buttons for quick processing. The decision, admin's ID, and decision date are automatically recorded.
*   **Detailed View**: A "View Details" button opens a dialog that displays all the information from the original submitted form, ensuring the admin has all the context needed to make a decision.
*   **Persistent Changes**: All administrative actions (approvals/rejections) are immediately saved back to the central `requests_pending.csv` file.

## Application Flow

1.  **Login**: The application starts with `login.py`. The user enters their matricule.
2.  **Authentication**: The system checks the matricule against `Table user.xlsx` (for admins) and `Table user.csv` (for users).
3.  **Role-Based Routing**:
    *   If the matricule is identified as an **admin**, the `AdminWindow` from `admin.py` is opened.
    *   If the matricule is identified as a **user**, the `MainUserWindow` from `user.py` is opened.
    *   If the matricule is not found, an error is displayed.
4.  **User Actions**:
    *   The user selects a form, fills it out, and submits it. The data is appended to `requests_pending.csv`.
    *   The user can open the `UserRequestsView` (`user_requests_manager.py`) to see their history, which is read from the `requests_pending.csv` and `requests_archive.csv` files.
5.  **Admin Actions**:
    *   The admin views all data from `requests_pending.csv`.
    *   When an admin approves or rejects a request, the corresponding row in `requests_pending.csv` is updated with the new status, the admin's matricule, and the date.

## Project Structure

The project is organized into directories for the application logic, UI files, styles, and data.

Repo Directory
│  
├── login.py  # Application entry point, handles authentication.  
├── user.py  # Main window for standard users to create requests.  
├── admin.py  # Main window for administrators to manage requests.  
├── user_requests_manager.py  # UI for users to view their request history.  
│  
├── Table user.csv  # Data file with user matricules and names.  
├── Table user.xlsx  # Data file with administrator matricules.  
├── requests_pending.csv  # Central database for all new and pending requests.  
├── requests_archive.csv  # (Optional/Future) For storing completed requests.  
│  
├── ui/  
│   ├── login.ui  
│   ├── user.ui  
│   ├── admin.ui  
│   ├── my_requests_view.ui  
│   ├── grauve.ui  # Specific form UIs...  
│   ├── cle3g.ui  
│   ├── internet.ui  
│   ├── fishe.ui  
│   └── externaldrive.ui  
│  
└── styles/  
    ├── app_style.qss  # Global stylesheet for the application.  
    └── admin_details_style.qss  # Specific style for the request details dialog.  


**Note:** The `BASE_DIR` variable in all `.py` files must be correctly set to the project's root folder path (e.g., `C:\Users\sl3ag\Desktop\polina`).

## Data Schema

For the application to function correctly, the data files must contain specific columns.

### `requests_pending.csv`
This file is the core database. It is created and updated by the application.
*   **Core Columns**:
    *   `RequestID`: Unique UUID for the request.
    *   `FormType`: The name of the form that was submitted (e.g., "Fiche d'engagement clé 3g").
    *   `DateSubmitted`: The date the request was made (`YYYY-MM-DD`).
    *   `UserMatricule`: The matricule of the user who made the request.
    *   `Status`: The current state of the request (`Pending`, `Approved`, `Rejected`).
    *   `AdminMatricule`: The matricule of the admin who processed the request.
    *   `DecisionDate`: The date the decision was made (`YYYY-MM-DD`).
*   **Form-Specific Columns**: The file also contains a column for every single field from every possible form (e.g., `cle3g_nomPrenom_lineEdit`, `gravure_motif_textEdit`, etc.).

### `Table user.csv`
This file contains information about all standard users and their managers (who are the admins).
*   `matricule`: The employee ID for a standard user.
*   `Matricule_Responsable`: The employee ID for the user's manager/admin.
*   `Nom_Prenom_Responsable`: The full name of the user's manager/admin.

### `Table user.xlsx`
This file contains the list of all users who can log in as administrators.
*   `Matricule_responsable`: The employee ID for an administrator.

## Setup and Installation

1.  **Prerequisites**:
    *   Python 3.x
    *   `pip` package installer

2.  **Clone/Download**: Place all project files in a single directory as shown in the [Project Structure](#project-structure).

3.  **Install Dependencies**: Open a terminal or command prompt and run the following command to install the required Python libraries:
    ```sh
    pip install PyQt6 pandas openpyxl
    ```

4.  **Verify Paths**: Open each `.py` file and ensure the `BASE_DIR` variable at the top is set to the correct absolute path of your project folder.
    ```python
    # Example from user.py
    self.BASE_DIR = r"C:\Users\sl3ag\Desktop\polina"
    ```

5.  **Prepare Data Files**: Ensure `Table user.csv` and `Table user.xlsx` exist in the `BASE_DIR` and are populated with the correct column headers and data.

## How to Run

To start the application, execute the `login.py` script from your terminal:

```sh
python login.py
```
This will launch the login window. You can then enter a valid user or admin matricule from your data files to proceed.

## Dependencies

- **PyQt6**: The library used for the graphical user interface.
- **pandas**: Used for all data manipulation, including reading from and writing to CSV and Excel files.
- **openpyxl**: Required by pandas to handle .xlsx Excel files.
