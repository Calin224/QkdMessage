from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, send
import jwt, time, requests, datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bb84_qskit import BB84, Receiver

SECRET_KEY = "43217896589172571"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# AES helpers
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64

shared_key = None

def get_aes_key():
    global shared_key
    if not shared_key or not isinstance(shared_key, list):
        return None
    bits = shared_key[:128]
    bits += [0] * (128 - len(bits))
    b = bytearray()
    for i in range(0, 128, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        b.append(byte)
    return bytes(b)

def aes_encrypt(plaintext):
    key = get_aes_key()
    if not key:
        return plaintext
    iv = b'\x00' * 16
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(ct).decode()

def aes_decrypt(ciphertext):
    key = get_aes_key()
    if not key:
        return ciphertext
    iv = b'\x00' * 16
    ct = base64.b64decode(ciphertext)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    pt = unpadder.update(padded) + unpadder.finalize()
    return pt.decode()

saved_messages = []
all_messages = []
# ==============================
#   ROUTES
# ==============================
@app.route("/", methods=["GET", "POST"])
def index():
    global saved_messages,all_messages
    if request.method == "POST":
        user_message = request.form["message"]
        enc_message = aes_encrypt(user_message)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("User sent:", user_message)
        message_entry = {
            "type": "sent",
            "text": user_message,
            "enc": enc_message,
            "time": timestamp
        }
        # Save locally
        saved_messages.append(user_message)
        saved_messages = saved_messages[-5:]

        # Add to combined list and sort by time
        all_messages.append(message_entry)
        all_messages = sorted(all_messages, key=lambda x: x["time"], reverse=False)
        # Emit to WebSocket clients so UI updates live
        try:
            socketio.emit("new_message", message_entry)
        except Exception:
            pass
        # Send encrypted message to Server A (port 5000)
        try:
            r = requests.post("http://127.0.0.1:5000/receive", json={"msg": enc_message})
            print(f"➡️ Sent to Server B (5000): {enc_message} | Response: {r.text}")
        except Exception as e:
            print(f"❌ Could not send to Server B: {e}")

    # Build a list of dicts for display: only show encrypted for sent messages
    display_messages = []
    for m in all_messages:
        enc_val = m["enc"] if m["type"] == "sent" else None
        display_messages.append({
            "msg": f'{m["time"]} | ({m["type"]}) {m["text"]}',
            "enc": enc_val,
            "type": m["type"]
        })
    disabled = shared_key is None
    return render_template("index1.html", display_messages=display_messages, saved_messages=saved_messages, disabled=disabled, shared_key=shared_key)


@app.route('/send', methods=['POST'])
def send_message():
    user_message = request.form["message"]
    print(f"User sent: {user_message}")
    socketio.emit('message', user_message)
    return render_template('index.html', messages=[user_message])

receiver = Receiver()
bb84 = BB84()
@app.route('/receive', methods=['POST'])
def receive():
    """Receive messages from Server B."""
    global all_messages
    recv_data = request.get_json()
    enc_msg = recv_data.get("msg")
    try:
        msg = aes_decrypt(enc_msg)
    except Exception:
        msg = enc_msg
    recv_time = recv_data.get("time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    message_entry = {
        "type": "received",
        "text": msg,
        "enc": enc_msg,
        "time": recv_time
    }
    all_messages.append(message_entry)
    all_messages = sorted(all_messages, key=lambda x: x["time"], reverse=False)

    socketio.emit("new_message", message_entry)

    print(f"📩 Received from Server B: {msg} at {recv_time}")
    return "OK"


@app.route('/establish', methods=['POST'])
def establish():
    bases = receiver.choose_bases()
    return jsonify({"bases": bases})

@app.route('/receive-shared-key', methods=['POST'])
def receive_shared_key():
    global shared_key
    data = request.get_json()
    shared_key = data.get('shared_key')
    print(f"Received shared_key from App A: {shared_key}")
    
    # Emit connection success to all clients on Server B
    socketio.emit('connection_success', {'status': 'connected', 'message': 'Quantum connection established!', 'shared_key': shared_key})
    
    return jsonify({"status": "ok"})

@app.route('/debug-shared-key')
def debug_shared_key():
    print(f"DEBUG: shared_key = {shared_key}")
    return jsonify({"shared_key": shared_key})

@socketio.on('token')
def handle_token(data):
    token = data.get('jwt')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        print(f"✅ Received valid token from Server B: {payload}")
    except jwt.ExpiredSignatureError:
        print("⚠️ Token expired")
    except jwt.InvalidTokenError:
        print("❌ Invalid token")


def send_token():
    """Generate and emit a token that includes date and time."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {'server': 'A', 'timestamp': time.time(), 'datetime': now}
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    socketio.emit('token', {'jwt': token})
    print(f"➡️ Sent token to Server B: {payload}")


@socketio.on('message')
def handle_message(msg):
    print('💬 Message received via WebSocket:', msg)
    send(f"Echo: {msg}", broadcast=True)


@socketio.on('custom_event')
def handle_custom_event(data):
    print(f"Received custom data: {data}")
    emit('response', {'status': 'OK', 'received': data})


# ==============================
#   MAIN
# ==============================
if __name__ == '__main__':
    print("🚀 Server A running on port 5001")
    socketio.run(app, host='127.0.0.1', port=5001)
