import gradio as gr
from PIL import Image
import numpy as np
import cv2
import easyocr
from transformers import pipeline

# 1. Initialize core AI and OCR models
# EasyOCR reader initializes on CPU for quick local text extraction
reader = easyocr.Reader(['en'], gpu=False)

image_classifier = pipeline(
    "image-classification",
    model="google/vit-base-patch16-224",
    device=-1
)

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
        return "⚠️ **Error:** Please upload a product photo.", gr.update(visible=False)

    # ----------------------------------------------------
    # PHASE 1: Image Quality Analysis
    # ----------------------------------------------------
    gray_img = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    height, width = gray_img.shape

    # Check A: Low Resolution (Threshold: Less than 400px on either side)
    if height < 400 or width < 400:
        return f"""### ❌ Image Rejected
**Reason:** Resolution is too low ({width}x{height}px). Please upload an image where both width and height are at least 400 pixels.""", gr.update(visible=False)

    # Check B: Blur Detection using Laplacian Variance (Threshold: < 80 is blurry)
    laplacian_var = cv2.Laplacian(gray_img, cv2.CV_64F).var()
    if laplacian_var < 80.0:
        return f"""### ❌ Image Rejected
**Reason:** The image is too blurry (Sharpness Score: {laplacian_var:.1f}). Please upload a sharper photo.""", gr.update(visible=False)

    # Check C: Text-Heavy/Watermark Image Detection using OCR
    ocr_results = reader.readtext(image)
    total_text_area = 0
    img_area = width * height

    for (bbox, text, prob) in ocr_results:
        xs = [pt[0] for pt in bbox]
        ys = [pt[1] for pt in bbox]
        box_w = max(xs) - min(xs)
        box_h = max(ys) - min(ys)
        total_text_area += (box_w * box_h)

    text_ratio = total_text_area / img_area
    if text_ratio > 0.20:
        return f"""### ❌ Image Rejected
**Reason:** The image contains too much text or graphic overlays ({text_ratio:.1%}). Please upload a clear photo of the product.""", gr.update(visible=False)

    # ----------------------------------------------------
    # PHASE 2: Image-based Category Suggestion
    # ----------------------------------------------------
    pil_img = Image.fromarray(image.astype('uint8'), 'RGB')
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
    top_labels = "\n".join(
        [f"  - `{item['label'].split(',')[0]}` — {item['score']:.1%}" for item in img_res[:5]]
    )

    markdown_report = f"""
### 📊 Image Analysis Summary
* **Suggested Category:** **{suggested_category}**
* **Primary Object Detected:** `{top_img_object}` *(Confidence: {top_img_confidence:.1%})*

### 🔍 Top Detected Labels
{top_labels}

### 🛠️ Quality Metrics
* **Resolution:** {width}x{height}px ✅
* **Sharpness Score:** {laplacian_var:.1f} ✅
* **Text Density:** {text_ratio:.1%} coverage ✅

*Note: Data processed entirely in-memory and discarded after evaluation.*
"""
    return markdown_report


# 3. Build UI Architecture
with gr.Blocks(title="Marketplace AI Secure Validator") as demo:
    gr.Markdown("# 🛒 Marketplace Product Category Suggester")
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
