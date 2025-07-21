from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Twilio setup
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_sms_from = os.getenv("TWILIO_SMS_FROM")
twilio_sms_to = os.getenv("TWILIO_SMS_TO")
twilio_whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM")
twilio_whatsapp_to = os.getenv("TWILIO_WHATSAPP_TO")

client = Client(account_sid, auth_token)

# Email setup
email_sender = os.getenv("EMAIL_SENDER")
email_receiver = os.getenv("EMAIL_RECEIVER")
email_password = os.getenv("EMAIL_PASSWORD")

@app.route("/notify", methods=["GET"])
def notify():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not lat or not lon:
        return jsonify({"error": "Missing 'lat' or 'lon' parameters"}), 400

    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    message_body = f"🚨 Alert!\nLocation: {maps_url}"

    result = {}

    # Send WhatsApp
    try:
        whatsapp_msg = client.messages.create(
            from_=twilio_whatsapp_from,
            to=twilio_whatsapp_to,
            body=message_body
        )
        result["whatsapp_status"] = "sent"
        result["whatsapp_sid"] = whatsapp_msg.sid
    except Exception as e:
        result["whatsapp_status"] = "failed"
        result["whatsapp_error"] = str(e)

    # Send SMS
    try:
        sms_msg = client.messages.create(
            from_=twilio_sms_from,
            to=twilio_sms_to,
            body=message_body
        )
        result["sms_status"] = "sent"
        result["sms_sid"] = sms_msg.sid
    except Exception as e:
        result["sms_status"] = "failed"
        result["sms_error"] = str(e)

    # Send Email
    try:
        subject = "🚨 AlertBuddy: Location Notification"
        body = f"""
🚨 Alert Triggered!

The user has shared their location:
Latitude: {lat}
Longitude: {lon}

Google Maps Link: {maps_url}
"""
        msg = MIMEMultipart()
        msg["From"] = email_sender
        msg["To"] = email_receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)

        result["email_status"] = "sent"
    except Exception as e:
        result["email_status"] = "failed"
        result["email_error"] = str(e)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
