import os
from openai import OpenAI
from dotenv import load_dotenv
from app.storage import get_conversation

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key = OPENAI_API_KEY)

def get_ai_response(call_sid: str) -> str:
    history = get_conversation(call_sid) or []
    messages = [{"role": "system", "content": "You are a helpful AI assistant."}] + history

    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

def analyze_conversation(text: str):
    prompt = f"""
Transcript:
{text}

1. Summarize this conversation in 2–3 sentences.
2. Analyze the overall sentiment (Positive, Neutral, Negative) with a short reason.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    content = response.choices[0].message.content

    summary_line = None
    sentiment_line = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("1."):
            summary_line = line[2:].strip()
        elif line.startswith("2."):
            sentiment_line = line[2:].strip()

    return {
        "summary": summary_line or "Summary not found.",
        "sentiment": sentiment_line or "Sentiment not found."
    }


def generate_summary_report(call_sid: str):
    convo = get_conversation(call_sid)
    if not convo:
        raise ValueError(f"No conversation found for {call_sid}")

    transcript = "\n".join([f"{msg['role']}: {msg['content']}" for msg in convo])
    result = analyze_conversation(transcript)

    os.makedirs("summaries", exist_ok=True)
    path = f"summaries/{call_sid}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"CallSid: {call_sid}\n\n")
        f.write("Summary:\n" + result["summary"] + "\n\n")
        f.write("Sentiment:\n" + result["sentiment"] + "\n\n")
        f.write("Transcript:\n" + transcript)
