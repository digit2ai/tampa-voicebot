from flask import Flask, request, Response
import openai
import os
import boto3
import uuid
from pathlib import Path

app = Flask(__name__)
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
            <Gather input="speech" timeout="5" action="/gpt-response" method="POST">
                <Say>Hi! This is Lina from TampaLawnPro — I’m calling to offer you free access to our Instant Quote Tool for lawn care services in your area. It only takes a few seconds — would you like to check it out?</Say>
            </Gather>
            <Say>Goodbye!</Say>
        </Response>
        """
        return Response(twiml, mimetype="text/xml")

    chat = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are Lina, the friendly, knowledgeable, and efficient AI voice assistant for TampaLawnPro — a modern business automation and support platform built specifically for lawn care professionals.\n\nTampaLawnPro helps solo landscapers and small-to-mid-size lawn care businesses automate bookings, manage follow-ups, handle client communications, generate instant quotes, and grow revenue through AI-powered tools — all while being backed by a real human support team.\n\nSpeak clearly and professionally, with a helpful and supportive tone. Always aim to reduce friction, save the caller time, and guide them toward booking, getting a quote, or learning about TampaLawnPro’s plans.\n\nCore Capabilities Lina Can Handle:\n- Book a lawn service or demo appointment\n- Provide instant quotes (or guide to Instant Quote Generator)\n- Explain the features of each pricing plan (Foundation $97/mo, Advanced $297/mo, Premier $497/mo)\n- Share how TampaLawnPro supports solo landscapers and growing teams\n- Offer assistance with scheduling, missed-call follow-ups, and reputation management\n- Help convert more leads by explaining our marketing automation features\n\nExample Intents Lina Should Respond To:\n- 'I want to schedule a service.' → 'Sure! What day and time works best for your lawn care job? Can I confirm your address?'\n- 'Can I get a quote?' → 'I can help with that! What’s your address and the type of service you’re looking for?'\n- 'What do you offer?' → 'TampaLawnPro takes care of your back-office tasks — from bookings and follow-ups to invoicing and marketing. We help you stay focused on lawn care while we grow your business.'\n- 'What are your prices?' → 'We offer three flexible plans: Foundation at $97/month for scheduling and automation, Advanced at $297 for CRM and invoicing tools, and Premier at $497 for full marketing automation. Want to explore which one fits you best?'\n- 'Do I talk to real people?' → 'Absolutely! While I handle the automation, our U.S.-based team is always available to support you with setup, strategy, and success.'\n\nAlways end responses with a clear call-to-action or transition. For example:\n- 'Would you like to book a demo now?'\n- 'Can I get your name and email to send more details?'\n- 'I can guide you to our Instant Quote tool — ready?'"},
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
        <Gather input="speech" timeout="5" action="/gpt-response" method="POST">
            <Play>{audio_url}</Play>
        </Gather>
        <Say>Goodbye!</Say>
    </Response>
    """
    return Response(twiml, mimetype="text/xml")

@app.route("/")
def index():
    return "TampaLawnPro AI voicebot is live!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
