from telethon.sync import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    PasswordHashInvalidError,
)
from telethon.sessions import StringSession
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/generate_session', methods=['POST'])
def generate_session():
    data = request.json

    # Ensure required fields are present
    if not all(k in data for k in ('api_id', 'api_hash', 'phone_number')):
        return jsonify({"error": "Missing required fields: api_id, api_hash, or phone_number."}), 400

    api_id = data['api_id']
    api_hash = data['api_hash']
    phone_number = data['phone_number']

    # Initialize Telegram client
    client = TelegramClient(StringSession(), api_id, api_hash)

    try:
        # Connect to Telegram
        client.connect()
        if not client.is_user_authorized():
            # Send OTP
            client.send_code_request(phone_number)

            # Get OTP from user input (via API request)
            if 'otp' not in data:
                return jsonify({"error": "OTP required. Send the OTP to complete the process."}), 400

            otp = data['otp'].replace(" ", "")

            try:
                client.sign_in(phone_number, otp)
            except SessionPasswordNeededError:
                if 'password' not in data:
                    return jsonify({"error": "Two-step verification password required."}), 400

                password = data['password']
                try:
                    client.sign_in(password=password)
                except PasswordHashInvalidError:
                    return jsonify({"error": "Invalid two-step verification password."}), 401
            except PhoneCodeInvalidError:
                return jsonify({"error": "Invalid OTP."}), 401

        # Generate and return session string
        session_string = client.session.save()
        return jsonify({"session_string": session_string}), 200

    except PhoneNumberInvalidError:
        return jsonify({"error": "Invalid phone number."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        client.disconnect()

if __name__ == '__main__':
    app.run(debug=True)
