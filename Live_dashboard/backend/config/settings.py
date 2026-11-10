from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_PATH = _PROJECT_ROOT / '.env'
if not _ENV_PATH.exists():
    raise RuntimeError(f'Environment file not found: {_ENV_PATH}. Copy .env.example to .env and fill in real values.')
load_dotenv(_ENV_PATH, override=False)

def _required(name: str) -> str:
    value = os.environ.get(name)
    if value is None or value == '':
        if name.endswith('_PASSWORD') or name.endswith('_USERNAME'):
            return ''
        raise RuntimeError(f'Required environment variable missing: {name}')
    return value

def _required_float(name: str) -> float:
    raw = _required(name)
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f'Environment variable {name} is not a float: {raw!r}') from exc

def _required_int(name: str) -> int:
    raw = _required(name)
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f'Environment variable {name} is not an int: {raw!r}') from exc

@dataclass(frozen=True)
class Settings:
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    mqtt_client_id_prefix: str
    mqtt_keepalive_seconds: int
    mqtt_topic_telemetry: str
    mqtt_topic_state: str
    mqtt_topic_command: str
    replay_interval_seconds: float
    database_url: str

    def telemetry_topic(self, machine_code: str) -> str:
        return self.mqtt_topic_telemetry.format(machine_code=machine_code)

    def state_topic(self, machine_code: str) -> str:
        return self.mqtt_topic_state.format(machine_code=machine_code)

    def command_topic(self, machine_code: str) -> str:
        return self.mqtt_topic_command.format(machine_code=machine_code)

def load_settings() -> Settings:
    return Settings(mqtt_host=_required('MQTT_HOST'), mqtt_port=_required_int('MQTT_PORT'), mqtt_username=_required('MQTT_USERNAME'), mqtt_password=_required('MQTT_PASSWORD'), mqtt_client_id_prefix=_required('MQTT_CLIENT_ID_PREFIX'), mqtt_keepalive_seconds=_required_int('MQTT_KEEPALIVE_SECONDS'), mqtt_topic_telemetry=_required('MQTT_TOPIC_TELEMETRY'), mqtt_topic_state=_required('MQTT_TOPIC_STATE'), mqtt_topic_command=_required('MQTT_TOPIC_COMMAND'), replay_interval_seconds=_required_float('REPLAY_INTERVAL_SECONDS'), database_url=_required('DATABASE_URL'))
