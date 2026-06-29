import gradio as gr
from PIL import Image
import numpy as np
import cv2
import pytesseract
from transformers import pipeline, AutoImageProcessor
from optimum.onnxruntime import ORTModelForImageClassification

# 1. Initialize Core Models with ONNX Runtime Backend
#    Using apple/mobilevit-small — a lightweight model optimized for CPU inference.
#    ONNX Runtime eliminates PyTorch overhead and compiles the graph for max efficiency.
model_id = "apple/mobilevit-small"

try:
    onnx_model = ORTModelForImageClassification.from_pretrained(model_id, export=True)
    image_processor = AutoImageProcessor.from_pretrained(model_id, use_fast=True)

    image_classifier = pipeline(
        "image-classification",
        model=onnx_model,
        image_processor=image_processor
    )
    MODEL_LOADED = True
except Exception as e:
    MODEL_LOADED = False
    MODEL_ERROR = str(e)

# 2. Marketplace Categorisation Taxonomy — map visual labels to categories
CATEGORY_KEYWORDS = {
    "Electronics & Gadgets": ["screen", "phone", "laptop", "mouse", "keyboard", "audio", "camera", "electronic", "television", "modem", "monitor", "remote", "computer", "tablet"],
    "Fashion & Apparel": ["jersey", "coat", "suit", "dress", "shoe", "boot", "jeans", "shirt", "apparel", "clothing", "sock", "hat", "sandal", "sneaker", "sunglasses", "tie", "bow"],
    "Home & Kitchen": ["table", "chair", "desk", "plate", "cup", "pot", "furniture", "appliance", "pillow", "bed", "stove", "lamp", "vase", "sofa", "clock", "ruler"],
    "Books & Stationery": ["book", "comic", "binder", "notebook", "paper", "pen", "pencil", "envelope", "magazine"],
    "Automotive": ["car", "wheel", "tire", "motorcycle", "vehicle", "tractor", "minibus", "cab", "moped"],
    "Beauty & Personal Care": ["bottle", "lotion", "lipstick", "cosmetic", "soap", "perfume", "hair", "shampoo", "cream"]
}


def analyze_product_image(image):
    if image is None:
        yield "⚠️ **Error:** Please upload a product photo."
        return

    if not MODEL_LOADED:
        yield f"### ❌ Model Failed to Load\n**Error:** `{MODEL_ERROR}`\n\nThe ONNX model could not be initialized. Please try again later."
        return

    # ----------------------------------------------------
    # PHASE 1: Image Quality Analysis
    # ----------------------------------------------------
    yield "⏳ **Step 1/3:** Checking image quality..."
    gray_img = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    height, width = gray_img.shape

    # Check A: Low Resolution (Threshold: Less than 400px on either side)
    if height < 400 or width < 400:
        yield f"""### ❌ Image Rejected
**Reason:** Resolution is too low ({width}x{height}px). Please upload an image where both width and height are at least 400 pixels."""
        return

    # Check B: Blur Detection using Laplacian Variance (Threshold: < 80 is blurry)
    laplacian_var = cv2.Laplacian(gray_img, cv2.CV_64F).var()
    if laplacian_var < 80.0:
        yield f"""### ❌ Image Rejected
**Reason:** The image is too blurry (Sharpness Score: {laplacian_var:.1f}). Please upload a sharper photo."""
        return

    # Check C: Text-Heavy/Watermark Image Detection using Tesseract OCR
    try:
        ocr_data = pytesseract.image_to_data(gray_img, output_type=pytesseract.Output.DICT)
        total_text_area = 0
        img_area = width * height

        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) > 40 and ocr_data['text'][i].strip():
                total_text_area += ocr_data['width'][i] * ocr_data['height'][i]

        text_ratio = total_text_area / img_area
        if text_ratio > 0.20:
            yield f"""### ❌ Image Rejected
**Reason:** The image contains too much text or graphic overlays ({text_ratio:.1%}). Please upload a clear photo of the product."""
            return
    except Exception:
        # If OCR fails, proceed without text density check
        text_ratio = 0.0

    # ----------------------------------------------------
    # PHASE 2: ONNX-Powered Category Suggestion
    # ----------------------------------------------------
    yield "⏳ **Step 2/3:** Classifying product category via ONNX Runtime..."
    pil_img = Image.fromarray(image.astype('uint8'), 'RGB')

    # Inference handled natively via ONNX Runtime sessions — no PyTorch overhead
    img_res = image_classifier(pil_img)

    top_img_object = img_res[0]['label'].split(',')[0].lower()
    top_img_confidence = img_res[0]['score']
    detected_objects = [item['label'].lower() for item in img_res]

    # Match detected objects to a marketplace category
    suggested_category = "Uncategorized"
    for category, keywords in CATEGORY_KEYWORDS.items():
        for obj_string in detected_objects[:5]:
            if any(kw in obj_string for kw in keywords):
                suggested_category = category
                break
        if suggested_category != "Uncategorized":
            break

    # ----------------------------------------------------
    # PHASE 3: Build Report
    # ----------------------------------------------------
    yield "⏳ **Step 3/3:** Generating report..."
    top_labels = "\n".join(
        [f"  - `{item['label'].split(',')[0]}` — {item['score']:.1%}" for item in img_res[:5]]
    )

    markdown_report = f"""
### 📊 Image Analysis Summary
* **Suggested Category:** **{suggested_category}**
* **Primary Object Detected:** `{top_img_object}` *(Confidence: {top_img_confidence:.1%})*

### 🔍 Top Detected Labels (ONNX Runtime)
{top_labels}

### 🛠️ Quality Metrics
* **Resolution:** {width}x{height}px ✅
* **Sharpness Score:** {laplacian_var:.1f} ✅
* **Text Density:** {text_ratio:.1%} coverage ✅

*Note: Data processed entirely in-memory and discarded after evaluation.*
"""
    yield markdown_report


# 3. Build UI Architecture
with gr.Blocks(title="Marketplace AI Secure Validator") as demo:
    gr.Markdown("# 🛒 Marketplace Product Category Suggester (ONNX-Accelerated)")
    gr.Markdown("Upload a product photo to get an AI-suggested marketplace category and image quality check.")

    with gr.Row():
        with gr.Column():
            input_img = gr.Image(label="Upload Product Photo")
            submit_btn = gr.Button("Analyze Image", variant="primary")

        with gr.Column():
            output_report = gr.Markdown(label="Analysis Report")

    submit_btn.click(
        fn=analyze_product_image,
        inputs=[input_img],
        outputs=[output_report]
    )

if __name__ == "__main__":
    demo.launch()
