from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_frozen import Freezer
import requests  # to make a request to another server

app = Flask(__name__)
CORS(app)
app.config.from_object(__name__)
app.config['FREEZER_DESTINATION'] = "out"
freezer = Freezer(app)

# Temporary storage for the last response
last_response = None
queue = 0

class ImageRequest():
    def __init__(self, prompt, artist):
        self._prompt = prompt
        self._artist = artist

    def send(self):
        global queue
        queue += 1
        # Send the request to the server
        return queue


@app.route('/', methods=['GET'])
def start():
    return render_template(
       'start.html'
   )

@app.route('/', methods=['POST'])
def prompt():
    global last_response
    # Receive input fields from the frontend
    data = request.json
    prompt = data.get('prompt')
    artist = data.get('artist')
    image_request = ImageRequest(prompt, artist)
    queue = image_request.send()
    
    last_response = prompt
    return jsonify({"status": "success", "data": {
        "prompt": prompt, 
        "artist": artist, 
        "queue": queue 
    }})

@app.route('/last', methods=['GET'])
def last():
    global last_response
    return jsonify(last_response if last_response else {"status": "no data"})

@app.route('/display', methods=['GET'])
def display():
    return 'This should be the frontend page that updates every 15s.'

if __name__ == '__main__':
    freezer.freeze()
    app.run(port=5000)