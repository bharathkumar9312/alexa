# Requirements: Flask, Flask-CORS, SpeechRecognition, pyttsx3, pywhatkit, wikipedia, pyjokes, requests

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import speech_recognition as sr
import pyttsx3
import pywhatkit
import datetime
import wikipedia
import pyjokes
import requests
import time

app = Flask(__name__)
CORS(app)

# Initialize voice engine globally (thread-safe)
listener = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Female voice

# Lock to prevent multiple threads from speaking at once
talk_lock = threading.Lock()

# Add your NewsAPI key here
NEWS_API_KEY = 'bcb7ed8c1b544880b562458397bb478d'  # Replace with your real API key

def talk(text):
    print(f"Speaking: {text}")
    try:
        with talk_lock:
            engine.say(text)
            engine.runAndWait()
    except RuntimeError as e:
        print(f"[Error] Speaking failed: {e}")

def take_command():
    try:
        with sr.Microphone() as source:
            print('Listening...')
            listener.adjust_for_ambient_noise(source, duration=1)
            voice = listener.listen(source, timeout=5, phrase_time_limit=7)
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'alexa' in command:
                command = command.replace('alexa', '').strip()
            print(f"Command: {command}")
            return command
    except sr.UnknownValueError:
        print("[Error] Could not understand audio.")
        talk("Sorry, I could not understand. Please try again.")
    except sr.RequestError:
        print("[Error] Speech Recognition service unavailable.")
        talk("Speech recognition service is unavailable.")
    except Exception as e:
        print(f"[Error] General exception: {e}")
        talk("Sorry, something went wrong.")
    return ""

def get_latest_news():
    url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        if data['status'] == 'ok':
            headlines = [article['title'] for article in data['articles'][:3]]
            return headlines
    except Exception as e:
        print(f"[Error] News API request failed: {e}")
    return []

def run_alexa():
    command = take_command()
    if not command:
        return

    try:
        if 'play' in command:
            song = command.replace('play', '').strip()
            talk(f"Playing {song}")
            pywhatkit.playonyt(song)
        elif 'time' in command:
            time_now = datetime.datetime.now().strftime('%I:%M %p')
            talk(f'Current time is {time_now}')
        elif 'who is' in command:
            person = command.replace('who is', '').strip()
            try:
                 # Try direct lookup first
                info = wikipedia.summary(person, sentences=1)
                talk(info)
            except wikipedia.exceptions.DisambiguationError as e:
        # Too many matches, pick the first one from the options
                try:
                    info = wikipedia.summary(e.options[0], sentences=1)
                    talk(info)
                except Exception as e2:
                    print(f"[Error] Disambiguation fallback failed: {e2}")
                    talk("Your query is too broad. Please be more specific.")
            except wikipedia.exceptions.PageError:
                # Fallback: try search()
                search_results = wikipedia.search(person)
                if search_results:
                    try:
                        info = wikipedia.summary(search_results[0], sentences=1)
                        talk(info)
                    except Exception as e3:
                        print(f"[Error] Search fallback failed: {e3}")
                        talk("I couldn't find any information about that.")
                else:
                    talk("I couldn't find any information about that.")
            except Exception as e:
                print(f"[Error] Wikipedia general error: {e}")
                talk("Something went wrong while searching Wikipedia.")
        elif 'news' in command:
            try:
                response = requests.get(
                    f'https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}'
                )
                articles = response.json().get('articles', [])
                if articles:
                    headlines = [article['title'] for article in articles[:3]]
                    print(f"Headlines List: {headlines}")
                    talk("Here are the latest headlines.")
                    for idx, headline in enumerate(headlines, start=1):
                        talk(f"{idx}. {headline}")
                        time.sleep(1)
                else:
                    talk("Sorry, I couldn't find any news at the moment.")
            except Exception as e:
                print(f"[Error] Fetching news failed: {e}")
                talk("Sorry, I couldn't fetch the news.")
        elif 'date' in command:
            talk('Sorry, I have a headache.')
        elif 'are you single' in command:
            talk('I am in a relationship with wifi.')
        elif 'joke' in command:
            joke = pyjokes.get_joke()
            talk(joke)
        else:
            talk('Please say the command again.')
    except Exception as e:
        print(f"[Error] Processing command failed: {e}")
        talk("Something went wrong while processing your request.")

@app.route('/start-alexa', methods=['POST'])
def start_alexa():
    print("Received request to start Alexa...")
    threading.Thread(target=run_alexa).start()
    return jsonify({'message': 'Alexa started'})

if __name__ == '__main__':
    print("Starting Alexa Flask server...")

    with app.test_request_context():
        print("Registered URLs:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint}: {rule}")

    app.run(host='127.0.0.1', port=5000, debug=True)
