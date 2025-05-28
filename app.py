@app.route("/gpt-response", methods=["POST"])
def gpt_response():
    speech = request.form.get("SpeechResult")

    if not speech:
        # First call — no speech yet
        twiml = """
        <Response>
            <Say>Hi! This is Lina from TampaLawnPro. How can I help you today?</Say>
            <Gather input="speech" timeout="3" action="/gpt-response" method="POST">
                <Say>I'm listening...</Say>
            </Gather>
        </Response>
        """
        return Response(twiml, mimetype="text/xml")

    # If we got speech, process it via GPT and Polly
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
