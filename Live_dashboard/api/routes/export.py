from flask import Blueprint, current_app,request, jsonify, send_file, current_app
from api import db
from api.models import Machine, Reading, Limit, Alarm, Event, History, Stat, Manifest, Subscriber
import csv
import io
from datetime import datetime

export_bp = Blueprint('export', __name__)


@export_bp.route('/export', methods=['GET'])
def export():
    
    machine_id = request.args.get('machine_id', type=int)
    start_ts = request.args.get('start_ts', type=str)
    end_ts = request.args.get('end_ts', type=str)
    fmt = request.args.get('format', 'csv', type=str)
    
    query = Reading.query
    
    if machine_id:
        query = query.filter(Reading.machine_id == machine_id)
    
    if start_ts:
        from datetime import datetime
        start = datetime.fromisoformat(start_ts)
        query = query.filter(Reading.ts >= start)
    
    if end_ts:
        from datetime import datetime
        end = datetime.fromisoformat(end_ts)
        query = query.filter(Reading.ts <= end)
    
    readings = query.order_by(Reading.ts.desc()).all()
    
    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['machine_id', 'ts', 'oil_temp', 'delta_t', 'burner_load', 'moisture', 'paddle_speed', 'oil_level'])
        
        for r in readings:
            writer.writerow([
                r.machine_id,
                r.ts.isoformat() if r.ts else '',
                r.oil_temp,
                r.delta_t,
                r.burner_load,
                r.moisture,
                r.paddle_speed,
                r.oil_level,
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='readings.csv'
        )
    elif fmt == 'json':
        return jsonify({
            'readings': [r.to_dict() for r in readings],
            'count': len(readings),
        }), 200
    
    return jsonify({'error': 'unsupported format'}), 400