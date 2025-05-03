from flask import Flask, request, render_template, redirect, session, url_for, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import hashlib

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'  # Change this for production use

# ✅ Railway MySQL configuration
app.config['MYSQL_HOST'] = 'crossover.proxy.rlwy.net'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'BBYoZaaPxAdwlLnJzHzaowpwXZBWMhCG'
app.config['MYSQL_DB'] = 'railway'
app.config['MYSQL_PORT'] = 29472

mysql = MySQL(app)

# ✅ Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if session.get('loggedin'):
        return redirect(url_for('dashboard'))

    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admins WHERE username = %s AND password = %s',
                       (username, hashed_password))
        admin = cursor.fetchone()
        if admin:
            session['loggedin'] = True
            session['username'] = admin['username']
            return redirect(url_for('dashboard'))
        else:
            msg = '⚠️ Incorrect username or password!'
    return render_template('login.html', msg=msg)

# ✅ Admin Dashboard
@app.route('/admin/dashboard')
def dashboard():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM appeals ORDER BY id DESC")
    appeals = cursor.fetchall()
    return render_template('dashboard.html', appeals=appeals)

# ✅ Update Appeal Status
@app.route('/admin/update_status/<int:appeal_id>', methods=['POST'])
def update_status(appeal_id):
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    new_status = request.form.get('status')  # status can be 'Approved' or 'Rejected'
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE appeals SET status_id = %s WHERE id = %s", (new_status, appeal_id))
    mysql.connection.commit()
    flash('✅ Appeal status updated successfully!', 'success')
    return redirect(url_for('dashboard'))

# ✅ Logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# ✅ USSD Logic
@app.route("/ussd", methods=["POST"])
def ussd():
    session_id = request.form.get("sessionId", "")
    phone_number = request.form.get("phoneNumber", "")
    text = request.form.get("text", "")

    user_response = text.split("*")

    if text == "":
        return "CON Welcome to the Appeal Status Checker\n1. Check Appeal Status"
    
    elif text == "1":
        return "CON Please enter your Student ID"

    elif len(user_response) == 2 and user_response[0] == "1":
        student_id = user_response[1]
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT status_id FROM appeals WHERE student_id = %s ORDER BY id DESC LIMIT 1", (student_id,))
        result = cursor.fetchone()

        if result:
            status = result[0]
            return f"END Your appeal status is: {status}"
        else:
            return "END ⚠️ No appeal found for that Student ID."

    else:
        return "END ❌ Invalid input. Please try again."

# ✅ Run the app
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

