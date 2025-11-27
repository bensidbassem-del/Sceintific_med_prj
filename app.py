from flask import Flask, render_template,request,url_for,redirect
import sqlite3
from werkzeug.security import check_password_hash,generate_password_hash
from flask import session
app = Flask(__name__)
app.secret_key = 'bassem'
@app.route('/')
def accueil():
    return render_template('login.html')
 # def get_db_connection():
   # conn = sqlite3.connect('database.db')
    #conn.row_factory = sqlite3.Row
   # return conn
def setup_database():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,    
            email TEXT UNIQUE NOT NULL,
            dateofbirth DATE,    
            password_hash TEXT NOT NULL,
            role TEXT  NOT NULL,  -- 'super_admin', 'admin', 'participant', 'author', 'committee', 'speaker', 'animator',
            institution TEXT,
            research_domain TEXT,
            biography TEXT
        )
    """)
    cur.execute("""CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 event_title TEXT,event_description TEXT,
                 event_start_date DATE,event_end_date DATE,
                 event_location TEXT,
                 event_theme TEXT,
                 organiser_id INTEGER,
                 status TEXT DEFAULT 'upcoming',
                 FOREIGN KEY (organiser_id) REFERENCES users (id))""")
    cur.execute(""" 
    CREATE TABLE IF NOT EXISTS Inscription (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_inscription TEXT,
    statut_paiement TEXT,
    date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_user INTEGER,
    id_evenement INTEGER
      )"""  
    )
    cur.execute("""
      CREATE TABLE IF NOT EXISTS Proposition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT,
    resume TEXT,
    type TEXT,
    date_soumission DATETIME DEFAULT CURRENT_TIMESTAMP,
    statut TEXT,
    id_user INTEGER,
    id_evenement INTEGER
     )"""
    )
    cur.execute("""
     CREATE TABLE IF NOT EXISTS Evaluation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_proposition INTEGER,
    id_evaluateur INTEGER,
    note_qualite INTEGER,
    note_originalite INTEGER,
    commentaires TEXT,
    recommandation TEXT,
    date_evaluation DATETIME DEFAULT CURRENT_TIMESTAMP  )
    """)
    #Committee table

    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_committee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    user_id INTEGER,
    FOREIGN KEY(event_id) REFERENCES events(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
    )
   """)

#Speakers table

    cur.execute("""
     CREATE TABLE IF NOT EXISTS speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    name TEXT NOT NULL,
    biography TEXT,
    topic TEXT,
    FOREIGN KEY(event_id) REFERENCES events(id)
    )
     """)

    # Create admin user with hashed password
    admin_hash = generate_password_hash('admin')
    print(f"Admin hash: {admin_hash}")  # Debug print
    
    cur.execute("INSERT OR IGNORE INTO users (username, email, password_hash, role) VALUES (?,?, ?, ?)",
                ('admin','admin@example.com', admin_hash, 'super_admin'))
    
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_title TEXT,
            event_description TEXT,
            event_start_date DATE,
            event_end_date DATE,
            event_location TEXT,
            event_theme TEXT,
            organiser_id INTEGER,
            status TEXT DEFAULT 'upcoming',
            FOREIGN KEY (organiser_id) REFERENCES users (id)
        )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_committee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    user_id INTEGER,
    FOREIGN KEY(event_id) REFERENCES events(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

    cur.execute("""
CREATE TABLE IF NOT EXISTS speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    name TEXT NOT NULL,
    biography TEXT,
    topic TEXT,
    FOREIGN KEY(event_id) REFERENCES events(id)
)
""")

#Committee table
cur.execute("""
CREATE TABLE IF NOT EXISTS event_committee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    user_id INTEGER,
    FOREIGN KEY(event_id) REFERENCES events(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

#Speakers table
cur.execute("""
CREATE TABLE IF NOT EXISTS speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    name TEXT NOT NULL,
    biography TEXT,
    topic TEXT,
    FOREIGN KEY(event_id) REFERENCES events(id)
)
""")
    
    # Verify the user was created
    cur.execute("SELECT * FROM users WHERE email=?", ('admin@example.com',))
    user = cur.fetchone()
    print(f"User in database: {user}")  # Debug print
    
    con.commit()
    con.close()

@app.route('/checkin', methods=[ 'POST'])
def checkin():
    email = request.form.get('idd')
    password = request.form.get('password')
    if not email or not password:
        return render_template('login.html', error="All fields required")
    
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    con.close()
    
    if user and check_password_hash(user[4], password):  
        session['user_id'] = user[0]
        session['email'] = user[2]
        session['role'] = user[5]  
        
        if user[5]=='super_admin':  
            return render_template('superadmindashboard.html')
        else:
            if user[5]=='admin':  
                return redirect(url_for('admindashboard'))
            else:
             return redirect(url_for('userpage'))
    else:
        return render_template('login.html', error="Invalid credentials")

  
   
@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/register', methods=['POST'])
def register():
    username=request.form.get('username')
    email=request.form.get('email')
    dateofbirth=request.form.get('dateofbirth')
    password=request.form.get('password')
    password=generate_password_hash(password)
    role=request.form.get('role')
    institution=request.form.get('institution')
    con = sqlite3.connect("database.db")
    cur=con.cursor()
    cur.execute("INSERT INTO users (username,email,dateofbirth,password_hash,role,institution)VALUES (?,?,?,?,?,?)",(username,email,dateofbirth,password,role,institution) )
    con.commit()
    con.close()
    if role == 'admin':
        return redirect(url_for('admindashboard'))
    else:
        if role == 'superadmin':
            return redirect(url_for('superadm'))
        else:
            return redirect(url_for('userpage'))
    #return render_template('welcome.html', username=username, email=email, dateofbirth=dateofbirth, password=password)
@app.route('/adminpage')
def admindashboard():
    return render_template('admindashboard.html')
@app.route('/superadm')
def superadm():
    return render_template('superadmindashboard.html')
@app.route('/userpage')
def userpage():
    return render_template('userdashboard.html')

@app.route('/userdetails')
def userdetails():
    email=session.get('email')
    con = sqlite3.connect("database.db")
    cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE email=?",(email,))
    data=cur.fetchall()
    con.close()
    return render_template('userdashboard.html', data=data)

@app.route('/find',methods=['GET'])
def find():
    email=request.args.get('email')
    con = sqlite3.connect("database.db")
    cur=con.cursor()
    cur.execute("SELECT * FROM users WHERE email=?",(email,))
    data=cur.fetchall()
    con.close()
    return render_template('showuser.html', data=data)

@app.route('/deleteuser',methods=['POST'])
def delete():
    email=request.form.get('email')    
    con = sqlite3.connect("database.db")
    cur=con.cursor()
    cur.execute("DELETE FROM users WHERE email=?",(email,))
    con.commit()
    return redirect(url_for('superadm'))

@app.route('/question',methods=['GET'])
def question():
    eid=request.args.get('eid')
    return render_template('question.html', eid=eid)
@app.route('/create_event',methods=['GET','POST'])
def create_event():
    if request.method=='GET':
        return render_template('create_event.html')
    else:
        event_title=request.form.get('event_title')
        event_description=request.form.get('event_description')
        event_start_date=request.form.get('event_start_date')
        event_end_date=request.form.get('event_end_date')
        event_location=request.form.get('event_location')
        event_theme=request.form.get('event_theme')
        role=session.get('role')
        if role != 'admin':
            return "Unauthorized", 403
        organiser_id=session.get('user_id')
        if not all([event_title, event_description, event_start_date, event_end_date, event_location, event_theme]):
           return render_template('create_event.html', error="All fields are required")
        con = sqlite3.connect("database.db")
        cur=con.cursor()
        cur.execute("INSERT INTO events ( event_title,event_description, event_start_date,event_end_date, event_location, event_theme,organiser_id)VALUES (?,?,?,?,?,?,?)",(event_title,event_description,event_start_date,event_end_date,event_location,event_theme,organiser_id) )
        con.commit()
        return redirect(url_for('admindashboard'))
@app.route('/show_events',methods=['GET'])
def show_events():
    con = sqlite3.connect("database.db")
    cur=con.cursor()
    cur.execute("SELECT * FROM events")
    data=cur.fetchall()
    con.close()
    return render_template('show_events.html', data=data)    
@app.route('/deleteevent',methods=['POST'])
def deleteevent():
    id=request.form.get('id')    
    con = sqlite3.connect("database.db")
    cur=con.cursor()
    cur.execute("DELETE FROM events WHERE id=?",(id,))
    con.commit()
    return redirect(url_for('admindashboard'))

@app.route('/event_details')
def event_details():
    event_id = request.args.get('id')
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cur.fetchone()

    # get speakers
    cur.execute("SELECT name, topic FROM speakers WHERE event_id=?", (event_id,))
    speakers = cur.fetchall()

    # get committee members
    cur.execute("""
        SELECT u.username, u.email 
        FROM users u 
        JOIN event_committee ec ON u.id = ec.user_id
        WHERE ec.event_id=?
    """, (event_id,))
    committee = cur.fetchall()
    con.close()
    return render_template('event_details.html', event=event, speakers=speakers, committee=committee)

#update_event()
@app.route('/update_event', methods=['GET','POST'])
def update_event():
    event_id = request.args.get('id')

    if request.method == 'GET':
        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM events WHERE id=?", (event_id,))
        event = cur.fetchone()
        con.close()
        return render_template('update_event.html', event=event)

    else:
        title = request.form.get('event_title')
        description = request.form.get('event_description')
        start_date = request.form.get('event_start_date')
        end_date = request.form.get('event_end_date')
        location = request.form.get('event_location')
        theme = request.form.get('event_theme')
        status = request.form.get('status')

        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("""
            UPDATE events 
            SET event_title=?, event_description=?, event_start_date=?, event_end_date=?, event_location=?, event_theme=?, status=?
            WHERE id=?
        """, (title, description, start_date, end_date, location, theme, status, event_id))
        con.commit()
        con.close()

return redirect(url_for('show_events'))

#Add Committee Member
@app.route('/add_committee_member', methods=['POST'])
def add_committee_member():
    user_email = request.form.get('email')
    event_id = request.form.get('event_id')

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    # find user id
    cur.execute("SELECT id FROM users WHERE email=?", (user_email,))
    user = cur.fetchone()
    if not user:
    con.close()
    return "User not found"
    user_id = user[0]
    # insert link
    cur.execute("INSERT INTO event_committee (event_id, user_id) VALUES (?,?)", (event_id, user_id))
    con.commit()
    con.close()
    return redirect(url_for('event_details', id=event_id))

#Add Speaker
@app.route('/add_speaker', methods=['POST'])
def add_speaker():
    event_id = request.form.get('event_id')
    name = request.form.get('name')
    biography = request.form.get('biography')
    topic = request.form.get('topic')

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
        INSERT INTO speakers (event_id, name, biography, topic)
        VALUES (?, ?, ?, ?)
    """, (event_id, name, biography, topic))

    con.commit()
    con.close()

    return redirect(url_for('event_details', id=event_id))

#Show speakers for 1 event
@app.route('/speakers')
def show_speakers():
 event_id = request.args.get('event_id')

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM speakers WHERE event_id=?", (event_id,))
    speakers = cur.fetchall()
    con.close()

    return render_template('speakers.html', speakers=speakers)

#Upcoming events
@app.route('/events/upcoming')
def show_upcoming_events():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM events WHERE status='upcoming'")
    events = cur.fetchall()
    con.close()
    return render_template('show_events.html', data=events)

#Archived events
@app.route('/events/archived')
def show_archived_events():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM events WHERE status='archived'")
    events = cur.fetchall()
    con.close()
    return render_template('show_events.html', data=events)

    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('checkin'))
#event_details()

@app.route('/event_details')
def event_details():
    event_id = request.args.get('id')

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cur.fetchone()

    # get speakers
    cur.execute("SELECT name, topic FROM speakers WHERE event_id=?", (event_id,))
    speakers = cur.fetchall()

    # get committee members
    cur.execute("""
        SELECT u.username, u.email 
        FROM users u 
        JOIN event_committee ec ON u.id = ec.user_id
        WHERE ec.event_id=?
    """, (event_id,))
    committee = cur.fetchall()

    con.close()

    return render_template('event_details.html', event=event, speakers=speakers, committee=committee)
#update_event()

@app.route('/update_event', methods=['GET','POST'])
def update_event():
    event_id = request.args.get('id')

    if request.method == 'GET':
        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM events WHERE id=?", (event_id,))
        event = cur.fetchone()
        con.close()
        return render_template('update_event.html', event=event)

    else:
        title = request.form.get('event_title')
        description = request.form.get('event_description')
        start_date = request.form.get('event_start_date')
        end_date = request.form.get('event_end_date')
        location = request.form.get('event_location')
        theme = request.form.get('event_theme')
        status = request.form.get('status')

        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("""
            UPDATE events 
            SET event_title=?, event_description=?, event_start_date=?, event_end_date=?, event_location=?, event_theme=?, status=?
            WHERE id=?
        """, (title, description, start_date, end_date, location, theme, status, event_id))
        con.commit()
        con.close()

        return redirect(url_for('show_events'))

#Add Committee Member

@app.route('/add_committee_member', methods=['POST'])
def add_committee_member():
    user_email = request.form.get('email')
    event_id = request.form.get('event_id')

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    # find user id
    cur.execute("SELECT id FROM users WHERE email=?", (user_email,))
    user = cur.fetchone()

    if not user:
        con.close()
        return "User not found"

    user_id = user[0]

    # insert link
    cur.execute("INSERT INTO event_committee (event_id, user_id) VALUES (?,?)", (event_id, user_id))
    con.commit()
    con.close()

    return redirect(url_for('event_details', id=event_id))

#Add Speaker

@app.route('/add_speaker', methods=['POST'])
def add_speaker():
    event_id = request.form.get('event_id')
    name = request.form.get('name')
    biography = request.form.get('biography')
    topic = request.form.get('topic')

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
        INSERT INTO speakers (event_id, name, biography, topic)
        VALUES (?, ?, ?, ?)
    """, (event_id, name, biography, topic))

    con.commit()
    con.close()

    return redirect(url_for('event_details', id=event_id))

#Show speakers for 1 event

@app.route('/speakers')
def show_speakers():
    event_id = request.args.get('event_id')

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM speakers WHERE event_id=?", (event_id,))
    speakers = cur.fetchall()
    con.close()

    return render_template('speakers.html', speakers=speakers)

#Upcoming events

@app.route('/events/upcoming')
def show_upcoming_events():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM events WHERE status='upcoming'")
    events = cur.fetchall()
    con.close()
    return render_template('show_events.html', data=events)

#Archived events

@app.route('/events/archived')
def show_archived_events():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM events WHERE status='archived'")
    events = cur.fetchall()
    con.close()
    return render_template('show_events.html', data=events)

if __name__ == '__main__':
    setup_database()
    app.run(debug=True,host="0.0.0.0",port=5000)

