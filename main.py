import string
from openai import OpenAI
from flask import request, Flask
import os
import requests
from dotenv import load_dotenv
import random
from time import sleep

load_dotenv()
GRAPH_URL = os.getenv("GRAPH_URL") ##update version number as needed
TOKEN = os.getenv("VERIFY_TOKEN")
W_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
#MY_NUMBER_ID = os.getenv("WHATSAPP_NUMBER_ID")
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
W_BUSINESS_ID = os.getenv("WAHTSAPP_BUSINESS_ID") ##This is the whatsapp business number

app = Flask(__name__)


def recieve_message():
    data = request.get_json()
    if data:
        if "messages" in data["entry"][0]["changes"][0]["value"]:
            messages = data["entry"][0]["changes"][0]["value"]["messages"]
            if messages:
                for message in messages:
                    sender_number = str(message["from"])
                    message_type = message["type"]

                    # filter audio messages
                    if message_type == "audio":
                        audio = message["audio"]
                        message_id = audio["id"]
                        recieve_url = GRAPH_URL + message_id + "/?access_token=" + W_API_TOKEN
                        return [recieve_url, sender_number]
                    else:
                        text = ["הקליטו או העבירו לי הודעה קולית בכל שפה, וקבלו טקסט 💫"]
                        send_message(text, sender_number)
                        exit()


def download_media(recieve_url):
    header = {'Authorization': f'Bearer {W_API_TOKEN}'}
    response = requests.get(recieve_url, headers=header, allow_redirects=True)
    if response.status_code == 200:
        json_response = response.json()
        media_url = json_response.get('url')
        if media_url:
            media_response = requests.get(media_url, headers=header, allow_redirects=True)
            #print(media_response)
            content_type = media_response.headers.get('Content-Type', '')
            #print(content_type)
            if media_response.status_code == 200:
                content_type = media_response.headers.get('Content-Type')
                if content_type and 'audio' in content_type:
                    #print("audio in content type")
                    audio_format = content_type
                    filename = ''.join(
                    random.choice(string.ascii_letters + string.digits) for _ in
                        range(10)) + '.mp3'
                    open(filename + '.ogg', 'wb').write(media_response.content)
                    filename = filename + '.ogg'
                    #print(audio_format)
                    return filename


def transcribe_audio(filename):
    client = OpenAI()
    audio_file = open(filename, "rb")

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    transcript = transcript.text

    texts = [transcript[i:i + 1600] for i in
        range(0, len(transcript), 1600)]
    print("transcribed successfully: ", texts)
    os.remove(filename)
    return texts

def send_message(texts, sender_number):
    for text in texts:
        header = {
            'Authorization': f"Bearer {W_API_TOKEN}",
            'Content_type': 'application/json'
        }
        url = GRAPH_URL + W_BUSINESS_ID + "/messages"
        #print(url)
        payload = {
            'messaging_product': 'whatsapp',
            'to': sender_number,
            'text': {'body': text}
        }
        response = requests.post(url=url, json=payload, headers=header)
        if response.status_code == 200:
            print(response, response.status_code)

            sleep(1)
            if random.random() < 0.2:
                text = [
                    '''הי! 👋
                הבוט שלנו, "דברו אליי", נוצר כדי להקל עליכם את החיים, והתגובות ממש כיפיות 🥰
                אנחנו שמחים לראות את האהבה והתמיכה שלכם, ולמרות שאנחנו משאירים את השירות חינמי, קצת עזרה לא תזיק. 🙏
                אם אתם מרגישים שהשירות שלנו מועיל לכם, נשמח אם תוכלו לתמוך בנו בכל סכום שמתאים לכם. 💖 זה יעזור לנו להמשיך לשפר את הבוט ולשמור אותו פעיל לרווחת הציבור. 🌱
                https://www.paypal.com/donate/?hosted_button_id=J9V26WN5BT2AQ
                מוזמנים לשתף את הבוט עם חברים ומשפחה ולקרוא עוד על העשייה שלנו כאן https://sofi.coop
                תודה על התמיכה שלכם, 🙏
                קואופרטיב סופי - בית תוכנה חברתי.'''
                        ]
                send_message(text, sender_number)
                return
            else:
                retun

        else:
            return




@app.route("/", methods=['GET'])
#a function to verify the callback url used for the webhook
def webhook_verification():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    print("mode: ", mode, "token: ", token)
    if mode == 'subscribe' and token == TOKEN:
        print("webhook verified")
        return challenge, 200
    else:
        return "webhook verification faliure", 403


@app.route('/', methods=['GET','POST'])

def webhook():
    result = recieve_message()
    if result:
        [receive_url, sender_number] = result


        ## For messages sent from non-users
        if receive_url == "non-user message format":
            print("non-user message")
            return "non_user message", 200

        ##For messages from users
        else:
            filename = download_media(receive_url)
            texts = transcribe_audio(filename)
            send_message(texts, sender_number)

            return "message transcribed", 200
    else:
        return "non voice message", 200



if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
