from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'system_info.db'

# Initialisatie van de database
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Verwijder de bestaande tabel als deze bestaat (start vers)
    c.execute('DROP TABLE IF EXISTS system_specs')

    # Maak de tabel opnieuw met de volledige structuur
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

# Endpoint voor de hoofdpagina
@app.route('/')
def index():
    return render_template('specs.html')

# Endpoint voor grafiekgegevens
@app.route('/data')
def data():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT timestamp, cpu_percent, memory_percent, disk_used, network_sent, network_received FROM system_specs ORDER BY timestamp DESC LIMIT 60')
    rows = c.fetchall()
    conn.close()

    # Data formatteren voor de grafiek
    data = {
        "timestamps": [row[0] for row in rows][::-1],
        "cpu_percent": [row[1] for row in rows][::-1],
        "memory_percent": [row[2] for row in rows][::-1],
        "disk_used": [row[3] for row in rows][::-1],
        "network_sent": [row[4] for row in rows][::-1],
        "network_received": [row[5] for row in rows][::-1]
    }
    return jsonify(data)

# Endpoint voor het ontvangen van rapporten
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
