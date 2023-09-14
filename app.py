import os
import requests  # to make a request to another server
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_frozen import Freezer
from io import BytesIO


load_dotenv()

HF_ACCESS_TOKEN = os.environ.get('HF_ACCESS_TOKEN')
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
        API_URL = "https://msao2heoteruhalz.us-east-1.aws.endpoints.huggingface.cloud"
        headers = {"Authorization": f"Bearer {HF_ACCESS_TOKEN}"}

        def query(payload):
            return requests.post(API_URL, headers=headers, json=payload)
        
        response = query({
            "inputs": self._prompt,
        })

        # Send the image bytes directly as the response to the original request
        return response

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
    global queue
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
    # don't empty the queue, just return the last item
    elif len(queue) == 1:
        image_request = queue[0]
    else:
        image_request = queue.pop(0)

    response = image_request.send()
    image_bytes = response.content

    print(len(queue))
    print(image_request)
    print(response.content)

    content_type = response.headers['Content-Type'] # Content type received from the third-party server (e.g., 'image/png')
    return Response(image_bytes, content_type=content_type)

@app.route('/display', methods=['GET'])
def display():
    return render_template(
       'display.html'
   )

if __name__ == '__main__':
    # freezer.freeze()
    app.run(port=7000, debug=True)