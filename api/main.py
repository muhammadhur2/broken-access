from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from pymongo import MongoClient
import os
from bson import ObjectId



app = Flask(__name__)
mongo_uri = "mongodb+srv://cookie-tracker:NWA4atFPA9rj.Ek@cluster0.ljc5i8j.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
db = client['defaultdb']  # This will get the default database or you can specify a database name

app.config['SECRET_KEY'] = 'your_secret_key'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'adhdestinies@gmail.com'
app.config['MAIL_PASSWORD'] = 'ufcjvdlrhjdbhwco'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

# class UserActivity(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     activity = db.Column(db.Text)
#     timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     password = db.Column(db.String(80), nullable=False)
#     activities = db.relationship('UserActivity', backref='user', lazy=True)
#     is_admin = db.Column(db.Boolean, default=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # In a real-world application, ensure this password is hashed
        user = {"username": username, "password": password, "is_admin": False, "activities": []}
        db.users.insert_one(user)
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Hash password before comparing, in a real application
        user = db.users.find_one({"username": username, "password": password})
        if user:
            session['user_id'] = str(user['_id'])
            log_activity(user['_id'], "User logged in")
            # analyze_user_behavior(user['_id'])  # Implement this function for MongoDB if needed
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

# Logging activity function
def log_activity(user_id, activity):
    timestamp = datetime.utcnow()
    db.users.update_one({"_id": user_id}, {"$push": {"activities": {"activity": activity, "timestamp": timestamp}}})


# def analyze_user_behavior(user_id):
#     activities = UserActivity.query.filter_by(user_id=user_id).all()
#     recent_logins = [act for act in activities if act.activity == "User logged in" and datetime.utcnow() - act.timestamp < timedelta(minutes=5)]
#     if len(recent_logins) > 3:
#         generate_alert("User " + str(user_id) + " logged in multiple times in a short period.")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('You need to login first.')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/bank')
def bank():
    if 'user_id' not in session:
        flash('You need to login first')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user and user.get('is_admin'):
        generate_alert(f"Admin user {user['username']} accessed the bank page")
        return render_template('bank.html')
    else:
        flash('You do not have admin privileges to access this page')
        return redirect(url_for('dashboard'))

@app.route('/escalate_privileges')
def escalate_privileges():
    if 'user_id' not in session:
        flash('You need to login first.')
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        new_status = not user.get('is_admin', False)
        db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_admin": new_status}})
        flash(f'Privileges have been escalated. Admin status: {new_status}')
        generate_alert(f"Admin privileges changed for user {user['username']}. New status: {new_status}")
    else:
        flash('User not found.')

    return redirect(url_for('dashboard'))

def generate_alert(message):
    try:
        msg = Message("Alert from Flask App", sender=app.config['MAIL_USERNAME'], recipients=["m.bibi.22844@khi.iba.edu.pk"])
        msg.body = message
        mail.send(msg)
        print("Email alert sent: " + message)
    except Exception as e:
        print("Failed to send email alert: " + str(e))

if __name__ == '__main__':
    app.run(debug=True)
