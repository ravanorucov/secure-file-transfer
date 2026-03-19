# 🔐 Secure File Transfer

---

## 📌 Overview

Secure File Transfer is a web-based application built with Flask that enables users to securely upload, encrypt, share, and decrypt files. It is designed to protect sensitive data during storage and transfer by applying strong cryptographic principles inspired by End-to-End encryption.

The system utilizes AES-based symmetric encryption (via Fernet) to ensure data confidentiality, along with secure password hashing, session-based authentication, and controlled access mechanisms. Each file is encrypted before storage and can only be decrypted by users who provide the correct password, ensuring that data remains protected at all times.

Overall, the application simulates real-world secure file-sharing systems, combining encryption, authentication, and authorization to deliver a practical and secure solution.

---

## 🚀 Features

* 🔑 User authentication (Register/Login)
* 🔒 File encryption using Fernet (symmetric encryption)
* 📤 Upload & encrypt files
* 📥 Download encrypted files
* 🔓 Decrypt files with password
* 🗑️ Delete your own files
* ⏳ Session timeout (auto logout)

---

## 🏗️ Project Structure

```
# 📦 secure-file-transfer
#  ┣ 📂 static/css         # Custom UI styling (Modern Blue-Dark Gradients)
#  ┣ 📂 templates/         # Jinja2 HTML Templates
#  ┣ 📂 uploads/           # 🔒 Encrypted binary files (.bin)
#  ┣ 📂 decrypted/         # 🔓 Temporary area for retrieved files
#  ┣ 📜 app.py             # Backend logic: Flask routes & Crypto operations
#  ┣ 📜 database.db        # SQLite3: Users & File Metadata (Auto-generated)
#  ┣ 📜 private_key.pem    # 🔑 RSA Private Key (KEEP SECRET)
#  ┣ 📜 public_key.pem     # 🔓 RSA Public Key
#  ┗ 📜 .gitignore         # Safety filter
```

---

🏗️ Architecture Overview

The system follows a simple yet effective secure workflow:

User uploads a file

File is encrypted using a dynamically generated symmetric key

Encrypted file is stored on disk (/uploads)

Encryption key and password hash are securely stored in the database

Encrypted file can be shared or downloaded by other users

Decryption is only possible when the correct password is provided


## ⚙️ Installation

### 1. Clone the repository

```
git clone https://github.com/ravanorucov/secure-file-transfer.git
cd secure-file-transfer
```

### 2. Create virtual environment (optional but recommended)

```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Run the application

```
python app.py
```

---

## 🧠 How It Works

### Encryption

* File is read as binary
* Encrypted using Fernet key
* Stored in `/uploads`
* Key + password hash stored in database

### Decryption

* User selects file + enters password
* Password is verified
* File is decrypted and sent to user

---

## 🔐 Security Notes

* Passwords are hashed using Werkzeug
* Files are encrypted using symmetric encryption (AES via Fernet)
* Session timeout is enabled (5 minutes)
* Filenames are sanitized using `secure_filename`
---

## 📌 Future Improvements

* Add HTTPS support
* Use environment variables for secrets
* Improve key management (KMS)
* Add file size/type validation
* UI/UX improvements


⭐ Support
If you like this project, give it a star ⭐ on GitHub!