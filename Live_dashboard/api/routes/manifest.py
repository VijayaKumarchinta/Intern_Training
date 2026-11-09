from flask import Blueprint, jsonify
from api import db
from api.models import Machine, Reading, Limit, Alarm, Event, History, Stat, Manifest, Subscriber

manifest_bp = Blueprint('manifest', __name__)
@manifest_bp.route('/manifest', methods=['GET'])
def manifest():
    manifest_obj = Manifest.query.first()
    if not manifest_obj:
        manifest_obj = Manifest(version='1.0.0', reading_count=0, machine_count=0)
        db.session.add(manifest_obj)
        db.session.commit()
    
    return jsonify({
        'version': manifest_obj.version,
        'reading_count': manifest_obj.reading_count,
        'machine_count': manifest_obj.machine_count,
        'last_update': manifest_obj.last_update.isoformat() if manifest_obj.last_update else None,
        'service': 'line-speed-30-iot',
    }), 200