from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import database as db
from scanner import get_system_metrics
from email_sender import send_report_email, send_report_email_from_db
from speed_test import run_speed_test
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = db.authenticate_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['is_admin'] = user['is_admin']
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if db.register_user(name, email, password):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email already registered', 'error')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    reports = db.get_user_reports(user_id)
    last_scan = reports[0] if reports else None
    speed_tests = db.get_user_speed_tests(user_id)
    
    total_issues = 0
    import json
    for r in reports:
        try:
            issues = json.loads(r['issues_found'])
            total_issues += len(issues)
        except:
            pass
            
    return render_template('dashboard.html', user=user, reports=reports, last_scan=last_scan, speed_tests=speed_tests, total_scans=len(reports), total_issues=total_issues)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    password_hash = None
    if password:
        password_hash = generate_password_hash(password)
        
    profile_pic = None
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and file.filename != '':
            filename = secure_filename(f"user_{user_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile_pic = filename
            
    if db.update_user(user_id, name, email, phone, password_hash, profile_pic):
        session['user_name'] = name
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Email already exists or invalid data'})

@app.route('/send_email', methods=['POST'])
def send_email():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    report_id = data.get('report_id')
    recipient_email = data.get('email')
    
    if session.get('is_admin'):
        report = db.get_report(report_id)
    else:
        report = db.get_report(report_id, session['user_id'])
        
    if not report:
        return jsonify({'success': False, 'error': 'Report not found'})
        
    if send_report_email_from_db(session['user_name'], recipient_email, report):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to send email. Check credentials.'})

@app.route('/scan', methods=['POST'])
def scan():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    data = get_system_metrics()
    report_id = db.save_report(user_id, data)
    send_report_email(user['name'], user['email'], data)
    data['report_id'] = report_id
    return jsonify({'success': True, 'data': data})

@app.route('/speedtest', methods=['POST'])
def execute_speedtest():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    result = run_speed_test()
    if result.get('success'):
        db.save_speed_test(user_id, result)
        return jsonify(result)
    return jsonify(result), 500

@app.route('/report/<int:report_id>')
def view_report(report_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Allow admin to view any report
    if session.get('is_admin'):
        report = db.get_report(report_id)
    else:
        report = db.get_report(report_id, session['user_id'])
    return jsonify(report)

@app.route('/report/<int:report_id>', methods=['DELETE'])
def delete_report_endpoint(report_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if session.get('is_admin'):
        db.delete_report(report_id)
    else:
        db.delete_report(report_id, session['user_id'])
    return jsonify({'success': True})

# --- ADMIN ROUTES ---

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    stats = db.get_admin_stats()
    return render_template('admin.html', user_name=session['user_name'], stats=stats)

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    users = db.get_all_users()
    return jsonify(users)

@app.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    reports = db.get_all_reports()
    return jsonify(reports)

@app.route('/admin/user/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    db.delete_user(user_id)
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
