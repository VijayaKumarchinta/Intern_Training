from flask import Blueprint, jsonify, request
from api import db
from api.models import Alarm

alarms_bp = Blueprint('alarms', __name__)

@alarms_bp.route('/alarms', methods=['GET'])
def alarms():

    machine_id = request.args.get('machine_id', type=int)
    severity = request.args.get('severity', type=str)
    status = request.args.get('status', type=str)
    limit = request.args.get('limit', default=50, type=int)
    page = request.args.get('page', default=1, type=int)
    query = Alarm.query
    
    if machine_id:
        query = query.filter(Alarm.machine_id == machine_id)
    
    if severity:
        query = query.filter(Alarm.severity == severity)
    
    if status:
        query = query.filter(Alarm.status == status)

    paginated = query.paginate(page=page, per_page=limit, error_out=False)
    
    return jsonify({
        'alarms': [a.to_dict() for a in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'page': paginated.page,
        'per_page': paginated.per_page,
    }), 200