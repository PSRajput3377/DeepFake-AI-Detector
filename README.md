# 🎭 DeepFake AI Detector (ResNeXt + LSTM + MobileViT)

An advanced deep learning-based system to detect deepfake videos by analyzing both **spatial** and **temporal inconsistencies**.

---

## 📌 Overview

This project uses a hybrid deep learning architecture combining:

- **ResNeXt** → Extracts spatial features from video frames  
- **LSTM** → Captures temporal inconsistencies across frames  
- **MobileViT** → Lightweight transformer for global feature refinement  

---

## 🧠 Architecture

video → frames → ResNeXt → LSTM → MobileViT → classifier → Real/Fake

---

## ⚙️ Tech Stack

- Python
- PyTorch
- OpenCV
- FastAPI (for deployment)
- timm (for MobileViT)

---

## 📂 Project Structure
