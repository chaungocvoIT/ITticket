from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import pyodbc
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change in production

# Database connection
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=VNCORPVNWKS1061;'
        'DATABASE=ITSupportDB;'
        'UID=sa;'
        'PWD=1234567'
    )
    return conn

# Auto-assignment thread
def auto_assign_tickets():
    while True:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TicketID, Severity, CreatedAt
            FROM SupportTickets
            WHERE Status = 'Open' AND AssignedTo IS NULL
        """)
        tickets = cursor.fetchall()
        for ticket in tickets:
            ticket_id, severity, created_at = ticket
            time_elapsed = datetime.now() - created_at
            threshold = {'Normal': 30, 'Urgent': 5, 'MissionCritical': 3}
            if time_elapsed > timedelta(minutes=threshold[severity]):
                cursor.execute("""
                    SELECT TOP 1 UserID FROM Users
                    WHERE Role = 'ITStaff' AND CampusID = (
                        SELECT CampusID FROM SupportTickets WHERE TicketID = ?
                    )
                """, ticket_id)
                it_staff = cursor.fetchone()
                if it_staff:
                    cursor.execute("""
                        UPDATE SupportTickets
                        SET AssignedTo = ?, AssignedAt = GETDATE(), Status = 'InProgress'
                        WHERE TicketID = ?
                    """, (it_staff[0], ticket_id))
                    conn.commit()
        conn.close()
        time.sleep(60)  # Check every minute

# Start auto-assignment thread
threading.Thread(target=auto_assign_tickets, daemon=True).start()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT UserID, Role, CampusID FROM Users WHERE Username = ? AND Password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['role'] = user[1]
            session['campus_id'] = user[2]
            print(f"Login successful: Username={username}, Role={user[1]}, CampusID={user[2]}")
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    role = session['role']
    user_id = session['user_id']
    campus_id = session['campus_id']
    
    # Debug: Fetch all tickets for comparison
    cursor.execute("""
        SELECT t.TicketID, t.Title, t.Status, t.Severity, t.CampusID, t.CreatedBy, c.CampusName
        FROM SupportTickets t
        LEFT JOIN Campuses c ON t.CampusID = c.CampusID
    """)
    all_tickets = cursor.fetchall()
    print(f"All tickets in SupportTickets table: {len(all_tickets)} tickets")
    for ticket in all_tickets:
        print(f"TicketID: {ticket.TicketID}, Title: {ticket.Title}, Status: {ticket.Status}, CampusID: {ticket.CampusID}, CreatedBy: {ticket.CreatedBy}, CampusName: {ticket.CampusName}")
    
    # Fetch tickets for the user
    if role == 'EndUser':
        cursor.execute("""
            SELECT t.TicketID, t.Title, t.Status, t.Severity, c.CampusName
            FROM SupportTickets t
            JOIN Campuses c ON t.CampusID = c.CampusID
            WHERE t.CreatedBy = ?
        """, user_id)
    elif role == 'ITStaff':
        cursor.execute("""
            SELECT t.TicketID, t.Title, t.Status, t.Severity, c.CampusName
            FROM SupportTickets t
            JOIN Campuses c ON t.CampusID = c.CampusID
            WHERE t.AssignedTo = ? OR t.Status = 'Open'
        """, user_id)
    elif role in ['Supervisor', 'Manager']:
        cursor.execute("""
            SELECT t.TicketID, t.Title, t.Status, t.Severity, c.CampusName
            FROM SupportTickets t
            JOIN Campuses c ON t.CampusID = c.CampusID
        """)
    
    tickets = cursor.fetchall()
    print(f"Tickets for {role} (UserID: {user_id}, CampusID: {campus_id}): {len(tickets)} tickets")
    for ticket in tickets:
        print(f"TicketID: {ticket.TicketID}, Title: {ticket.Title}, Status: {ticket.Status}, Campus: {ticket.CampusName}")
    
    cursor.execute("SELECT CampusID, CampusName FROM Campuses")
    campuses = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', tickets=tickets, role=role, campuses=campuses)

@app.route('/ticket/new', methods=['GET', 'POST'])
def new_ticket():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT CampusID, CampusName FROM Campuses")
    campuses = cursor.fetchall()
    
    if request.method == 'POST':
        if 'campus_id' not in request.form or not request.form['campus_id']:
            flash('Please select a campus')
            conn.close()
            return render_template('ticket_form.html', campuses=campuses)
        
        title = request.form['title']
        description = request.form['description']
        severity = request.form['severity']
        campus_id = request.form['campus_id']
        
        cursor.execute("SELECT CampusID FROM Campuses WHERE CampusID = ?", campus_id)
        if not cursor.fetchone():
            flash('Invalid campus selected')
            conn.close()
            return render_template('ticket_form.html', campuses=campuses)
        
        print(f"Creating ticket: Title={title}, CampusID={campus_id}, CreatedBy={session['user_id']}")
        
        cursor.execute("""
            INSERT INTO SupportTickets (Title, Description, Severity, Status, CampusID, CreatedBy)
            VALUES (?, ?, ?, 'Open', ?, ?)
        """, (title, description, severity, campus_id, session['user_id']))
        conn.commit()
        conn.close()
        flash('Ticket created successfully')
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('ticket_form.html', campuses=campuses)

@app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
def ticket_detail(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, c.CampusName 
        FROM SupportTickets t
        JOIN Campuses c ON t.CampusID = c.CampusID
        WHERE t.TicketID = ?
    """, ticket_id)
    ticket = cursor.fetchone()
    cursor.execute("SELECT * FROM TicketActions WHERE TicketID = ?", ticket_id)
    actions = cursor.fetchall()
    cursor.execute("SELECT UserID, Username FROM Users WHERE Role = 'ITStaff' AND CampusID = ?", ticket.CampusID)
    it_staff = cursor.fetchall()
    
    if request.method == 'POST':
        if 'action_type' not in request.form or not request.form['action_type']:
            flash('Please select an action type')
            conn.close()
            return render_template('ticket_detail.html', ticket=ticket, actions=actions, it_staff=it_staff, role=session['role'])
        
        action_type = request.form['action_type']
        action_description = request.form['action_description']
        
        cursor.execute("""
            INSERT INTO TicketActions (TicketID, UserID, ActionType, ActionDescription)
            VALUES (?, ?, ?, ?)
        """, (ticket_id, session['user_id'], action_type, action_description))
        
        if action_type == 'Close':
            cursor.execute("UPDATE SupportTickets SET Status = 'Closed', ClosedAt = GETDATE() WHERE TicketID = ?", ticket_id)
        elif action_type == 'Fix':
            cursor.execute("UPDATE SupportTickets SET Status = 'Resolved' WHERE TicketID = ?", ticket_id)
        elif action_type in ['Escalation', 'AdditionalSupport']:
            if ticket.Status == 'Open':
                cursor.execute("UPDATE SupportTickets SET Status = 'InProgress' WHERE TicketID = ?", ticket_id)
        elif action_type == 'Assign' and session['role'] in ['Supervisor', 'ITStaff']:
            assigned_to = request.form.get('assigned_to')
            if assigned_to:
                cursor.execute("""
                    UPDATE SupportTickets 
                    SET AssignedTo = ?, AssignedAt = GETDATE(), Status = 'InProgress' 
                    WHERE TicketID = ?
                """, (assigned_to, ticket_id))
        
        conn.commit()
        conn.close()
        flash('Action recorded')
        return redirect(url_for('ticket_detail', ticket_id=ticket_id))
    
    conn.close()
    return render_template('ticket_detail.html', ticket=ticket, actions=actions, it_staff=it_staff, role=session['role'])

@app.route('/kb/search', methods=['GET', 'POST'])
def kb_search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    search_term = request.form.get('search_term', '') if request.method == 'POST' else ''
    query = "SELECT KBID, Title, Content FROM KnowledgeBase WHERE Title LIKE ? OR Content LIKE ?"
    cursor.execute(query, (f'%{search_term}%', f'%{search_term}%'))
    kb_entries = cursor.fetchall()
    conn.close()
    return render_template('kb_search.html', kb_entries=kb_entries, search_term=search_term)

@app.route('/kb/new', methods=['GET', 'POST'])
def new_kb():
    if 'user_id' not in session or session['role'] not in ['ITStaff', 'Supervisor', 'Manager']:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO KnowledgeBase (Title, Content, CreatedBy, CampusID)
            VALUES (?, ?, ?, ?)
        """, (title, content, session['user_id'], session['campus_id']))
        conn.commit()
        conn.close()
        flash('Knowledge base entry created')
        return redirect(url_for('kb_search'))
    return render_template('kb_form.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)