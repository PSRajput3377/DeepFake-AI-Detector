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
backend/
│
├── models/
├── utils/
├── train.py
├── inference.py


---

## 🎥 Pipeline

1. Upload video  
2. Extract frames using OpenCV  
3. Process frames through ResNeXt  
4. Sequence modeling using LSTM  
5. Feature refinement using MobileViT  
6. Final classification  

---

## 📊 Dataset

- FaceForensics++
- DeepFake Detection Challenge (DFDC)

---

## 🚀 Features

- Hybrid deep learning model  
- Efficient & lightweight design  
- Temporal + spatial analysis  
- Scalable for real-time applications  

---

## 🌐 Deployment

- Backend: FastAPI  
- Hosting: Render  

---

## 📌 Future Improvements

- Face detection (MTCNN)
- Grad-CAM visualization
- Model optimization (quantization/pruning)
- Web UI for user interaction

---

## 🤝 Contributing

Feel free to fork and improve this project!

---

## 👨‍💻 Author

Prashant Singh Rajput
