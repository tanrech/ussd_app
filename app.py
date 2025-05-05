from flask import Flask, request, render_template, redirect, session, url_for, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import hashlib
import os





app = Flask(__name__)
app.secret_key = 'your_super_secret_key'  # Change for production use

# ✅ Railway MySQL configuration
app.config['MYSQL_HOST'] = 'shuttle.proxy.rlwy.net'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'XchZGCahQrMQifPOTxFXFmdrWjBMaEhg'
app.config['MYSQL_DB'] = 'railway'
app.config['MYSQL_PORT'] =28780

mysql = MySQL(app)

# ---------- Admin Login ----------
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
  


# ---------- Admin Dashboard ----------
@app.route('/admin/dashboard')
def dashboard():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT appeals.*, appeal_status.status_name 
        FROM appeals 
        LEFT JOIN appeal_status ON appeals.status_id = appeal_status.id 
        ORDER BY appeals.id DESC
    """)
    appeals = cursor.fetchall()

    cursor.execute("SELECT * FROM appeal_status")
    status_options = cursor.fetchall()

    return render_template('dashboard.html', appeals=appeals, status_options=status_options)

# ---------- Update Appeal Status ----------
@app.route('/admin/update_status/<int:appeal_id>', methods=['POST'])
def update_status(appeal_id):
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    status_name = request.form.get('status')
    cursor = mysql.connection.cursor()

    cursor.execute("SELECT id FROM appeal_status WHERE status_name = %s", (status_name,))
    result = cursor.fetchone()

    if result:
        status_id = result[0]
        cursor.execute("UPDATE appeals SET status_id = %s WHERE id = %s", (status_id, appeal_id))
        mysql.connection.commit()
        flash('✅ Appeal status updated successfully!', 'success')
    else:
        flash('❌ Invalid status selected.', 'danger')

    return redirect(url_for('dashboard'))

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# ---------- USSD Endpoint ----------
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
        cursor.execute("""
            SELECT appeal_status.status_name 
            FROM appeals 
            LEFT JOIN appeal_status ON appeals.status_id = appeal_status.id 
            WHERE student_id = %s 
            ORDER BY appeals.id DESC LIMIT 1
        """, (student_id,))
        result = cursor.fetchone()

        if result:
            status = result[0]
            return f"END Your appeal status is: {status}"
        else:
            return "END ⚠️ No appeal found for that Student ID."

    else:
        return "END ❌ Invalid input. Please try again."

# ---------- Run App ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
