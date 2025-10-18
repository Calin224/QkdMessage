from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, send
import jwt, time, requests, datetime

SECRET_KEY = "43217896589172571"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

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
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("User sent:", user_message)
        message_entry = {
            "type": "sent",
            "text": user_message,
            "time": timestamp
        }
        # Save locally
        saved_messages.append(user_message)
        saved_messages = saved_messages[-5:]

        # Add to combined list and sort by time
        all_messages.append(message_entry)
        all_messages = sorted(all_messages, key=lambda x: x["time"], reverse=False)
        # Trimite mesajul la serverul B (port 5000)
        try:
            r = requests.post("http://127.0.0.1:5000/receive", json={"msg": user_message})
            print(f"➡️ Sent to Server B (5000): {user_message} | Response: {r.text}")
        except Exception as e:
            print(f"❌ Could not send to Server B: {e}")

    messages = [f'{m["time"]} | ({m["type"]}) {m["text"]}' for m in all_messages]
    # messages = ["Hello", "Welcome", "Flask is cool", "WebSockets soon", "Good luck!"]
    return render_template("index1.html", messages=messages, saved_messages=saved_messages)


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
    msg = recv_data.get("msg")
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
    print("🚀 Server A running on port 5001")
    socketio.run(app, host='127.0.0.1', port=5001)
