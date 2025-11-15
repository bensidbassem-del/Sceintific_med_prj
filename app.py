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
    
    # Create admin user with hashed password
    admin_hash = generate_password_hash('admin')
    print(f"Admin hash: {admin_hash}")  # Debug print
    
    cur.execute("INSERT OR IGNORE INTO users (username, email, password_hash, role) VALUES (?,?, ?, ?)",
                ('admin','admin@example.com', admin_hash, 'super_admin'))
    
    
    con.commit()
    
    # Verify the user was created
    cur.execute("SELECT * FROM users WHERE email=?", ('admin@example.com',))
    user = cur.fetchone()
    print(f"User in database: {user}")  # Debug print
    cur.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_title TEXT,event_description TEXT, event_start_date DATE,event_end_date DATE, event_location TEXT, event_theme TEXT)")
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
        
        if user[5]:  
            return render_template('superadmindashboard.html')
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
    con = sqlite3.connect("database.db")
    cur=con.cursor()
    cur.execute("INSERT INTO users (username,email,dateofbirth,password_hash,role)VALUES (?,?,?,?,?)",(username,email,dateofbirth,password,role) )
    con.commit()
    con.close()
    if role == 'admin':
        return redirect(url_for('admindashboard'))
    else:
        if role == 'superadmin':
            return redirect(url_for('superadm'))
        else:
            return redirect(url_for('userdashboard.html'))
    #return render_template('welcome.html', username=username, email=email, dateofbirth=dateofbirth, password=password)
@app.route('/adminpage')
def admindashboard():
    return render_template('admindashboard.html')
@app.route('/superadm')
def superadm():
    return render_template('superadmindashboard.html')

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

@app.route('/delete',methods=['GET'])
def delete():
    email=request.args.get('email')    
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
        role=session.get('role')
        if role != 'admin':
            return "Unauthorized", 403
        
        event_title=request.form.get('event_title')
        event_description=request.form.get('event_description')
        event_start_date=request.form.get('event_start_date')
        event_end_date=request.form.get('event_end_date')
        event_location=request.form.get('event_location')
        event_theme=request.form.get('event_theme')
        if not all([event_title, event_description, event_start_date, event_end_date, event_location, event_theme]):
           return render_template('create_event.html', error="All fields are required")
        con = sqlite3.connect("database.db")
        cur=con.cursor()
        cur.execute("INSERT INTO events ( event_title,event_description, event_start_date,event_end_date, event_location, event_theme)VALUES (?,?,?,?,?,?)",(event_title,event_description,event_start_date,event_end_date,event_location,event_theme) )
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('checkin'))
if __name__ == '__main__':
    setup_database()
    app.run(debug=True,host="0.0.0.0",port=5000)

