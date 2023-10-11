import os
import requests  # to make a request to another server
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from io import BytesIO
import qrcode

load_dotenv()
app = Flask(__name__)
port = 7001

# Configure the upload folder and allowed file extensions
UPLOAD_FOLDER = 'static/images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

height = 512
width = 512
steps = 50

queue = []
last_image = "intro.png"
time_per_turn = 30

def save(image, description, author):
    filename = f'{description}-{author}.png'
    filepath = f'{UPLOAD_FOLDER}{filename}'
    image.save(filepath)
    return filename

def improve_prompt(prompt):
    import openai

    openai.api_key = os.environ.get('OPENAI_API_KEY')

    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"i want you to act as an artistic designer and prompt engineer. I want you to improve a prompt that i'll give you for image generation. don't greet me, don't do anything else. The original prompt is enclosed in triple backticks. ```{prompt}```",
            temperature=0.9,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        )
        improved_prompt = response["choices"][0]["text"].strip()
        print(f"Improved prompt: {improved_prompt}")
        return improved_prompt
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return prompt  # Return the original prompt if there's an error


class ImageRequest():
    def __init__(self, prompt, author):
        self.prompt = prompt
        self.author = author

    def send(self):
        # image = self._send_test()
        # image = self._send_local()
        image = self._send_prod()
        return image

    def _send_test(self):
        from PIL import Image

        # Open an image file
        return Image.open(os.path.join(UPLOAD_FOLDER, 'test.png'))
    
    def _send_local(self):
        from diffusers import DiffusionPipeline

        repo_id = "../stable-diffusion-v1-5"
        pipe = DiffusionPipeline.from_pretrained(repo_id, use_safetensors=True)
        pipe = pipe.to("mps")

        # Recommended if your computer has < 64 GB of RAM
        pipe.enable_attention_slicing()

        # Results match those from the CPU device after the warmup pass.
        return pipe(self.prompt, num_inference_steps=steps).images[0]
    
    def _send_prod(self):
        import base64
        from PIL import Image

        prompt = self.prompt
        prompt = improve_prompt(prompt)

        api_host = 'https://api.stability.ai'
        engine_id = 'stable-diffusion-xl-beta-v2-2-2'    

        url = f"{api_host}/v1/generation/{engine_id}/text-to-image"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {os.environ.get('STABILITY_API_KEY')}"
        }
        payload = {}
        payload['text_prompts'] = [{"text": f"{prompt}"}]
        payload['cfg_scale'] = 7
        payload['clip_guidance_preset'] = 'FAST_BLUE'
        payload['height'] = height
        payload['width'] = width
        payload['samples'] = 1
        payload['steps'] = steps

        response = requests.post(url,headers=headers,json=payload)

        #Processing the response
        if response.status_code == 200:
            data = response.json()
            for i, image in enumerate(data["artifacts"]):
                return Image.open(BytesIO(base64.b64decode(image["base64"])))


    def __str__(self):
        return f"{self.prompt} by {self.author}"


# ROUTES

@app.route('/', methods=['GET'])
def start():
    global time_per_turn, last_image
    print(time_per_turn)
    return render_template(
       'start.html', last_image=f"{UPLOAD_FOLDER}{last_image}", time_per_turn=time_per_turn
   )


@app.route('/display', methods=['GET'])
def display():
    global time_per_turn
    return render_template(
       'display.html', time_per_turn = time_per_turn
   )


@app.route('/prompt', methods=['GET'])
def get_prompt():
    global last_image
    return jsonify({"last_image": f"{UPLOAD_FOLDER}{last_image}"})

@app.route('/prompt', methods=['POST'])
def post_prompt():
    # Receive input fields from the frontend
    global queue
    data = request.json
    
    prompt = data.get('prompt')
    author = data.get('artist')
    print(f"Received prompt: {prompt} by {author}")

    if prompt is None or prompt == "":
        return jsonify({"status": "error", "message": "prompt is missing"})

    image_request = ImageRequest(prompt, author)
    queue.append(image_request)

    return jsonify({"status": "success", "data": {
        "prompt": prompt,
        "author": author,
        "queue": [item.__str__() for item in queue]
    }})


@app.route('/last', methods=['GET'])
def last():
    global queue, last_image
    if len(queue) == 0:
        return jsonify({"last_image": f"{UPLOAD_FOLDER}intro.png", "description": "", "author": ""})
    else:
        image_request = queue.pop(0)

    image = image_request.send()
    last_image = save(image, image_request.prompt, image_request.author)

    print(f"Image Generated: {image_request}")
    
    return jsonify({"last_image": f"{UPLOAD_FOLDER}{last_image}", "description": image_request.prompt, "author": image_request.author})


def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        ip = response.json()['ip']
        print(f"Detected public IP: {ip}")
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
        img.save(f'{UPLOAD_FOLDER}public_ip_qr_code.png')
        print(f"QR code generated for {url} and saved as 'public_ip_qr_code.png'")
    except Exception as e:
        print(f"Could not generate QR code: {e}")


if __name__ == '__main__':
    ip = get_public_ip()
    # ip = "192.168.0.15"
    if ip:
        generate_qr_code(ip, port)
    
    app.run(host='0.0.0.0', port=port, debug=True)
