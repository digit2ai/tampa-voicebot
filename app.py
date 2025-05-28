from flask import Flask, request, Response
import openai
import os
import boto3
import uuid
from pathlib import Path

app = Flask(__name__)
openai.api_key = os.environ["OPENAI_API_KEY"]

# Directory to save audio responses
audio_dir = Path("static/audio")
audio_dir.mkdir(parents=True, exist_ok=True)

# AWS Polly client setup
polly = boto3.client(
    "polly",
    region_name=os.environ["AWS_REGION"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
)

@app.route("/gpt-response", methods=["POST"])
def gpt_response():
    user_input = request.form.get("SpeechResult", "").strip()

    if not user_input:
        fallback_twiml = """
        <Response>
            <Say>I didn't catch that. Can you please repeat?</Say>
            <Gather input="speech" timeout="3" action="/gpt-response" method="POST" />
        </Response>
        """
        return Response(fallback_twiml, mimetype="text/xml")

    # Call OpenAI for response
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You're Lina, the helpful voice of TampaLawnPro."},
            {"role": "user", "content": user_input}
        ]
    )
    reply_text = response.choices[0].message.content.strip()

    # Convert reply to MP3 using Polly
    filename = f"{uuid.uuid4()}.mp3"
    filepath = audio_dir / filename

    polly_response = polly.synthesize_speech(
        Text=reply_text,
        OutputFormat="mp3",
        VoiceId="Joanna"
    )

    with open(filepath, "wb") as f:
        f.write(polly_response['AudioStream'].read())

    audio_url = f"https://{request.host}/static/audio/{filename}"
    
    # Return TwiML to play audio and gather again
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
    return "✅ TampaLawnPro AI voicebot is live and listening!"

# Required for Render hosting
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
