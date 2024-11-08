from flask import Flask, request, jsonify, render_template
import sqlite3
import rsa

app = Flask(__name__)
DATABASE = 'system_info.db'

# Load the public key for verification
with open("public_key.pem", "rb") as key_file:
    public_key = rsa.PublicKey.load_pkcs1(key_file.read())

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Create the table with full structure
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_specs (
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

# Function to verify the signature
def verify_signature(data, signature_hex):
    # Convert the hex signature back to bytes
    signature = bytes.fromhex(signature_hex)
    # Convert data to bytes for verification
    data_bytes = str(data).encode('utf-8')
    try:
        # Verify the signature
        rsa.verify(data_bytes, signature, public_key)
        return True
    except rsa.VerificationError:
        return False

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
@app.route("/report", methods=['POST'])
def report():
    data = request.json

    # Separate info and signature
    info = data.get("info")
    signature = data.get("signature")

    # Verify the signature before processing
    if not verify_signature(info, signature):
        return jsonify({'error': 'Invalid signature'}), 403

    # If signature is valid, store the information in the database
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO system_specs (hostname, os, os_version, cpu_count, cpu_percent, memory_percent, disk_total, disk_used, network_sent, network_received)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            info['hostname'],
            info['os'],
            info['os_version'],
            info['cpu_count'],
            info['cpu_percent'],
            info['memory_percent'],
            info['disk_total'],
            info['disk_used'],
            info['network_sent'],
            info['network_received']
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
