---
title: SnapSort
emoji: 📸
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.7.1
app_file: app.py
pinned: false
license: mit
short_description: AI product image classifier and category suggester
tags:
  - image-classification
  - marketplace
  - gradio
---

# 📸 SnapSort

> Snap it. Sort it. Sell it.

AI-powered marketplace product classifier. Upload a photo — get a suggested category and image quality report. No data stored.

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:7860` in your browser.

## What It Does

- **Category Suggestion** — classifies product images into Electronics, Fashion, Home & Kitchen, Books, Automotive, or Beauty & Personal Care
- **Quality Checks** — validates resolution (≥400px), sharpness, and text/watermark density
- **Privacy First** — all processing is in-memory, nothing saved

## License

MIT
