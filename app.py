from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from flask_frozen import Freezer
import requests  # to make a request to another server

app = Flask(__name__)
# app.config['FREEZER_DESTINATION'] = "out"
# freezer = Freezer(app)
CORS(app)

queue = []

class ImageRequest():
    def __init__(self, prompt):
        self._prompt = prompt

    def send(self):
        # Send the server response
        return self._prompt

    def __str__(self):
        return self._prompt
    

# ROUTES

@app.route('/', methods=['GET'])
def start():
    return render_template(
       'start.html'
   )

@app.route('/prompt', methods=['POST'])
def receive_request():
    # Receive input fields from the frontend
    data = request.json
    print(data)
    prompt = data.get('prompt')
    artist = data.get('artist')
    image_request = ImageRequest(prompt)
    queue.append(image_request)
    
    return jsonify({"status": "success", "data": {
        "prompt": prompt, 
        "artist": artist, 
        "queue_position": len(queue)
    }})

@app.route('/last', methods=['GET'])
def last():
    global queue
    if len(queue) == 0:
        return jsonify({"status": "no data"})
    
    image_request = queue.pop(0)
    response = image_request.send()
    return jsonify(response)

@app.route('/display', methods=['GET'])
def display():
    return render_template(
       'display.html'
   )

if __name__ == '__main__':
    # freezer.freeze()
    app.run(port=5000, debug=True)