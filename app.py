import os
import requests  # to make a request to another server
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file
# from flask_ngrok import run_with_ngrok
from flask_cors import CORS
from io import BytesIO
import qrcode

# load_dotenv()
app = Flask(__name__)
port = 7001

# Configure the upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app)
# run_with_ngrok(app)

queue = []

def save(image, description, author):
    filename = f'{UPLOAD_FOLDER}{description}-{author}.png'
    image.save(filename)
    return filename

class ImageRequest():
    def __init__(self, prompt, author):
        self.prompt = prompt
        self.author = author

    def send(self):
        image = self._send_test()
        # image = self._send_prod()
        return image

    def _send_test(self):
        from PIL import Image

        # Open an image file
        return Image.open(os.path.join(UPLOAD_FOLDER, 'test.png'))
    
    def _send_prod(self):
        from diffusers import DiffusionPipeline
        import torch

        repo_id = "../stable-diffusion-v1-5"
        pipe = DiffusionPipeline.from_pretrained(repo_id, use_safetensors=True)
        pipe = pipe.to("mps")

        # Recommended if your computer has < 64 GB of RAM
        pipe.enable_attention_slicing()

        # Results match those from the CPU device after the warmup pass.
        return pipe(self.prompt, num_inference_steps=25).images[0]

    def __str__(self):
        return f"{self.prompt} by {self.author}"


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
    author = data.get('artist')
    image_request = ImageRequest(prompt, author)
    queue.append(image_request)

    return jsonify({"status": "success", "data": {
        "prompt": prompt,
        "author": author,
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

    image = image_request.send()
    filename = save(image, image_request.prompt, image_request.author)

    print(f"queue {len(queue)}")
    print(f"request {image_request}")
    print(f"filename {filename}")

    # Send the local file path back to the frontend
    return send_file(filename, mimetype='image/png')


@app.route('/display', methods=['GET'])
def display():
    return render_template(
       'display.html'
   )



def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        ip = response.json()['ip']
        print(response.json())
        return ip
    except Exception as e:
        print(f"Could not fetch public IP: {e}")
        return None

def generate_qr_code(ip, port):
    try:
        url = f"http://{ip}:{port}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save('public_ip_qr_code.png')
        print(f"QR code generated for {url} and saved as 'public_ip_qr_code.png'")
    except Exception as e:
        print(f"Could not generate QR code: {e}")


if __name__ == '__main__':
    # freezer.freeze()
    ip = get_public_ip()
    if ip:
        generate_qr_code(ip, port)
    
    app.run(host='0.0.0.0', port=port, debug=True)
