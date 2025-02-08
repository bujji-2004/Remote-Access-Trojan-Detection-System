from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from datetime import datetime
import sqlite3
import pandas as pd
import time

app = Flask(__name__)

# Database setup
DB_PATH = 'scan_history.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                file_type TEXT,
                is_trojan INTEGER,
                scan_date TEXT
            )
        ''')
        conn.commit()

# Utility to save scan results
def save_scan_result(file_name, file_type, is_trojan):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scan_history (file_name, file_type, is_trojan, scan_date)
            VALUES (?, ?, ?, ?)
        ''', (file_name, file_type, is_trojan, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'})

    file_name = file.filename
    file_type = os.path.splitext(file_name)[1].lower()

    # Simulating scanning process
    time.sleep(5)  # Mimic scan time

    # Trojan detection logic
    trojan_extensions = ['.exe', '.com', '.bat', '.scr']
    trojan_keywords = [
        "Backdoor", "Payload", "Exploits", "Downloader", "Shellcode", "Keylogger",
        "Rootkit", "Infection", "Malicious code", "Command and Control (C&C)",
        "Remote Access", "Persistence", "Injector", "Spyware", "Phishing", "Dropper"
    ]

    # Check for trojan
    is_trojan = False
    if file_type in trojan_extensions:
        is_trojan = True
    else:
        content = file.read().decode('utf-8', errors='ignore')
        if any(keyword.lower() in content.lower() for keyword in trojan_keywords):
            is_trojan = True

    save_scan_result(file_name, file_type, is_trojan)

    if is_trojan:
        return jsonify({
            'success': True,
            'message': f'Trojan detected in {file_name}! Delete or do not click on this file.'
        })
    else:
        return jsonify({
            'success': True,
            'message': f'No trojan detected in {file_name}. The file is safe.'
        })

# History route
@app.route('/history')
def history():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM scan_history ORDER BY scan_date DESC')
        rows = cursor.fetchall()
    return render_template('history.html', rows=rows)

# Clear history route
@app.route('/clear-history', methods=['POST'])
def clear_history():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM scan_history')
        conn.commit()
    return redirect(url_for('history'))

# Dashboard route
@app.route('/dashboard')
def dashboard():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM scan_history", conn)
        total_files = len(df)
        trojans_detected = df['is_trojan'].sum()
        safe_files = total_files - trojans_detected
        file_types = df['file_type'].value_counts().to_dict()
        trojan_percentage = (trojans_detected / total_files * 100) if total_files > 0 else 0

        return render_template('dashboard.html',
                               total_files=total_files,
                               trojans_detected=trojans_detected,
                               safe_files=safe_files,
                               file_types=file_types,
                               trojan_percentage=trojan_percentage)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
