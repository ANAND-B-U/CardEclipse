# 📇 Business Card Parser API

A **production-ready**, **multi-model** API to extract structured contact information from business card images using **NVIDIA**, **Mistral**, and **Gemini** vision models with intelligent fallback.

---

## ✨ Features

- ✅ **Multi-Model Support**: NVIDIA Phi-3.5 Vision, Mistral Large (with vision), Google Gemini 2.5 Flash  
- 🔁 **Smart Fallback**: Auto retries with alternative models if one fails  
- 🌍 **Global Phone Normalization**: Uses Google’s `libphonenumber` for correct international formats  
- 🧹 **Clean Output**: Omits null/empty fields — only returns what’s present  
- 🛡️ **Robust Error Handling**: Detects quota limits, auth failures, and parsing errors  
- 📦 **Batch & Single Processing**: Upload one or many cards at once  
- 📊 **Detailed Logging**: Full traceability for debugging and monitoring  
- 🔐 **Secure**: Safe file handling, no data leakage  

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install flask flask-cors python-dotenv pillow google-generativeai openai mistralai phonenumbers

2. Set Up API Keys
Create a .env file:

GEMINI_API_KEY=your_gemini_key
NVIDIA_API_KEY=nvapi-your_nvidia_key_from_build_nvidia_com
MISTRAL_API_KEY=your_mistral_key_from_console_mistral_ai

3. Run the Server
python app.py

Server starts at http://localhost:5000

📡 API Endpoints
🔍 Health Check
http
GET /health
Returns service status and available models.

🖼️ Single Card Extraction
http 
POST /api/single

Form Data:

image: (file) Business card image (.jpg, .png)
model: (optional) auto (default), nvidia, mistral, or gemini
Success Response:
{
  "success": true,
  "data": {
    "name": "Senthilkumar M",
    "title": "Marketing Executive",
    "company": "Vesat Renewables Pvt. Ltd.",
    "phoneNumbers": ["+91 74188 58884"],
    "email": "sales@vesatsolar.com",
    "website": "www.vesatsolar.com",
    "model": "nvidia"
  },
  "model_used": "nvidia",
  "filename": "card.jpg"
}

📁 Batch Extraction

POST /api/batch

Form Data:

images: (multiple files) Business card images
model: (optional) same as above
Response:
Form Data:

images: (multiple files) Business card images
model: (optional) same as above
Response:

🔧 Model Behavior
Mode
Fallback Order
auto (default)
NVIDIA → Mistral → Gemini
nvidia
NVIDIA → Mistral → Gemini
mistral
Mistral → NVIDIA → Gemini
gemini
Gemini → NVIDIA → Mistral
If your primary model fails (e.g., quota exceeded), the system automatically retries with the next.

📝 Output Schema
All fields are optional — only included if data is present and valid:

Field
Type
Example
name
string
"Senthilkumar M"
title
string
"Marketing Executive"
company
string
"Vesat Renewables Pvt. Ltd."
address
string
"Chennai, Tamil Nadu, India"
phoneNumbers
array of strings
["+91 74188 58884"]
email
string
"sales@vesatsolar.com"
website
string
"www.vesatsolar.com"
tokens
integer
1020
model
string
"nvidia"
❌ No null, empty strings, or empty arrays — keeps JSON clean.

🛠️ Common Errors & Fixes
Error
Cause
Solution
Authorization failed
Invalid/missing API key
Verify keys in .env; NVIDIA key must be from build.nvidia.com
Gemini quota exceeded
Free tier limit (20/day)
Wait until reset (~1:30 PM IST next day) or upgrade plan
Extraction failed with all models
All models failed
Check logs; ensure image is clear and <50 MB
400 No image provided
Missing file upload
In Postman, attach file as File type (not Text)
🧪 Testing in Postman
Method: POST
URL: http://localhost:5000/api/single
Body → form-data:
Key: image → Type: File → Select image
Key: model → Type: Text → Value: mistral (optional)
Click Send
📜 License
MIT License — free to use, modify, and deploy.

💡 Built for reliability — whether you're processing 1 card or 10,000, this API handles errors gracefully and delivers clean, structured data.

Happy parsing! 🚀
```

