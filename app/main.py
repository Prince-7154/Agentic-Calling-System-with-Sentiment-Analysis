# app/main.py
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from twilio.twiml.voice_response import VoiceResponse
import logging

from app.storage import (
    append_to_conversation,
    get_conversation,
    reset_silence,
    increment_silence
)

from app.llm_utils import (
    get_ai_response,
    analyze_conversation,
    generate_summary_report
)

import os


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
logging.basicConfig(level=logging.INFO)

GOODBYE_PHRASES = ["bye", "goodbye", "see you", "talk later", "thank you", "thanks, bye"]


@app.post("/voice")
async def voice():
    response = VoiceResponse()
    response.say("Hello! I am your AI assistant. How can I help you? ", voice="Polly.Joanna")
    response.gather(input="speech", action="/gather", method="POST", timeout=5)
    return PlainTextResponse(str(response))


@app.post("/gather")
async def gather(CallSid: str = Form(...), SpeechResult: str = Form("")):
    logging.info(f"{CallSid} - User said: {SpeechResult}")
    user_input = SpeechResult.strip().lower()
    response = VoiceResponse()


    if not user_input:
        silence_count = increment_silence(CallSid)
        logging.info(f"{CallSid} - Silence count: {silence_count}")

        if silence_count >= 2:
            
            ai_reply = "Ending the call. Thank you for speaking with me."
            append_to_conversation(CallSid, {"role": "assistant", "content": ai_reply})
            _speak_response(response, ai_reply)
            response.hangup()

            try:
                generate_summary_report(CallSid)
                logging.info(f"Summary generated for {CallSid}")
            except Exception as e:
                logging.error(f"Failed to generate summary for {CallSid}: {e}")

            return PlainTextResponse(str(response))

        _speak_response(response, "I didn’t catch that. Could you please repeat?")
        response.gather(input="speech", action="/gather", method="POST", timeout=5)
        return PlainTextResponse(str(response))

    reset_silence(CallSid)

    append_to_conversation(CallSid, {"role": "user", "content": SpeechResult})

    if any(bye in user_input for bye in GOODBYE_PHRASES):
        ai_reply = "Thank you for the conversation. Have a great day!"
        append_to_conversation(CallSid, {"role": "assistant", "content": ai_reply})
        _speak_response(response, ai_reply)
        response.hangup()

        try:
            generate_summary_report(CallSid)
            logging.info(f" Summary generated for {CallSid}")
        except Exception as e:
            logging.error(f" Failed to generate summary for {CallSid}: {e}")

        return PlainTextResponse(str(response))
    
    try:
        ai_reply = get_ai_response(CallSid)
        append_to_conversation(CallSid, {"role": "assistant", "content": ai_reply})
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        ai_reply = "Sorry, I encountered an error while trying to respond."

    _speak_response(response, ai_reply)
    response.gather(input="speech", action="/gather", method="POST", timeout=5)
    return PlainTextResponse(str(response))


def _speak_response(response, message):
    """Split long messages into natural-sounding chunks for Twilio"""
    parts = message.split(". ")
    for sentence in parts:
        if sentence.strip():
            response.say(sentence.strip(), voice="Polly.Joanna")


@app.get("/summary/{call_sid}", response_class=HTMLResponse)
async def summary(call_sid: str, request: Request):
    conversation = get_conversation(call_sid)
    if not conversation:
        return HTMLResponse(f"<h2>No conversation found for call: {call_sid}</h2>")

    transcript = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])
    logging.info(f"Transcript:\n{transcript}")

    result = analyze_conversation(transcript)

    return templates.TemplateResponse("summary.html", {
        "request": request,
        "call_sid": call_sid,
        "transcript": transcript,
        "summary": result["summary"],
        "sentiment": result["sentiment"]
    })


@app.get("/summary_file", response_class=HTMLResponse)
async def summary_form(request: Request):
    return templates.TemplateResponse("summary_form.html", {"request": request})


@app.post("/summary_file", response_class=HTMLResponse)
async def summary_post(request: Request, call_sid: str = Form(...)):
    """Redirect to summary detail page"""
    return RedirectResponse(url=f"/summary_file/{call_sid}", status_code=303)


@app.get("/summary_file/{call_sid}", response_class=HTMLResponse)
async def summary_file(request: Request, call_sid: str):
    filepath = f"summaries/{call_sid}.txt"
    if not os.path.exists(filepath):
        return templates.TemplateResponse("summary_not_found.html", {"request": request, "call_sid": call_sid})

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    return templates.TemplateResponse("summary_display.html", {
        "request": request,
        "call_sid": call_sid,
        "content": content.replace("\n", "<br>")
    })


