from flask import Flask, request
from flask_mysqldb import MySQL
import os
import time

app = Flask(__name__)

# Configure MySQL from Railway's environment variables
app.config['MYSQL_HOST'] = os.getenv('MYSQLHOST')
app.config['MYSQL_USER'] = os.getenv('MYSQLUSER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQLPASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQLDATABASE')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQLPORT', 3306))  # Default MySQL port is 3306

mysql = MySQL(app)

@app.route("/ussd", methods=["POST"])
def ussd():
    text = request.form.get("text", "").strip()
    
    if text == "":
        return "CON Welcome to USSD App\n1. Check status\n2. Exit"
    elif text == "1":
        return "END Your status is OK"
    elif text == "2":
        return "END Goodbye!"
    else:
        return "END Invalid option"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)