import os
import sqlite3
import io
import datetime
from datetime import timedelta
from flask import Flask, request, redirect, url_for, render_template, flash, session, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
DECRYPT_FOLDER = 'decrypted'
for folder in [UPLOAD_FOLDER, DECRYPT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=7)
app.secret_key = 'secure_transfer_2026_key'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

def generate_rsa_keys():
    if not os.path.exists('private_key.pem') or not os.path.exists('public_key.pem'):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with open("private_key.pem", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        public_key = private_key.public_key()
        with open("public_key.pem", "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)')
        conn.execute('''CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        filename TEXT, 
                        encryption_key TEXT, 
                        password_hash TEXT,
                        user_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users (id))''')
        conn.commit()
        conn.close()

def encrypt_file(data):
    key = Fernet.generate_key()
    f = Fernet(key)
    return f.encrypt(data), key

def decrypt_file(encrypted_data, key):
    f = Fernet(key)
    return f.decrypt(encrypted_data)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    files = conn.execute('SELECT files.*, users.username FROM files JOIN users ON files.user_id = users.id').fetchall()
    conn.close()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session: return redirect(url_for('login'))
    file = request.files.get('file')
    password = request.form.get('password')
    if file and password:
        data = file.read()
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        enc_data, key = encrypt_file(data)
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        with open(file_path, 'wb') as f:
            f.write(enc_data)
        conn = get_db_connection()
        conn.execute('INSERT INTO files (filename, encryption_key, password_hash, user_id) VALUES (?, ?, ?, ?)', 
                     (unique_filename, key.decode(), generate_password_hash(password), session['user_id']))
        conn.commit()
        conn.close()
        flash('File successfully encrypted and uploaded.')
    return redirect(url_for('index'))

@app.route('/decrypt', methods=['POST'])
def decrypt_file_endpoint():
    if 'user_id' not in session: return redirect(url_for('login'))
    filename = request.form.get('filename')
    password = request.form.get('password')
    conn = get_db_connection()
    file_record = conn.execute('SELECT * FROM files WHERE filename = ?', (filename,)).fetchone()
    conn.close()
    if file_record and check_password_hash(file_record['password_hash'], password):
        try:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, 'rb') as f:
                enc_data = f.read()
            decrypted_data = decrypt_file(enc_data, file_record['encryption_key'].encode())
            orig_name = filename.split("_", 1)[1] if "_" in filename else filename
            dec_file_path = os.path.join(DECRYPT_FOLDER, f"decrypted_{orig_name}")
            with open(dec_file_path, 'wb') as f:
                f.write(decrypted_data)
            return send_file(io.BytesIO(decrypted_data), download_name=orig_name, as_attachment=True)
        except Exception as e:
            flash(f'Decryption error: {str(e)}')
    else:
        flash('Invalid password!')
    return redirect(url_for('index'))

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if 'user_id' not in session: return redirect(url_for('login'))
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    conn = get_db_connection()
    conn.execute('DELETE FROM files WHERE filename = ? AND user_id = ?', (filename, session['user_id']))
    conn.commit()
    conn.close()
    flash('File deleted successfully.')
    return redirect(url_for('index'))

@app.route('/download_enc/<filename>')
def download_encrypted_file(filename):
    if 'user_id' not in session: return redirect(url_for('login'))
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=f"encrypted_{filename}")
    flash('File not found!')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (u,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], p):
            session.clear()
            session['username'], session['user_id'] = u, user['id']
            session.permanent = False
            return redirect(url_for('index'))
        flash('Authentication failed.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (u, generate_password_hash(p)))
            conn.commit()
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        except: flash('Username already exists.')
        finally: conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    generate_rsa_keys()
    init_db()
    app.run(debug=True)