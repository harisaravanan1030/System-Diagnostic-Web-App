import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'sysdiag.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))
        
    conn = get_db_connection()
    c = conn.cursor()
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Reports table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            cpu_usage REAL,
            ram_usage REAL,
            disk_usage REAL,
            disk_total INTEGER,
            disk_free INTEGER,
            ram_total INTEGER,
            ram_free INTEGER,
            network_status TEXT,
            ip_address TEXT,
            os_name TEXT,
            uptime TEXT,
            issues_found TEXT,
            fixes_suggested TEXT,
            top_processes TEXT,
            bytes_sent INTEGER,
            bytes_recv INTEGER,
            battery TEXT,
            security_score INTEGER,
            security_details TEXT,
            scan_date TEXT,
            scan_time TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    # Speed Tests table
    c.execute('''
        CREATE TABLE IF NOT EXISTS speed_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            download_speed REAL,
            upload_speed REAL,
            ping REAL,
            isp TEXT,
            server_location TEXT,
            test_date TEXT,
            test_time TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()

    _migrate_reports_table(conn)

    # Create default admin account if not exists
    c.execute('SELECT * FROM users WHERE email = ?', ('admin@sysdiag.com',))
    if not c.fetchone():
        hash_pw = generate_password_hash('Admin@123')
        c.execute('INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)', 
                  ('System Admin', 'admin@sysdiag.com', hash_pw, 1))
        conn.commit()

    conn.close()

def _migrate_reports_table(conn):
    c = conn.cursor()
    new_columns = [
        ('processor_name', 'TEXT'),
        ('processor_gen', 'TEXT'),
        ('cpu_cores', 'INTEGER'),
        ('cpu_threads', 'INTEGER'),
        ('cpu_speed', 'TEXT'),
        ('gpu_name', 'TEXT'),
        ('gpu_vram', 'TEXT'),
        ('gpu_usage', 'TEXT'),
        ('ram_used', 'INTEGER'),
        ('ram_type', 'TEXT'),
        ('ram_speed', 'TEXT'),
        ('drives', 'TEXT'),
        ('os_version', 'TEXT'),
        ('os_build', 'TEXT'),
        ('device_name', 'TEXT'),
        ('device_type', 'TEXT'),
        ('screen_resolution', 'TEXT'),
        ('display_count', 'INTEGER'),
        ('network_adapters', 'TEXT'),
        ('bios_version', 'TEXT'),
        ('last_boot_time', 'TEXT'),
        ('device_info', 'TEXT'),
    ]
    for col, col_type in new_columns:
        try:
            c.execute(f'ALTER TABLE reports ADD COLUMN {col} {col_type}')
        except sqlite3.OperationalError:
            pass
    conn.commit()

def register_user(name, email, password, is_admin=False):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        hash_pw = generate_password_hash(password)
        c.execute('INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)', 
                  (name, email, hash_pw, 1 if is_admin else 0))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def get_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT u.id, u.name, u.email, u.created_at, u.is_admin,
               COUNT(r.id) as total_scans,
               MAX(r.scan_date || ' ' || r.scan_time) as last_scan
        FROM users u
        LEFT JOIN reports r ON u.id = r.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''')
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return users

def delete_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    # Reports and speed tests should cascade delete, but sqlite needs PRAGMA foreign_keys = ON;
    c.execute("PRAGMA foreign_keys = ON;")
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def save_report(user_id, data):
    conn = get_db_connection()
    c = conn.cursor()
    import json

    display_count = data.get('display_count', 'N/A')
    if display_count == 'N/A':
        display_count_val = None
    else:
        try:
            display_count_val = int(display_count)
        except (TypeError, ValueError):
            display_count_val = None

    cpu_cores = data.get('cpu_cores', None)
    cpu_threads = data.get('cpu_threads', None)
    try:
        cpu_cores = int(cpu_cores) if cpu_cores not in (None, 'N/A') else None
    except (TypeError, ValueError):
        cpu_cores = None
    try:
        cpu_threads = int(cpu_threads) if cpu_threads not in (None, 'N/A') else None
    except (TypeError, ValueError):
        cpu_threads = None

    c.execute('''
        INSERT INTO reports (
            user_id, cpu_usage, ram_usage, disk_usage, disk_total, disk_free,
            ram_total, ram_free, ram_used, network_status, ip_address, os_name, uptime,
            issues_found, fixes_suggested, top_processes, bytes_sent, bytes_recv,
            battery, security_score, security_details, scan_date, scan_time,
            processor_name, processor_gen, cpu_cores, cpu_threads, cpu_speed,
            gpu_name, gpu_vram, gpu_usage, ram_type, ram_speed, drives,
            os_version, os_build, device_name, device_type, screen_resolution,
            display_count, network_adapters, bios_version, last_boot_time, device_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, data['cpu']['usage'], data['ram']['usage_percent'], data['disk']['usage_percent'],
        data['disk']['total'], data['disk']['free'], data['ram']['total'], data['ram']['free'],
        data['ram']['used'], data['network']['status'], data['network']['ip'],
        data['os']['name_version'], data['os']['uptime'],
        json.dumps(data['issues']), json.dumps(data['fixes']), json.dumps(data['processes']),
        data['network']['bytes_sent'], data['network']['bytes_recv'], json.dumps(data['battery']),
        data['security']['score'], json.dumps(data['security']['details']),
        data['time']['date'], data['time']['time'],
        data.get('processor_name'), data.get('processor_gen'), cpu_cores, cpu_threads,
        data.get('cpu_speed'), data.get('gpu_name'), data.get('gpu_vram'), data.get('gpu_usage'),
        data.get('ram_type'), data.get('ram_speed'), json.dumps(data.get('drives', [])),
        data.get('os_version'), data.get('os_build'), data.get('device_name'), data.get('device_type'),
        data.get('screen_resolution'), display_count_val,
        json.dumps(data.get('network_adapters', [])), data.get('bios_version'),
        data.get('last_boot_time'), json.dumps(data.get('device_info', {}))
    ))
    report_id = c.lastrowid
    conn.commit()
    conn.close()
    return report_id

def get_user_reports(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    # Left join with latest speed test on the same date (approximate)
    c.execute('''
        SELECT r.*, s.download_speed, s.upload_speed, s.ping 
        FROM reports r
        LEFT JOIN speed_tests s ON r.user_id = s.user_id AND r.scan_date = s.test_date
        WHERE r.user_id = ? 
        GROUP BY r.id
        ORDER BY r.id DESC
    ''', (user_id,))
    reports = [dict(row) for row in c.fetchall()]
    conn.close()
    return reports

def get_all_reports():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT r.*, u.name as user_name 
        FROM reports r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.id DESC
    ''')
    reports = [dict(row) for row in c.fetchall()]
    conn.close()
    return reports

def get_report(report_id, user_id=None):
    conn = get_db_connection()
    c = conn.cursor()
    if user_id:
        c.execute('SELECT * FROM reports WHERE id = ? AND user_id = ?', (report_id, user_id))
    else:
        c.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
    report = c.fetchone()
    conn.close()
    if report:
        return dict(report)
    return None

def delete_report(report_id, user_id=None):
    conn = get_db_connection()
    c = conn.cursor()
    if user_id:
        c.execute('DELETE FROM reports WHERE id = ? AND user_id = ?', (report_id, user_id))
    else:
        c.execute('DELETE FROM reports WHERE id = ?', (report_id,))
    conn.commit()
    conn.close()

def save_speed_test(user_id, data):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO speed_tests (
            user_id, download_speed, upload_speed, ping, isp, server_location, test_date, test_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, data['download'], data['upload'], data['ping'],
        data['isp'], data['server'], data['date'], data['time']
    ))
    conn.commit()
    conn.close()

def get_user_speed_tests(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM speed_tests WHERE user_id = ? ORDER BY id DESC LIMIT 5', (user_id,))
    tests = [dict(row) for row in c.fetchall()]
    conn.close()
    return tests

def get_admin_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    stats = {}
    c.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM reports")
    stats['total_scans'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM speed_tests")
    stats['total_speed_tests'] = c.fetchone()[0]
    
    # Calculate total issues found (rough estimate by counting non-empty arrays, or we can fetch and count)
    c.execute("SELECT issues_found FROM reports")
    issues_rows = c.fetchall()
    import json
    total_issues = 0
    issue_counts = {}
    for row in issues_rows:
        try:
            issues = json.loads(row[0])
            total_issues += len(issues)
            for iss in issues:
                issue_counts[iss] = issue_counts.get(iss, 0) + 1
        except:
            pass
    stats['total_issues'] = total_issues
    stats['common_issues'] = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Scans per day (last 7 days)
    c.execute('''
        SELECT scan_date, COUNT(*) as count 
        FROM reports 
        GROUP BY scan_date 
        ORDER BY scan_date DESC LIMIT 7
    ''')
    stats['scans_per_day'] = [dict(row) for row in c.fetchall()][::-1]
    
    # Avg security score over time (last 7 days)
    c.execute('''
        SELECT scan_date, AVG(security_score) as avg_score 
        FROM reports 
        GROUP BY scan_date 
        ORDER BY scan_date DESC LIMIT 7
    ''')
    stats['avg_scores'] = [dict(row) for row in c.fetchall()][::-1]

    # Recent activity (mix of latest scans and speed tests)
    # Since sqlite doesn't have an easy way to interleave dynamically without UNION ALL and matching schemas
    # we'll just fetch latest 5 reports and 5 speed tests, then sort in python
    c.execute("SELECT 'Scan' as type, u.name as user_name, r.scan_date as date, r.scan_time as time FROM reports r JOIN users u ON r.user_id = u.id ORDER BY r.id DESC LIMIT 5")
    recent_scans = [dict(row) for row in c.fetchall()]
    c.execute("SELECT 'Speed Test' as type, u.name as user_name, s.test_date as date, s.test_time as time FROM speed_tests s JOIN users u ON s.user_id = u.id ORDER BY s.id DESC LIMIT 5")
    recent_speeds = [dict(row) for row in c.fetchall()]
    
    activity = recent_scans + recent_speeds
    activity.sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)
    stats['recent_activity'] = activity[:10]

    conn.close()
    return stats

# Initialize DB on import
init_db()
