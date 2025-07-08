from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print(os.getenv("OPENAI_API_KEY"))

# List all models available to this API key
models = client.models.list()

for model in models.data:
    print(model.id)
