from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
from functools import wraps

app = Flask(__name__)

# Konfigurace
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/calendar_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Inicializace srandicek
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ruzny classy
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    events = db.relationship('Event', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False, index=True)
    event_time = db.Column(db.Time)
    color = db.Column(db.String(7), default='#3b82f6')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.event_date.isoformat(),
            'time': self.event_time.isoformat() if self.event_time else None,
            'color': self.color,
            'userId': self.user_id,
            'createdBy': self.created_by,
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }

# Ochrana admina
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

# Prihlasovani 
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing credentials'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'token': access_token,
        'user': user.to_dict()
    }), 200

# Ziskani usera
@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@app.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    current_user_id = get_jwt_identity()
    
    if user.id == current_user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200

# Eventy
@app.route('/api/events', methods=['GET'])
@jwt_required()
def get_events():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    user_id = request.args.get('userId', type=int)
    
    # Admin vidi vse uzivatel jen svoje
    if user_id and user_id != current_user_id:
        if user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        query = Event.query.filter_by(user_id=user_id)
    else:
        query = Event.query.filter_by(user_id=current_user_id)
    
    if year and month:
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        query = query.filter(Event.event_date >= start_date, Event.event_date < end_date)
    
    events = query.order_by(Event.event_date).all()
    return jsonify([event.to_dict() for event in events]), 200

@app.route('/api/events', methods=['POST'])
@jwt_required()
def create_event():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('date'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Datum
    try:
        event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Check data
    event_time = None
    if data.get('time'):
        try:
            event_time = datetime.strptime(data['time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid time format'}), 400
    
    # Kdo je tam?
    target_user_id = data.get('userId', current_user_id)
    
    # Admin vytvari eventy pro ostatni, Je to spravne pripojene k databazi?:)
    if target_user_id != current_user_id and current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    event = Event(
        title=data['title'],
        description=data.get('description', ''),
        event_date=event_date,
        event_time=event_time,
        color=data.get('color', '#3b82f6'),
        user_id=target_user_id,
        created_by=current_user_id
    )
    
    db.session.add(event)
    db.session.commit()
    
    return jsonify(event.to_dict()), 201

@app.route('/api/events/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    event = Event.query.get_or_404(event_id)
    
    # Uzivatel smi editovat svoje
    if event.user_id != current_user_id and current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    if data.get('title'):
        event.title = data['title']
    if data.get('description') is not None:
        event.description = data['description']
    if data.get('date'):
        try:
            event.event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    if data.get('time'):
        try:
            event.event_time = datetime.strptime(data['time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid time format'}), 400
    if data.get('color'):
        event.color = data['color']
    
    event.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(event.to_dict()), 200

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    event = Event.query.get_or_404(event_id)
    
    # Users can only delete their own events, admins can delete any
    if event.user_id != current_user_id and current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({'message': 'Event deleted successfully'}), 200

@app.route('/api/events/export', methods=['GET'])
@jwt_required()
def export_events():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    user_id = request.args.get('userId', type=int, default=current_user_id)
    
    # Pristup kontorla
    if user_id != current_user_id and user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    query = Event.query.filter_by(user_id=user_id)
    
    if year and month:
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        query = query.filter(Event.event_date >= start_date, Event.event_date < end_date)
    
    events = query.all()
    
    # ICS funguje?
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Calendar App//EN\n"
    
    for event in events:
        date_str = event.event_date.strftime('%Y%m%d')
        time_str = event.event_time.strftime('%H%M%S') if event.event_time else '120000'
        
        ics_content += f"BEGIN:VEVENT\n"
        ics_content += f"UID:{event.id}@calendarapp.com\n"
        ics_content += f"DTSTAMP:{date_str}T{time_str}Z\n"
        ics_content += f"DTSTART:{date_str}T{time_str}Z\n"
        ics_content += f"SUMMARY:{event.title}\n"
        if event.description:
            ics_content += f"DESCRIPTION:{event.description}\n"
        ics_content += f"END:VEVENT\n"
    
    ics_content += "END:VCALENDAR"
    
    return ics_content, 200, {
        'Content-Type': 'text/calendar',
        'Content-Disposition': f'attachment; filename=calendar-{year}-{month}.ics'
    }

# Zapnuti databaze
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Pokud neni admin vytvor
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@kalendar.com',
            role='admin'
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
