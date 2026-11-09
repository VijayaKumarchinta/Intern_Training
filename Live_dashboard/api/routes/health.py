from flask import Blueprint, jsonify
from api import db
from api.models import Machine, Subscriber

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    try:
        db.session.execute(db.text('SELECT 1'))
        db_health = 'ok'
        db_count = db.session.query(Machine).count()
    except Exception:
        db_health = 'error'
        db_count = 0
    
    try:
        subscriber_count = db.session.query(Subscriber).count()
        machine_count = db.session.query(Machine).count()
    except Exception:
        subscriber_count = 0
        machine_count = 0
    
    status = 'healthy' if db_health == 'ok' else 'degraded'
    return jsonify({
        'status': status,
        'database': db_health,
        'machines': machine_count,
        'subscribers': subscriber_count,
        'service': 'line-speed-30-iot',
        'version': '1.0.0',
    }), 200