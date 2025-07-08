from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
your_number = os.getenv("YOUR_PERSONAL_NUMBER")
ngrok_url = os.getenv("NGROK_URL")  

client = Client(account_sid, auth_token)

call = client.calls.create(
    to=your_number,
    from_=twilio_number,
    url=f"{ngrok_url}/voice"
)

print(f"Calling {your_number}... Call SID: {call.sid}")
