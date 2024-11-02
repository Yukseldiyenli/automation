from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)
DATABASE = 'system_info.db'


# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Drop the existing table if it exists (start fresh)
    c.execute('DROP TABLE IF EXISTS system_specs')
    # Create the table with full structure
    c.execute('''
        CREATE TABLE system_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT,
            os TEXT,
            os_version TEXT,
            cpu_count INTEGER,
            cpu_percent REAL,
            memory_percent REAL,
            disk_total INTEGER,
            disk_used INTEGER,
            network_sent INTEGER,
            network_received INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized with the required structure.")


# Endpoint for the main page
@app.route('/')
def index():
    return render_template('specs.html')


# Endpoint to fetch the list of unique hostnames (connected devices)
@app.route('/devices')
def devices():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT DISTINCT hostname FROM system_specs')
    rows = c.fetchall()
    conn.close()
    hostnames = [row[0] for row in rows]
    return jsonify(hostnames)


# Endpoint to fetch chart data (optional hostname parameter)
@app.route('/data')
def data():
    hostname = request.args.get('hostname')
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if hostname:
        c.execute('''
            SELECT timestamp, cpu_percent, memory_percent, disk_used, network_sent, network_received 
            FROM system_specs WHERE hostname = ? ORDER BY timestamp DESC LIMIT 60
        ''', (hostname,))
    else:
        c.execute('''
            SELECT timestamp, cpu_percent, memory_percent, disk_used, network_sent, network_received 
            FROM system_specs ORDER BY timestamp DESC LIMIT 60
        ''')

    rows = c.fetchall()
    conn.close()

    data = {
        "timestamps": [row[0] for row in rows][::-1],
        "cpu_percent": [row[1] for row in rows][::-1],
        "memory_percent": [row[2] for row in rows][::-1],
        "disk_used": [row[3] for row in rows][::-1],
        "network_sent": [row[4] for row in rows][::-1],
        "network_received": [row[5] for row in rows][::-1]
    }
    return jsonify(data)


# Endpoint to receive reports from agents
@app.route('/report', methods=['POST'])
def report():
    data = request.json
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO system_specs (hostname, os, os_version, cpu_count, cpu_percent, memory_percent, disk_total, disk_used, network_sent, network_received)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['hostname'],
            data['os'],
            data['os_version'],
            data['cpu_count'],
            data['cpu_percent'],
            data['memory_percent'],
            data['disk_total'],
            data['disk_used'],
            data['network_sent'],
            data['network_received']
        ))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'}), 201
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
