from flask import Flask, request, Response
import openai
import os
import boto3
import uuid
from pathlib import Path

app = Flask(__name__)  # This must come BEFORE using @app.route

openai.api_key = os.environ["OPENAI_API_KEY"]

audio_dir = Path("static/audio")
audio_dir.mkdir(parents=True, exist_ok=True)

# AWS Polly client
polly = boto3.client(
    "polly",
    region_name=os.environ["AWS_REGION"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
)

@app.route("/gpt-response", methods=["POST"])
def gpt_response():
    speech = request.form.get("SpeechResult")
    if not speech:
        twiml = """
        <Response>
            <Say>Hi! This is Lina from TampaLawnPro. How can I help you today?</Say>
            <Gather input="speech" timeout="3" action="/gpt-response" method="POST">
                <Say>I'm listening...</Say>
            </Gather>
        </Response>
        """
        return Response(twiml, mimetype="text/xml")

    chat = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You're Lina, the helpful voice of TampaLawnPro."},
            {"role": "user", "content": speech}
        ]
    )
    reply = chat.choices[0].message.content

    filename = f"{uuid.uuid4()}.mp3"
    filepath = audio_dir / filename

    polly_response = polly.synthesize_speech(
        Text=reply,
        OutputFormat="mp3",
        VoiceId="Joanna"
    )

    with open(filepath, "wb") as f:
        f.write(polly_response['AudioStream'].read())

    audio_url = f"https://{request.host}/static/audio/{filename}"
    twiml = f"""
    <Response>
        <Play>{audio_url}</Play>
        <Gather input="speech" timeout="3" action="/gpt-response" method="POST">
            <Say>Is there anything else I can help you with?</Say>
        </Gather>
    </Response>
    """
    return Response(twiml, mimetype="text/xml")

@app.route("/")
def index():
    return "TampaLawnPro AI voicebot is live!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
