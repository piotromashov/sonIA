from flask import Flask, request, jsonify
from flask_cors import CORS
import requests  # to make a request to another server

app = Flask(__name__)
CORS(app)

# Temporary storage for the last response
last_response = None

@app.route('/start', methods=['GET'])
def start():
    return 'This should be a frontend page with input fields and a send button.'

@app.route('/prompt', methods=['POST'])
def prompt():
    global last_response
    # Receive input fields from the frontend
    data = request.json
    field1 = data.get('field1')
    field2 = data.get('field2')
    
    # Make a request to another server (Replace with the actual URL and data)
    # response = requests.post('http://example.com/another_server', json={"field1": field1, "field2": field2})
    
    # Store the response in memory
    # last_response = response.json()
    last_response = field1
    return jsonify({"status": "success"})

@app.route('/last', methods=['GET'])
def last():
    global last_response
    return jsonify(last_response if last_response else {"status": "no data"})

@app.route('/display', methods=['GET'])
def display():
    return 'This should be the frontend page that updates every 15s.'

if __name__ == '__main__':
    app.run(port=5000)