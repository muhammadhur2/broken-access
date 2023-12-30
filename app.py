from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'adhdestinies@gmail.com'
app.config['MAIL_PASSWORD'] = 'ufcjvdlrhjdbhwco'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    activities = db.relationship('UserActivity', backref='user', lazy=True)
    is_admin = db.Column(db.Boolean, default=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            log_activity(user.id, "User logged in")
            analyze_user_behavior(user.id)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

def log_activity(user_id, activity):
    new_activity = UserActivity(user_id=user_id, activity=activity)
    db.session.add(new_activity)
    db.session.commit()

def analyze_user_behavior(user_id):
    activities = UserActivity.query.filter_by(user_id=user_id).all()
    recent_logins = [act for act in activities if act.activity == "User logged in" and datetime.utcnow() - act.timestamp < timedelta(minutes=5)]
    if len(recent_logins) > 3:
        generate_alert("User " + str(user_id) + " logged in multiple times in a short period.")

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/bank')
def bank():
    user_id = session.get('user_id')
    if not user_id:
        flash('You need to login first')
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if user and user.is_admin:
        generate_alert("Admin user " + user.username + " accessed the bank page")
        return render_template('bank.html')
    else:
        flash('You do not have admin privileges to access this page')
        return redirect(url_for('dashboard'))

    return redirect(url_for('dashboard'))

@app.route('/escalate_privileges')
def escalate_privileges():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            user.is_admin = not user.is_admin
            db.session.commit()
            flash('Privileges have been escalated. Admin status: ' + str(user.is_admin))
            generate_alert("Admin privileges changed for user " + user.username + ". New status: " + str(user.is_admin))
        else:
            flash('User not found.')
    else:
        flash('You need to login first.')
    
    return redirect(url_for('dashboard'))

def generate_alert(message):
    try:
        msg = Message("Alert from Flask App", sender=app.config['MAIL_USERNAME'], recipients=["commanderata@gmail.com"])
        msg.body = message
        mail.send(msg)
        print("Email alert sent: " + message)
    except Exception as e:
        print("Failed to send email alert: " + str(e))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
