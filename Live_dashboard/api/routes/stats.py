from flask import Blueprint, jsonify, request
from api import db
from api.models import Stat
    
stats_bp = Blueprint('stats', __name__)
@stats_bp.route('/stats', methods=['GET'])
def stats():
    
    machine_id = request.args.get('machine_id', type=int)
    signal = request.args.get('signal', type=str)
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
    
    query = Stat.query.filter(Stat.ts >= start)
    
    if machine_id:
        query = query.filter(Stat.machine_id == machine_id)
    
    if signal:
        query = query.filter(Stat.signal == signal)
    
    results = query.all()
    
    return jsonify({
        'window': window,
        'signal': signal,
        'count': len(results),
        'statistics': [r.to_dict() for r in results],
    }), 200