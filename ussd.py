from flask import Flask, request
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime, timedelta
import time

app = Flask(__name__)
app.secret_key = "secret-key"

# MySQL configuration
app.config['MYSQL_HOST'] = "crossover.proxy.rlwy.net"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "BBYoZaaPxAdwlLnJzHzaowpwXZBWMhCG"
app.config['MYSQL_DB'] = "railway"
app.config['MYSQL_PORT'] = 29472

mysql = MySQL(app)

# In-memory session tracking and status caching
session_timers = {}
session_status_cache = {}

@app.route("/ussd", methods=["POST"])
def ussd():
    session_id = request.form.get("sessionId", "")
    phone_number = request.form.get("phoneNumber", "")
    text = request.form.get("text", "")
    print("Received USSD:", request.form)

    steps = text.split("*")
    level = len(steps)

    # Track session start
    if session_id not in session_timers:
        session_timers[session_id] = time.time()
    elif time.time() - session_timers[session_id] > 180:
        del session_timers[session_id]
        return "END ⏰ Session expired. Please try again.", 200, {'Content-Type': 'text/plain'}

    try:
        # MAIN MENU
        if text == "":
            response = (
                "CON 🌟 Welcome to the Marks Appeal System 🌟\n"
                "1. Check my marks 📊\n"
                "2. Appeal my marks 📝\n"
                "3. Check appeal status 📋\n"
                "4. Exit ❌"
            )

        # Option 1: Check marks
        elif text == "1":
            response = "CON 🧾 Enter your Student ID:\n0. Back"

        elif level == 2 and steps[0] == "1":
            if steps[1] == "0":
                return redirect_main_menu()
            student_id = steps[1]
            cur = mysql.connection.cursor()
            cur.execute("SELECT module_name, mark FROM marks WHERE student_id = %s", (student_id,))
            results = cur.fetchall()
            cur.execute("SELECT status FROM appeals WHERE student_id = %s ORDER BY id DESC LIMIT 1", (student_id,))
            appeal = cur.fetchone()
            cur.close()

            if results:
                marks_msg = "\n".join([f"{row[0]}: {row[1]}" for row in results])
                if appeal and appeal[0] == "resolved":
                    marks_msg += "\n✅ Your marks were re-confirmed."
                response = f"END 📚 Your Marks:\n{marks_msg}"
            else:
                response = "END ⚠️ Student ID not found."

        # Option 2: Appeal marks
        elif text == "2":
            response = "CON 🔍 Enter your Student ID to appeal:\n0. Back"

        elif level == 2 and steps[0] == "2":
            if steps[1] == "0":
                return redirect_main_menu()
            student_id = steps[1]
            cur = mysql.connection.cursor()
            cur.execute("SELECT module_name, mark FROM marks WHERE student_id = %s", (student_id,))
            modules = cur.fetchall()
            cur.close()
            if modules:
                response = "CON ✏️ Select module to appeal:\n"
                for i, m in enumerate(modules, 1):
                    response += f"{i}. {m[0]} ({m[1]})\n"
                response += "0. Back"
            else:
                response = "END ❌ No modules found for this student ID."

        elif level == 3 and steps[0] == "2":
            if steps[2] == "0":
                return "CON 🔍 Enter your Student ID to appeal:\n0. Back", 200, {'Content-Type': 'text/plain'}
            student_id = steps[1]
            module_index = int(steps[2]) - 1
            cur = mysql.connection.cursor()
            cur.execute("SELECT module_name FROM marks WHERE student_id = %s", (student_id,))
            modules = [row[0] for row in cur.fetchall()]
            cur.close()
            if 0 <= module_index < len(modules):
                selected_module = modules[module_index]
                response = f"CON 📃 Enter reason for appealing {selected_module}:\n0. Back"
            else:
                response = "END ⚠️ Invalid module selection."

        elif level == 4 and steps[0] == "2":
            if steps[3] == "0":
                student_id = steps[1]
                cur = mysql.connection.cursor()
                cur.execute("SELECT module_name, mark FROM marks WHERE student_id = %s", (student_id,))
                modules = cur.fetchall()
                cur.close()
                if modules:
                    response = "CON ✏️ Select module to appeal:\n"
                    for i, m in enumerate(modules, 1):
                        response += f"{i}. {m[0]} ({m[1]})\n"
                    response += "0. Back"
                    return response, 200, {'Content-Type': 'text/plain'}
                else:
                    return "END ❌ No modules found for this student ID.", 200, {'Content-Type': 'text/plain'}

            student_id = steps[1]
            module_index = int(steps[2]) - 1
            reason = steps[3]
            cur = mysql.connection.cursor()
            cur.execute("SELECT module_name FROM marks WHERE student_id = %s", (student_id,))
            modules = [row[0] for row in cur.fetchall()]
            selected_module = modules[module_index]
            cur.execute("INSERT INTO appeals (student_id, module_name, reason, status) VALUES (%s, %s, %s, %s)",
                        (student_id, selected_module, reason, 'pending'))
            mysql.connection.commit()
            cur.close()
            response = "END ✅ Appeal submitted successfully. We’ll review it shortly."

        # Option 3: Check appeal status
        elif text == "3":
            response = "CON 🕵️ Enter your Student ID:\n0. Back"

        elif level == 2 and steps[0] == "3":
            if steps[1] == "0":
                return redirect_main_menu()
            student_id = steps[1]
            now = datetime.now()

            if session_id in session_status_cache:
                cached = session_status_cache[session_id]
                if now - cached['time'] < timedelta(minutes=4):
                    return f"END [Cached] Appeal status: {cached['status']}", 200, {'Content-Type': 'text/plain'}

            cur = mysql.connection.cursor()
            cur.execute("SELECT status FROM appeals WHERE student_id = %s ORDER BY appeal_id DESC LIMIT 1", (student_id,))
            result = cur.fetchone()
            cur.close()
            if result:
                status = result[0]
                session_status_cache[session_id] = {'status': status, 'time': now}
                response = f"END Your appeal status is: {status}"
            else:
                response = "END ❌ No appeal found for this Student ID."

        # Option 4: Exit
        elif text == "4":
            response = "END 👋 Thank you for using our service!"

        else:
            response = "END ❓ Invalid choice. Please try again."

    except Exception as e:
        print("🔥 ERROR in /ussd route:", e)
        response = "END ⚠️ Dear customer, the network is experiencing technical problems. Please try again later."

    return response, 200, {'Content-Type': 'text/plain'}

def redirect_main_menu():
    return (
        "CON 🌟 Welcome to the Marks Appeal System 🌟\n"
        "1. Check my marks 📊\n"
        "2. Appeal my marks 📝\n"
        "3. Check appeal status 📋\n"
        "4. Exit ❌",
        200,
        {'Content-Type': 'text/plain'}
    )

if __name__ == "__main__":
    from os import getenv
    app.run(debug=False, host="0.0.0.0", port=int(getenv("PORT", 5000)))
