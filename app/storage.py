import os
import json

CONVO_DIR = "conversations"
SILENCE_TRACKER = {}

os.makedirs(CONVO_DIR, exist_ok=True)

def get_conversation(call_sid):
    path = os.path.join(CONVO_DIR, f"{call_sid}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def append_to_conversation(call_sid, message):
    convo = get_conversation(call_sid)
    convo.append(message)
    path = os.path.join(CONVO_DIR, f"{call_sid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(convo, f, indent=2)

def reset_silence(call_sid):
    SILENCE_TRACKER[call_sid] = 0

def increment_silence(call_sid):
    SILENCE_TRACKER[call_sid] = SILENCE_TRACKER.get(call_sid, 0) + 1
    return SILENCE_TRACKER[call_sid]
