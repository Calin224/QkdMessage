from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, send
import jwt, time, requests, datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bb84_qskit import BB84
from crypto_utils import encrypt_message, decrypt_message, generate_key_from_bb84

SECRET_KEY = "43217896589172571"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

saved_messages = []
all_messages = []

bb84_instance = BB84(key_length=16) 
aes_key = None

def initialize_bb84():
    global bb84_instance, aes_key
    print("🔐 Inițializare BB84...")
    bb84_instance.run()
    aes_key = bb84_instance.get_aes_key()
    print(f"🔑 Cheia AES generată: {aes_key.hex()}")
    return aes_key

@app.route("/", methods=["GET", "POST"])
def index():
    global saved_messages, all_messages, aes_key
    
    if aes_key is None:
        aes_key = initialize_bb84()
    
    if request.method == "POST":
        user_message = request.form["message"]
        
        if len(user_message) > 200:
            user_message = user_message[:200] + "..."
            print("Mesaj trunchiat la 200 caractere")
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("User sent:", user_message)
        
        encrypted_message = encrypt_message(user_message, aes_key)
        if encrypted_message:
            print(f"🔐 Mesaj criptat: {encrypted_message.hex()}")
        else:
            print("❌ Eroare la criptare!")
            return render_template("index.html", messages=[], saved_messages=saved_messages)
        
        message_entry = {
            "type": "sent",
            "text": user_message,
            "encrypted": encrypted_message.hex(),
            "time": timestamp
        }
        
        saved_messages.append(user_message)
        saved_messages = saved_messages[-5:]

        all_messages.append(message_entry)
        all_messages = sorted(all_messages, key=lambda x: x["time"], reverse=False)
        
        try:
            r = requests.post("http://127.0.0.1:5001/receive", json={
                "msg": user_message,
                "encrypted": encrypted_message.hex(),
                "key": aes_key.hex()
            })
            print(f"➡️ Sent to Server B (5001): {user_message} | Encrypted: {encrypted_message.hex()}")
        except Exception as e:
            print(f"❌ Could not send to Server B: {e}")

    messages = [f'{m["time"]} | ({m["type"]}) {m["text"]}' for m in all_messages]
    return render_template("index.html", messages=messages, saved_messages=saved_messages)


@app.route('/send', methods=['POST'])
def send_message():
    user_message = request.form["message"]
    print(f"User sent: {user_message}")
    socketio.emit('message', user_message)
    return render_template('index.html', messages=[user_message])


@app.route('/receive', methods=['POST'])
def receive():
    """Receive messages from Server B."""
    global all_messages, aes_key
    
    if aes_key is None:
        aes_key = initialize_bb84()
    
    recv_data = request.get_json()
    msg = recv_data.get("msg")
    encrypted_msg = recv_data.get("encrypted")
    received_key = recv_data.get("key")
    recv_time = recv_data.get("time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    decrypted_msg = msg
    if encrypted_msg and received_key:
        try:
            received_key_bytes = bytes.fromhex(received_key)
            decrypted_msg = decrypt_message(bytes.fromhex(encrypted_msg), received_key_bytes)
            if decrypted_msg:
                print(f"🔓 Mesaj decriptat: {decrypted_msg}")
            else:
                print("❌ Eroare la decriptare!")
                decrypted_msg = f"[CRYPT ERROR] {msg}"
        except Exception as e:
            print(f"❌ Eroare la procesarea mesajului criptat: {e}")
            decrypted_msg = f"[CRYPT ERROR] {msg}"
    
    message_entry = {
        "type": "received",
        "text": decrypted_msg,
        "time": recv_time
    }
    all_messages.append(message_entry)
    all_messages = sorted(all_messages, key=lambda x: x["time"], reverse=False)

    socketio.emit("new_message", message_entry)

    print(f"📩 Received from Server B: {decrypted_msg} at {recv_time}")
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

if __name__ == '__main__':
    print("🚀 Server A running on port 5000")
    socketio.run(app, host='127.0.0.1', port=5000)
