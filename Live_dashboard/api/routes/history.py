from flask import Blueprint, jsonify, request
from api import db
from api.models import Machine, Reading, Limit, Alarm, Event, History, Stat, Manifest, Subscriber

history_bp = Blueprint('history', __name__)

@history_bp.route('/history', methods=['GET'])
def history():

    machine_id = request.args.get('machine_id', type=int)
    signal = request.args.get('signal', type=str)
    limit = request.args.get('limit', default=100, type=int)
    page = request.args.get('page', default=1, type=int)
    window = request.args.get('window', '24h', type=str)
    
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    if window == '1h':
        start = now - timedelta(hours=1)
    elif window == '6h':
        start = now - timedelta(hours=6)
    elif window == '24h':
        start = now - timedelta(days=1)
    elif window == '7d':
        start = now - timedelta(days=7)
    else:
        start = now - timedelta(days=1)
    
    query = Reading.query.filter(Reading.ts >= start)
    
    if machine_id:
        query = query.filter(Reading.machine_id == machine_id)
    
    if signal:
        query = query.filter(Reading.signal == signal)
    
    paginated = query.paginate(page=page, per_page=limit, error_out=False)
    
    return jsonify({
        'readings': [r.to_dict() for r in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'page': paginated.page,
        'per_page': paginated.per_page,
        'window': window,
        'signal': signal,
    }), 200