from .db import db


class Machine(db.Model):
    __tablename__ = 'machines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(200))
    line_id = db.Column(db.String(50), nullable=False, unique=True)
    building = db.Column(db.String(100))
    floor = db.Column(db.String(50))
    area = db.Column(db.String(100))
    status = db.Column(db.String(20), default='offline')
    last_seen = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'line_id': self.line_id,
            'building': self.building,
            'floor': self.floor,
            'area': self.area,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Reading(db.Model):
    __tablename__ = 'readings'

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey('machines.id', ondelete='CASCADE'), nullable=False
    )
    ts = db.Column(db.DateTime(timezone=True), nullable=False)
    oil_temp = db.Column(db.Float)
    delta_t = db.Column(db.Float)
    burner_load = db.Column(db.Float)
    moisture = db.Column(db.Float)
    paddle_speed = db.Column(db.Float)
    oil_level = db.Column(db.Float)
    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
    )

    __table_args__ = (
        db.UniqueConstraint('machine_id', 'ts', name='uix_machine_ts'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'ts': self.ts.isoformat() if self.ts else None,
            'oil_temp': self.oil_temp,
            'delta_t': self.delta_t,
            'burner_load': self.burner_load,
            'moisture': self.moisture,
            'paddle_speed': self.paddle_speed,
            'oil_level': self.oil_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Limit(db.Model):
    __tablename__ = 'limits'

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey('machines.id', ondelete='CASCADE'), nullable=False
    )
    signal = db.Column(db.String(50), nullable=False)
    min_val = db.Column(db.Float, nullable=False)
    max_val = db.Column(db.Float, nullable=False)
    warning = db.Column(db.Float)
    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
    )

    __table_args__ = (
        db.UniqueConstraint('machine_id', 'signal', name='uix_machine_signal'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'signal': self.signal,
            'min_val': self.min_val,
            'max_val': self.max_val,
            'warning': self.warning,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Alarm(db.Model):
    __tablename__ = 'alarms'

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey('machines.id', ondelete='CASCADE'), nullable=False
    )
    signal = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    value = db.Column(db.Float)
    status = db.Column(db.String(20), default='raised')
    acked = db.Column(db.Boolean, default=False)
    acked_at = db.Column(db.DateTime(timezone=True))
    raised_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
    )
    cleared_at = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'signal': self.signal,
            'severity': self.severity,
            'value': self.value,
            'status': self.status,
            'acked': self.acked,
            'acked_at': self.acked_at.isoformat() if self.acked_at else None,
            'raised_at': self.raised_at.isoformat() if self.raised_at else None,
            'cleared_at': self.cleared_at.isoformat() if self.cleared_at else None,
        }


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey('machines.id', ondelete='CASCADE'), nullable=False
    )
    ts = db.Column(db.DateTime(timezone=True), nullable=False)
    kind = db.Column(db.String(50), nullable=False)
    detail = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
    )

    __table_args__ = (
        db.UniqueConstraint('machine_id', 'ts', kind, name='uix_machine_ts_kind'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'ts': self.ts.isoformat() if self.ts else None,
            'kind': self.kind,
            'detail': self.detail,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class History(db.Model):
    __tablename__ = 'history'

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey('machines.id', ondelete='CASCADE'), nullable=False
    )
    signal = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    ts = db.Column(db.DateTime(timezone=True), nullable=False)
    recorded_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'signal': self.signal,
            'value': self.value,
            'ts': self.ts.isoformat() if self.ts else None,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
        }


class Stat(db.Model):
    __tablename__ = 'stats'

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey('machines.id', ondelete='CASCADE'), nullable=True
    )
    signal = db.Column(db.String(50), nullable=False)
    min_val = db.Column(db.Float, nullable=False)
    max_val = db.Column(db.Float, nullable=False)
    avg_val = db.Column(db.Float, nullable=False)
    out_of_limit = db.Column(db.Integer, default=0)
    window = db.Column(db.String(20), default='24h')
    ts = db.Column(db.DateTime(timezone=True), nullable=False)
    recorded_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'signal': self.signal,
            'min_val': self.min_val,
            'max_val': self.max_val,
            'avg_val': self.avg_val,
            'out_of_limit': self.out_of_limit,
            'window': self.window,
            'ts': self.ts.isoformat() if self.ts else None,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
        }


class Manifest(db.Model):
    __tablename__ = 'manifest'

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), nullable=False, default='1.0.0')
    reading_count = db.Column(db.Integer, default=0)
    machine_count = db.Column(db.Integer, default=0)
    last_update = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'reading_count': self.reading_count,
            'machine_count': self.machine_count,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Subscriber(db.Model):
    __tablename__ = 'subscribers'

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(
        db.Integer, db.ForeignKey('machines.id', ondelete='CASCADE'), nullable=True
    )
    client_id = db.Column(db.String(100), nullable=False, unique=True)
    topic = db.Column(db.String(200), nullable=False)
    connected = db.Column(db.Boolean, default=False)
    connected_at = db.Column(db.DateTime(timezone=True))
    disconnected_at = db.Column(db.DateTime(timezone=True))
    last_seen = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'client_id': self.client_id,
            'topic': self.topic,
            'connected': self.connected,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'disconnected_at': self.disconnected_at.isoformat() if self.disconnected_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Config(db.Model):
    __tablename__ = 'config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(200))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }