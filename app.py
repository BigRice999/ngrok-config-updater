from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from geopy.distance import geodesic
import os

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'flaskuser'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'checkin_db'

mysql = MySQL(app)

@app.before_request
def log_request_info():
    print(f"Incoming: {request.method} {request.path}")

@app.route('/')
def home():
    return "Flask back-end is running."

@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form.get('worker_name')
        email = request.form.get('worker_email')
        password = request.form.get('worker_password')
        phone = request.form.get('worker_phone')

        if not all([name, email, password, phone]):
            return jsonify({'status': 'error', 'message': 'Missing registration fields'}), 400

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO workers (name, email, password, phone) VALUES (%s, %s, %s,%s)",
                    (name, email, hashed_password, phone))
        mysql.connection.commit()
        cur.close()

        return jsonify({'status': 'success', 'message': 'Registration successful'}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('worker_email')
        password = request.form.get('worker_password')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM workers WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[3], password):  
            user_data = {
                'worker_id': user[0],
                'worker_name': user[1],
                'worker_email': user[2],
                'worker_phone': user[4]
            }
            return jsonify({'status': 'success', 'data': [user_data]}), 200
        else:
            return jsonify({'status': 'fail', 'message': 'Invalid credentials'}), 401

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/checkin', methods=['POST'])
def checkin():
    try:
        print(f"Content-Type: {request.content_type}")
        if request.content_type.startswith('multipart/form-data'):
            worker_id = request.form.get('worker_id')
            worker_name = request.form.get('worker_name')
            checkin_date = request.form.get('checkin_date')
            checkin_time = request.form.get('checkin_time')
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            image = request.files.get('image')

            if not all([worker_id, checkin_date, checkin_time, latitude, longitude, image]):
                return jsonify({'status': 'error', 'message': 'Missing fields (multipart)'}), 400

            filename = secure_filename(f"{worker_id}_checkin_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
            image_path = os.path.join('checkin_images', filename)
            os.makedirs('checkin_images', exist_ok=True)
            image.save(image_path)

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO checkins (worker_id, worker_name, checkin_date, checkin_time, latitude, longitude, image_path) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (worker_id, worker_name, checkin_date, checkin_time, latitude, longitude, image_path))
            mysql.connection.commit()
            cur.close()

            return jsonify({'status': 'success', 'message': 'Check-in with photo successful'}), 200
        else:
            data = request.get_json()
            user_id = data.get('user_id')
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            if not all([user_id, latitude, longitude]):
                return jsonify({'status': 'error', 'message': 'Missing fields (json)'}), 400

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO checkins (user_id, latitude, longitude) VALUES (%s, %s, %s)",
                        (user_id, latitude, longitude))
            mysql.connection.commit()
            cur.close()

            return jsonify({'status': 'success', 'message': 'Check-in without photo successful'}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        worker_id = request.form.get('worker_id')
        worker_name = request.form.get('worker_name')
        checkout_date = request.form.get('checkout_date')
        checkout_time = request.form.get('checkout_time')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        image = request.files.get('image')

        if not all([worker_id, checkout_date, checkout_time, latitude, longitude, image]):
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

        filename = secure_filename(f"{worker_id}_checkout_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
        image_path = os.path.join('checkout_images', filename)
        os.makedirs('checkout_images', exist_ok=True)
        image.save(image_path)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO checkouts (worker_id, worker_name, checkout_date, checkout_time, latitude, longitude, image_path) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (worker_id, worker_name, checkout_date, checkout_time, latitude, longitude, image_path))
        mysql.connection.commit()
        cur.close()

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/task_submission', methods=['POST'])
def task_submission():
    try:
        worker_id = request.form.get('worker_id')
        worker_name = request.form.get('worker_name')
        submission_date = request.form.get('submission_date')
        tasks_completed = request.form.get('tasks_completed')

        if not all([worker_id, submission_date, tasks_completed]):
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO task_submissions (worker_id, worker_name, submission_date, tasks_completed)
            VALUES (%s, %s, %s, %s)
        """, (worker_id, worker_name, submission_date, tasks_completed))
        mysql.connection.commit()
        cur.close()

        return jsonify({'status': 'success', 'message': 'Tasks submitted successfully'}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

def is_within_geofence(lat, lon, center=(6.4266, 100.2803), radius=150):
    current = (float(lat), float(lon))
    return geodesic(center, current).meters <= radius

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

