from flask import Flask, render_template,request,url_for,redirect
import sqlite3
from werkzeug.security import check_password_hash,generate_password_hash
from flask import session
import os 
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import random
app = Flask(__name__)
app.secret_key = 'bassem'

UPLOAD_FOLDER = 'upload/proposals' 
ALLOWED_EXTENSIONS = {'pdf'} 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
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
      CREATE TABLE IF NOT EXISTS Proposition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT,
    resume TEXT,
    type TEXT,
    keywords TEXT,            
    date_soumission DATETIME DEFAULT CURRENT_TIMESTAMP,
    statut TEXT,
    id_user INTEGER,
    id_evenement INTEGER
     )"""
    )
    cur.execute(""" CREATE TABLE IF NOT EXISTS Evaluation ( id INTEGER PRIMARY KEY AUTOINCREMENT,
                 id_proposition INTEGER, 
                id_evaluateur INTEGER,
                 note_pertinence INTEGER, 
                note_qualite INTEGER, 
                note_originalite INTEGER, 
                commentaires TEXT, recommandation TEXT, 
                date_evaluation DATETIME DEFAULT CURRENT_TIMESTAMP ) """)
    
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
 #participant registrations
    cur.execute("""
     CREATE TABLE IF NOT EXISTS Inscription (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_inscription TEXT,
    statut_paiement TEXT DEFAULT 'pending',
    date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_user INTEGER,
    id_evenement INTEGER,
    badge_generated BOOLEAN DEFAULT FALSE,
    badge_code TEXT
)
    """)
    
    #une table qui relie une proposition et un evaluateur
    cur.execute("""
CREATE TABLE IF NOT EXISTS ReviewerAssignment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_proposition INTEGER,
    id_reviewer INTEGER,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_proposition) REFERENCES Proposition(id),
    FOREIGN KEY(id_reviewer) REFERENCES users(id)
)
""")

 # Sessions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT NOT NULL,
    horaire DATETIME,
    salle TEXT,
    id_evenement INTEGER,
    responsable INTEGER,
    FOREIGN KEY(id_evenement) REFERENCES events(id),
    FOREIGN KEY(responsable) REFERENCES users(id)
)
""")

# Link:which proposition in wechmn session
    cur.execute("""
    CREATE TABLE IF NOT EXISTS SessionProposition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_session INTEGER,
    id_proposition INTEGER,
    FOREIGN KEY(id_session) REFERENCES Session(id),
    FOREIGN KEY(id_proposition) REFERENCES Proposition(id)
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
            return render_template('superadmindashboard.html', user=user)
        else:
            if user[5]=='admin':  
                return render_template('admindashboard.html', user=user)
            else:
             return render_template('userdashboard.html', user=user)
    else:
        return render_template('login.html',error="Invalid credentials")
   
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
    email = session.get('email')
    
    if not email:
        return redirect(url_for('accueil')) # Rediriger si l'email n'est pas dans la session
        
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    # On sélectionne les champs spécifiques
    cur.execute("SELECT username, email, dateofbirth, role, institution, research_domain, biography FROM users WHERE email=?", (email,))
    user_data = cur.fetchone() # Utilisez fetchone() car l'email est unique
    con.close()
    
    if user_data:
        # Assigner les valeurs récupérées à des variables nommées pour Jinja
        username = user_data[1]
        email = user_data[2]
        dateofbirth = user_data[3]
        role = user_data[5]
       
        
        return render_template('userdashboard.html', 
                               username=username, 
                               email=email, 
                               dateofbirth=dateofbirth, 
                               role=role,
                               # Ajoutez d'autres champs si nécessaire
                              )
    else:
        # Gérer le cas où l'utilisateur n'est pas trouvé
        return "Utilisateur non trouvé", 404

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
   if session.get('role')=='super_admin':
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
   if session.get('role')=='admin':
    id=request.form.get('id')    
    con = sqlite3.connect("database.db")
    cur=con.cursor()
    cur.execute("DELETE FROM events WHERE id=?",(id,))
    con.commit()
    return redirect(url_for('admindashboard'))
   else:
       return "Vous n'etes pas autorisés"

@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')
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
@app.route('/submission_form', methods=['GET', 'POST'])
def submission_form():
    # 1. Si c'est un POST (le formulaire a été envoyé pour enregistrement)
    if request.method == 'POST':
        if session.get('role') == 'author':
            titre = request.form.get('titre')
            mot_cles = request.form.get('keywords')  
            type_prop = request.form.get('type')
            id_user = session.get('user_id')
            id_evenement = request.form.get('event_id') 
            
            if 'resume_file' not in request.files:
                # Gérer le cas où le champ est manquant (devrait être rare si 'required' est dans le HTML)
                return render_template('submission_form.html', event_id=id_evenement, error="Fichier de résumé manquant.")
            file = request.files['resume_file']
            if file.filename == '':
                print("rien n'etait selectionne ")
                return render_template('submission_form.html', event_id=id_evenement, error="Veuillez sélectionner un fichier.")

            file_path_for_db = None 
            
            if file and allowed_file(file.filename):
                print("On va securiser le fichier")
                filename = secure_filename(file.filename)
                
                unique_filename = f"{id_user}_{id_evenement}_{filename}"
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Sauvegarder le fichier
                file.save(full_path)
                
                # C'est ce chemin (ou nom unique) que nous insérons dans la DB
                file_path_for_db = unique_filename
            else:
                print("type de fichier non autorise")
                return render_template('submission_form.html', event_id=id_evenement, error="Type de fichier non autorisé (PDF seulement).")
            
            # Utilisation du chemin du fichier dans la colonne 'resume'
            # (Note : Le nom 'resume' est utilisé pour le chemin du fichier)
            resume_content = file_path_for_db 
            
            print("information récupérées et fichier sauvegardé.")
            
            con = sqlite3.connect("database.db")
            cur = con.cursor()
            try:
                cur.execute("""
                    INSERT INTO Proposition (titre, resume, type,keywords, id_user, id_evenement, statut) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (titre, resume_content, type_prop,mot_cles, id_user, id_evenement, 'submitted'))
                con.commit()
            except Exception as e:
                print(f"Erreur DB: {e}")
            finally:
                con.close()

            return redirect(url_for('userpage'))
        else:
            return "Unauthorized", 403

    # 2. Si c'est un GET (l'utilisateur veut juste VOIR le formulaire)
    else:
        event_id = request.args.get('event_id')
        return render_template('submission_form.html', event_id=event_id)
@app.route('/show_submissions', methods=['GET'])
def show_submissions():
    user_id = session.get("user_id")
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    soumissions = []
    
    if session.get('role') == 'admin':
        cur.execute("""SELECT * FROM Proposition""")
        soumissions = cur.fetchall()
    else:
        cur.execute("""SELECT * FROM Proposition WHERE id_user=?""", (user_id,))
        soumissions = cur.fetchall() 
    con.close()
    return render_template('show_submissions.html', soumissions=soumissions)

@app.route('/participant_signup')
def participant_signup():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('accueil'))

    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT id, event_title FROM events WHERE status='upcoming'")
    events = cur.fetchall()
    con.close()

    return render_template('participant_signup.html', events=events)


@app.route('/register_participant', methods=['POST'])
def register_participant():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('accueil'))

    event_id = request.form.get('event_id')
    type_inscription = request.form.get('ticket_type', 'standard')

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
        INSERT INTO Inscription (id_evenement, id_user, type_inscription)
        VALUES (?, ?, ?)
    """, (event_id, user_id, type_inscription))

    con.commit()
    insc_id = cur.lastrowid
    con.close()

    return redirect(url_for('registration_confirmation', id=insc_id))


@app.route('/registration_confirmation')
def registration_confirmation():
    insc_id = request.args.get('id')

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
        SELECT i.id, i.date_inscription, i.statut_paiement, e.event_title
        FROM Inscription i
        JOIN events e ON i.id_evenement = e.id
        WHERE i.id=?
    """, (insc_id,))

    reg = cur.fetchone()
    con.close()

    return render_template('registration_confirmation.html', reg=reg)

@app.route('/update_payment', methods=['POST'])
def update_payment():
    role = session.get('role')
    if role not in ('admin', 'super_admin'):
        return "Unauthorized", 403

    insc_id = request.form.get('registration_id')
    new_status = request.form.get('status')

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
        UPDATE Inscription
        SET statut_paiement=?
        WHERE id=?
    """, (new_status, insc_id))

    con.commit()
    con.close()

    return redirect(url_for('admindashboard'))

@app.route('/generate_badge', methods=['POST'])
def generate_badge():
    role = session.get('role')
    if role not in ('admin', 'super_admin'):
        return "Unauthorized", 403

    insc_id = request.form.get('registration_id')
    badge_code = str(uuid.uuid4())[:8]

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
        UPDATE Inscription
        SET badge_generated=TRUE, badge_code=?
        WHERE id=?
    """, (badge_code, insc_id))

    con.commit()
    con.close()

    return redirect(url_for('badge', id=insc_id))

@app.route('/badge')
def badge():
    insc_id = request.args.get('id')

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
        SELECT i.id, i.badge_code,
               e.event_title, e.event_start_date,
               u.username, u.institution
        FROM Inscription i
        JOIN users u ON i.id_user = u.id
        JOIN events e ON i.id_evenement = e.id
        WHERE i.id=?
    """, (insc_id,))

    data = cur.fetchone()
    con.close()

    return render_template('badge.html', info=data)


#affectation auto des propositions aux evaluateurs
@app.route('/auto_assign_reviewers', methods=['POST'])
def auto_assign_reviewers():
    if session.get('role') not in ['admin', 'super_admin']:
        return "Unauthorized", 403

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    #  Propositions non encore évaluées
    cur.execute("""
        SELECT id, id_evenement
        FROM Proposition
        WHERE statut='submitted'
    """)
    propositions = cur.fetchall()

    for prop_id, event_id in propositions:

        # Reviewers du comité de l'événement
        cur.execute("""
            SELECT user_id
            FROM event_committee
            WHERE event_id=?
        """, (event_id,))
        reviewers = [r[0] for r in cur.fetchall()]

        if not reviewers:
            continue

        # Choisir max 3 reviewers aléatoires
        selected = random.sample(reviewers, min(3, len(reviewers)))

        for reviewer_id in selected:

            # Vérifier doublon
            cur.execute("""
                SELECT 1 FROM ReviewerAssignment
                WHERE id_proposition=? AND id_reviewer=?
            """, (prop_id, reviewer_id))

            if cur.fetchone():
                continue  # déjà affecté → on ignore

            # Insérer l’affectation
            cur.execute("""
                INSERT INTO ReviewerAssignment (id_proposition, id_reviewer)
                VALUES (?, ?)
            """, (prop_id, reviewer_id))

    con.commit()
    con.close()

    return redirect(url_for('show_submissions'))


#Liste des propositions assignées à un reviewer
@app.route('/assigned_to_me')
def assigned_to_me():
    if session.get('role') != 'committee':
        return "Unauthorized", 403

    reviewer_id = session.get('user_id')

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
        SELECT p.id, p.titre, p.resume, p.keywords
        FROM Proposition p
        JOIN ReviewerAssignment ra 
             ON p.id = ra.id_proposition
        WHERE ra.id_reviewer = ?
    """, (reviewer_id,))

    propositions = cur.fetchall()
    con.close()

    return render_template(
        'assigned_list.html',
        propositions=propositions
    )
#formulaire d'évaluation
@app.route('/evaluate_form/<int:prop_id>')
def evaluate_form(prop_id):
    if session.get('role') != 'committee':
        return "Unauthorized", 403
    return render_template('evaluate.html', prop_id=prop_id)
#Enregistrement de l’évaluation
@app.route('/evaluate', methods=['POST'])
def evaluate():
    if session.get('role') != 'committee':
        return "Unauthorized", 403

    reviewer_id = session.get("user_id")
    id_prop = request.form.get("id_proposition")

    note_p = request.form.get("note_pertinence")
    note_q = request.form.get("note_qualite")
    note_o = request.form.get("note_originalite")
    commentaires = request.form.get("commentaires")
    recommandation = request.form.get("recommandation")

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    # Empêcher double évaluation
    cur.execute("""
        SELECT 1 FROM Evaluation
        WHERE id_proposition=? AND id_evaluateur=?
    """, (id_prop, reviewer_id))

    if cur.fetchone():
        con.close()
        return "Déjà évaluée"

    cur.execute("""
        INSERT INTO Evaluation 
        (id_proposition, id_evaluateur,
         note_pertinence, note_qualite, note_originalite,
         commentaires, recommandation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        id_prop, reviewer_id,
        note_p, note_q, note_o,
        commentaires, recommandation
    ))

    cur.execute("""
        UPDATE Proposition
        SET statut='evaluated'
        WHERE id=?
    """, (id_prop,))

    con.commit()
    con.close()

    return redirect(url_for('assigned_to_me'))

#Rapport d’évaluation auto
@app.route('/evaluation_report/<int:prop_id>')
def evaluation_report(prop_id):
    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
        SELECT titre, type, date_soumission
        FROM Proposition
        WHERE id=?
    """, (prop_id,))
    proposition = cur.fetchone()

    cur.execute("""
        SELECT u.username,
               e.note_pertinence,
               e.note_qualite,
               e.note_originalite,
               e.commentaires,
               e.recommandation,
               e.date_evaluation
        FROM Evaluation e
        JOIN users u ON e.id_evaluateur = u.id
        WHERE e.id_proposition=?
    """, (prop_id,))
    evaluations = cur.fetchall()

    con.close()

    return render_template(
        "evaluation_report.html",
        proposition=proposition,
        evaluations=evaluations
    )

 # If proposition does not exist or not accepted
    if not prop or prop[0] != 'accepted':
        con.close()
        return "Only accepted propositions can be assigned"

    cur.execute("""
        INSERT INTO SessionProposition (id_session, id_proposition)
        VALUES (?, ?)
    """, (session_id, prop_id))

    con.commit()
    con.close()

    return "Assignment successful"

if __name__ == '__main__':
    setup_database()
    app.run(debug=True,host="0.0.0.0",port=5000)

