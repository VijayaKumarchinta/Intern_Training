import sys
from pathlib import Path
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / 'backend'))
from config.settings import load_settings
from contract.schema import MACHINE_CODE, SCHEMA_VERSION
from mqtt.client import MqttClient

def main() -> int:
    settings = load_settings()
    sample = {'schema_version': SCHEMA_VERSION, 'machine_code': MACHINE_CODE, 'event_timestamp': '2026-04-17T12:09:53.162', 'smoke': True}
    with MqttClient(settings, MACHINE_CODE) as client:
        import time
        time.sleep(0.5)
        if not client.is_connected():
            print('FAIL: client did not connect')
            return 1
        client.publish(settings.telemetry_topic(MACHINE_CODE), sample, qos=1, retain=False)
        time.sleep(0.5)
    print('OK: published state and telemetry, then disconnected cleanly')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
