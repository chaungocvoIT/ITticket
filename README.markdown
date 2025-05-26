# IT Support Ticketing System

This is a simple IT Support Ticketing System built with Python, Flask, and MS SQL Server. It supports multiple campuses, ticket assignment, tracking, escalation, and a searchable knowledge base. The system is mobile-responsive and runs on localhost.
#  Video for instructions:
https://youtu.be/M5rmfejwS4k

## Requirements
- Python 3.8+
- Microsoft SQL Server (running on local computer)
- SQL Server Management Studio (SSMS)
- Windows OS

## Setup Instructions

1. **Create the Database**
   - Open SQL Server Management Studio (SSMS).
   - Connect to the SQL Server instance `local` using username for example `sa` and password `1234567`
   - Open the file `create_database.sql` from the project folder.
   - Execute the script to create the `ITSupportDB` database and tables.

2. **Set Up the Project Folder**
   - Create a folder at `C:\PythonProjects\ITTicket`.
   - Copy all project files into this folder, maintaining the structure:
     ```
     ITTicket/
     ├── app.py
     ├── requirements.txt
     ├── static/
     │   ├── css/
     │   │   └── styles.css
     │   └── js/
     │       └── scripts.js
     ├── templates/
     │   ├── base.html
     │   ├── login.html
     │   ├── dashboard.html
     │   ├── ticket_form.html
     │   ├── ticket_detail.html
     │   ├── kb_search.html
     │   └── kb_form.html
     └── README.md
     ```

3. **Install Python Dependencies**
   - Open a command prompt and navigate to `C:\PythonProjects\ITTicket`.
   - Run the following command to create a virtual environment:
     ```
     python -m venv venv
     ```
   - Activate the virtual environment:
     ```
     venv\Scripts\activate
     ```
   - Install dependencies:
     ```
     pip install -r requirements.txt
     ```

4. **Add Sample Data**
   - In SSMS, run the following SQL to add sample campuses and users:
     ```sql
     USE ITSupportDB;
     INSERT INTO Campuses (CampusName) VALUES ('Campus A'), ('Campus B');
     INSERT INTO Users (Username, Password, Role, CampusID, Email) VALUES
         ('user1', 'password1', 'EndUser', 1, 'user1@example.com'),
         ('itstaff1', 'password1', 'ITStaff', 1, 'itstaff1@example.com'),
         ('supervisor1', 'password1', 'Supervisor', 1, 'supervisor1@example.com'),
         ('manager1', 'password1', 'Manager', 1, 'manager1@example.com');
     ```

5. **Run the Application**
   - In the command prompt, ensure the virtual environment is activated.
   - Run the Flask app:
     ```
     python app.py
     ```
   - Open a web browser and navigate to `http://localhost:5000`.

6. **Using the System**
   - Log in with a username and password (e.g., `user1`/`password1` for an EndUser).
   - **EndUser**: Create tickets, view ticket status, confirm closure, search knowledge base.
   - **ITStaff**: View and assign themselves to tickets, add fixes/comments, contribute to knowledge base.
   - **Supervisor**: Assign IT staff to tickets, view all tickets, manage knowledge base.
   - **Manager**: View all tickets and campuses, manage knowledge base.
   - The system auto-assigns tickets after 30min (Normal), 5min (Urgent), or 3min (MissionCritical).

## Notes
- The system is mobile-responsive, tested on various screen sizes.
- Passwords are stored in plain text for simplicity; in production, use hashing (e.g., bcrypt).
- The application runs on `localhost:5000` by default.
