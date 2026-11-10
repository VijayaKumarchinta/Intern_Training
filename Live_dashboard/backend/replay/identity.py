import hashlib

def compute_message_id(
    dataset_id: str,
    replay_session_id: str,
    replay_cycle: int,
    source_sequence: int,
) -> str:
    payload = f"{dataset_id}:{replay_session_id}:{replay_cycle}:{source_sequence}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
