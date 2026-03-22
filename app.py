import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')

# Railway uses postgres:// but SQLAlchemy needs postgresql://
database_url = os.getenv('DATABASE_URL', '')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


# ─── Models ───────────────────────────────────────────────

class Helper(db.Model):
    __tablename__ = 'helpers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(10), nullable=False)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'location': self.location,
            'avatar': self.avatar,
            'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }


class Emergency(db.Model):
    __tablename__ = 'emergencies'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(30), nullable=False, default='pending')
    location = db.Column(db.String(200))
    urgency = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'status': self.status,
            'location': self.location,
            'urgency': self.urgency,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(30), nullable=False)
    text = db.Column(db.String(300), nullable=False)
    icon = db.Column(db.String(10), default='📋')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'text': self.text,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ─── Static File Serving ─────────────────────────────────

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


# ─── API Routes ───────────────────────────────────────────

@app.route('/api/availability/<int:helper_id>', methods=['GET'])
def get_availability(helper_id):
    helper = Helper.query.get_or_404(helper_id)
    return jsonify({'id': helper.id, 'is_online': helper.is_online})


@app.route('/api/availability/<int:helper_id>', methods=['POST'])
def toggle_availability(helper_id):
    helper = Helper.query.get_or_404(helper_id)
    helper.is_online = not helper.is_online
    helper.last_seen = datetime.utcnow()

    # log the activity
    action = 'online' if helper.is_online else 'offline'
    icon = '🟢' if helper.is_online else '🔴'
    log = ActivityLog(
        type=action,
        text=f'{helper.name} went {action}',
        icon=icon
    )
    db.session.add(log)
    db.session.commit()

    # broadcast via socketio
    socketio.emit('availability_changed', helper.to_dict())
    socketio.emit('dashboard_update', get_dashboard_data())
    socketio.emit('activity_update', log.to_dict())

    return jsonify(helper.to_dict())


@app.route('/api/helpers', methods=['GET'])
def get_helpers():
    online_only = request.args.get('online', 'false').lower() == 'true'
    query = Helper.query
    if online_only:
        query = query.filter_by(is_online=True)
    helpers = query.order_by(Helper.name).all()
    return jsonify([h.to_dict() for h in helpers])


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    return jsonify(get_dashboard_data())


def get_dashboard_data():
    active = Emergency.query.filter(Emergency.status.in_(['active', 'accepted'])).count()
    helpers_online = Helper.query.filter_by(is_online=True).count()
    pending = Emergency.query.filter_by(status='pending').count()
    return {
        'active_emergencies': active,
        'available_helpers': helpers_online,
        'pending_requests': pending
    }


@app.route('/api/activity', methods=['GET'])
def get_activity():
    limit = request.args.get('limit', 10, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return jsonify([l.to_dict() for l in logs])


# ─── SocketIO Events ─────────────────────────────────────

@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


# ─── Auto-create tables ──────────────────────────────────

with app.app_context():
    db.create_all()

# ─── Run ──────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
