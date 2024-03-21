from flask import Flask, render_template, request
from PIL import Image
import pytesseract
import cv2
from pytesseract import Output
import os
import base64
from io import BytesIO

app = Flask(__name__)

# Set upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part'

        file = request.files['file']

        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return 'No selected file'

        if file:
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Perform OCR using pytesseract
            try:
                text, img_with_boxes_str = ocr_with_bounding_boxes(file_path)
            except Exception as e:
                return f'Error processing file: {str(e)}'

            return render_template('result.html', image_with_boxes=img_with_boxes_str, ocr_text=text)

    return 'Error uploading file'


def ocr_with_bounding_boxes(image_path):
    img = cv2.imread(image_path)

    # Perform OCR and get bounding boxes
    d = pytesseract.image_to_data(img, output_type=Output.DICT)

    # Draw bounding boxes on the image
    n_boxes = len(d['text'])
    for i in range(n_boxes):
        if int(d['conf'][i]) > 60:
            (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
            img = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Convert image to RGB format for PIL
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_with_boxes = Image.fromarray(img_rgb)

    # Convert image to Base64-encoded string
    buffered = BytesIO()
    img_with_boxes.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # Extract OCR text
    text = pytesseract.image_to_string(Image.open(image_path))

    return text, img_str
if __name__ == '__main__':
    app.run(debug=True)
