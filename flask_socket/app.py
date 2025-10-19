from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit, send
import jwt, time, requests, datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bb84_qskit import BB84, Sender

SECRET_KEY = "43217896589172571"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

sender = Sender()
bb84 = BB84()

shared_key = None

def get_aes_key():
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
        # Send encrypted message to Server B
        try:
            r = requests.post("http://127.0.0.1:5001/receive", json={"msg": enc_message})
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
    # messages = ["Hello", "Welcome", "Flask is cool", "WebSockets soon", "Good luck!"]
    global shared_key
    disabled = shared_key is None
    return render_template("index.html", display_messages=display_messages, saved_messages=saved_messages, disabled=disabled, shared_key=shared_key)

@app.route('/establish_connection', methods=['POST'])
def establish_connection():
    global shared_key
    try:
        # Emit connection attempt to all clients
        socketio.emit('connection_attempt', {'status': 'starting', 'message': 'Initiating quantum key distribution...'})
        
        receiver_bases = None
        response = requests.post("http://127.0.0.1:5001/establish")
        if response.ok:
            receiver_bases = response.json().get('bases')
            print(f"📡 Received Bob bases: {receiver_bases}")
            socketio.emit('connection_progress', {'status': 'bases_received', 'message': 'Quantum bases received from Server B'})
        else:
            print(f"❌ Establish failed with status {response.status_code}")
            socketio.emit('connection_error', {'error': 'Failed to get bases from Server B'})
            return jsonify({"error": "Failed to get bases"}), 500

        socketio.emit('connection_progress', {'status': 'processing', 'message': 'Processing quantum key exchange...'})
        shared_key = bb84.run(receiver_bases)
        print(f"Shared_key SSSSSS: {shared_key}")

        try:
            r = requests.post("http://127.0.0.1:5001/receive-shared-key", json={"shared_key": shared_key})
            print(f"Sent shared_key to App B, response: {r.text}")
            socketio.emit('connection_success', {'status': 'connected', 'message': 'Quantum connection established!', 'shared_key': shared_key})
        except Exception as e:
            print(f"❌ Could not send shared_key to App B: {e}")
            socketio.emit('connection_error', {'error': f'Could not send shared key to Server B: {str(e)}'})

        return jsonify({"shared_key": shared_key})
    except Exception as e:
        print(f"❌ Could not establish connection: {e}")
        socketio.emit('connection_error', {'error': str(e)})
        return jsonify({"error": str(e)}), 500


@app.route('/send', methods=['POST'])
def send_message():
    user_message = request.form["message"]
    print(f"User sent: {user_message}")
    socketio.emit('message', user_message)
    return render_template('index.html', messages=[user_message])


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
        "time": recv_time
    }
    all_messages.append(message_entry)
    all_messages = sorted(all_messages, key=lambda x: x["time"], reverse=False)

    socketio.emit("new_message", message_entry)

    print(f"📩 Received from Server B: {msg} at {recv_time}")
    return "OK"


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
    print("🚀 Server A running on port 5000")
    socketio.run(app, host='127.0.0.1', port=5000)
