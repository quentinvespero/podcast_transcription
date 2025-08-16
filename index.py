import os
from mistralai import Mistral
from dotenv import load_dotenv
import time

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")

model = "voxtral-mini-latest"

# initialise mistral client
client = Mistral(api_key=api_key)

# getting transcription
with open('./s10e43_trimmed_benchmark.mp3', 'rb') as file:
    transcription_response = client.audio.transcriptions.complete(
        timestamp_granularities=['segment'],
        language='fr',
        model=model,
        file={
            'content': file ,
            'file_name':'./s10e43_trimmed_benchmark.mp3'
            },
)

print(transcription_response.language, transcription_response.segments)