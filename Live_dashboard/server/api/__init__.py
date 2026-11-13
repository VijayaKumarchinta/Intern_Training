
from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api")

from server.api import health_routes  # noqa: F401,E402
from server.api import telemetry_routes  # noqa: F401,E402
from server.api import summary_routes  # noqa: F401,E402
from server.api import event_routes  # noqa: F401,E402
from server.api import export_routes  # noqa: F401,E402

from server.api import replay_routes  # noqa: F401,E402
