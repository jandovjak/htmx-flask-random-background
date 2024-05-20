from flask import Flask, request, send_file
from flask_cors import CORS
from PIL import Image
from io import BytesIO
from Crypto.Hash import SHA3_224
import base64

app = Flask(__name__)
CORS(app)

BYTES_PER_PIXEL = 3
GENERATED_HEIGHT = 1
DEFAULT_WIDTH = 480
DEFAULT_HEIGHT = 270


def bytes_padding(bytes):
    padding_size = len(bytes) % BYTES_PER_PIXEL
    padding = [0] * padding_size
    return bytearray(bytes) + bytearray(padding)


def bytes_from_hash(hash):
    hash_bytes = bytearray(bytes.fromhex(hash))
    return bytes_padding(hash_bytes)


def image_from_bytes(bytes):
    width = len(bytes) // BYTES_PER_PIXEL
    image = Image.new("RGB", (width, GENERATED_HEIGHT))
    for i in range(width):
        r = bytes[i * BYTES_PER_PIXEL]
        g = bytes[i * BYTES_PER_PIXEL + 1]
        b = bytes[i * BYTES_PER_PIXEL + 2]
        image.putpixel((i, 0), (r, g, b))
    return image


def image_from_hash(hash):
    hash_bytes = bytes_from_hash(hash)
    return image_from_bytes(hash_bytes)


def base64_from_bytes(bytes):
    return base64.b64encode(bytes).decode("utf-8")     


def base64_from_image(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    return "data:image/png;base64," + base64_from_bytes(image_bytes)


def hash_from_text(text):
    text_bytes = text.encode('utf-8')
    hash = SHA3_224.new()
    hash.update(text_bytes)
    return hash.hexdigest()


def fill_image(image, start_x, start_y, width, height, color):
    for i in range(width):
        for j in range(height):
            image.putpixel((start_x + i, start_y + j), color)
    return image


def scale_image(image, scale_width, scale_height):
    width = image.width * scale_width
    height = image.height * scale_height
    new_image = Image.new("RGB", (width, height))
    for i in range(image.width):
        for j in range(image.height):
            new_image = fill_image(new_image, i * scale_width,
                                   j * scale_height, scale_width,
                                   scale_height, image.getpixel((i, j)))
    return new_image


def image_from_base64(encoded_image):
    image_bytes = base64.b64decode(encoded_image)
    image_stream = BytesIO(image_bytes)
    return Image.open(image_stream)


@app.route('/background/random', methods=['GET'])
def text_image_hash():
    text = request.args.get('text')
    hash = hash_from_text(text)
    image = image_from_hash(hash)
    base64_image = base64_from_image(image)
    return f'<img id="background-image" src="{base64_image}"/>'


@app.route('/background/download', methods=['GET'])
def download():
    width = DEFAULT_WIDTH
    height = DEFAULT_HEIGHT
    encoded_image = request.args.get('image')
    image = image_from_base64(encoded_image)
    image = scale_image(image, width, height)
    image_stream = BytesIO()
    image.save(image_stream, format='PNG')
    image_stream.seek(0)
    return send_file(image_stream, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True)
