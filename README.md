# 📇 Business Card Parser API

A **production‑ready**, **multi‑model** API to extract structured contact information from business card images using **NVIDIA**, **Mistral**, and **Gemini** vision models with intelligent fallback.

---

## ✨ Features

- ✅ **Multi‑Model Support**: NVIDIA Phi‑3.5 Vision, Mistral Large (vision), Google Gemini 2.5 Flash  
- 🔁 **Smart Fallback**: Auto‑retries with alternative models if one fails  
- 🌍 **Global Phone Normalization**: Uses `phonenumbers` (Google libphonenumber) for international formats  
- 🧹 **Clean Output**: Omits null/empty fields — only returns what's present  
- 🛡️ **Robust Error Handling**: Detects quota limits, auth failures, and JSON parsing errors  
- 📦 **Batch & Single Processing**: Upload one or many cards at once  
- 📊 **Detailed Logging**: Per‑model attempts, failures, and fallbacks  
- 🔐 **Secure**: Safe temp file handling, max upload size, no data leakage

---

## 🚀 Quick Start

### 1️⃣ Install Dependencies

```bash
pip install flask flask-cors python-dotenv pillow google-generativeai openai mistralai phonenumbers
```

### 2️⃣ Set Up API Keys

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_key
NVIDIA_API_KEY=nvapi-your_nvidia_key_from_build_nvidia_com
MISTRAL_API_KEY=your_mistral_key_from_console_mistral_ai
```

### 3️⃣ Run the Server

Assuming your main file is `app.py` (or update to your actual filename):

```bash
python app.py
```

Server starts at:

```text
http://localhost:5000
```

---

## 📡 API Endpoints

### 🔍 Health Check

```http
GET /health
```

Returns service status and available models.

**Example response:**

```json
{
  "status": "healthy",
  "models": ["nvidia", "mistral", "gemini"],
  "endpoints": ["/api/single", "/api/batch"]
}
```

---

### 🖼️ Single Card Extraction

```http
POST /api/single
```

**Form‑Data:**

- `image` (file, required): Business card image (`.jpg`, `.jpeg`, `.png`)
- `model` (text, optional): one of `auto` (default), `nvidia`, `mistral`, `gemini`

**Success response example:**

```json
{
  "success": true,
  "data": {
        "name": "Legend A",
        "title": "CEO",
        "company": "Alpha Pvt. Ltd.",
        "phoneNumbers": ["+91 xxxxxxxxx4"],
        "email": "xxxxxxxxxx@alpha.com",
        "website": "www.alpha******.com",
        "model": "nvidia""
  },
  "model_used": "nvidia",
  "filename": "card.jpg"
}
```

---

### 📁 Batch Extraction

```http
POST /api/batch
```

**Form‑Data:**

- `images` (multiple files, required): Business card images
- `model` (text, optional): same options as `/api/single`

**Response example:**

```json
{
  "success": true,
  "total": 2,
  "results": [
    {
      "filename": "card1.jpg",
      "success": true,
      "data": {
        "name": "Legend A",
        "title": "CEO",
        "company": "Alpha Pvt. Ltd.",
        "phoneNumbers": ["+91 xxxxxxxxx4"],
        "email": "xxxxxxxxxx@alpha.com",
        "website": "www.alpha******.com",
        "model": "nvidia"
      },
      "model_used": "nvidia",
      "error": null
    },
    {
      "filename": "card2.jpg",
      "success": false,
      "data": null,
      "model_used": "gemini_quota_exceeded",
      "error": "Gemini quota exceeded and other models also failed"
    }
  ]
}
```

---

## 🔧 Model Behavior & Fallback

**Model selection behavior:**

| `model` value | Fallback order                     |
| ------------- | ---------------------------------- |
| `auto`        | NVIDIA → Mistral → Gemini          |
| `nvidia`      | NVIDIA → Mistral → Gemini          |
| `mistral`     | Mistral → NVIDIA → Gemini          |
| `gemini`      | Gemini → NVIDIA → Mistral          |

If the primary model fails (e.g., quota exceeded, auth error, bad JSON), the API automatically tries the next one in the order until one succeeds or all fail.

---

## 📝 Output Schema

All fields are **optional** — included only if data is present and valid.

| Field        | Type              | Example                          |
| ------------ | ----------------- | -------------------------------- |
| `name`       | string            | "Legend A"               |
| `title`      | string            | "CEO"          |
| `company`    | string            | "Alpha Pvt. Ltd."   |
| `address`    | string            | "Chennai, Tamil Nadu, India"   |
| `phoneNumbers` | array of string | ["+91*****4"]            |
| `email`      | string            | "alpha***********.com"         |
| `website`    | string            | "www.alpha******.com"           |
| `tokens`     | integer           | 1020                           |
| `model`      | string            | "nvidia"                       |

- ❌ No `null` values  
- ❌ No empty strings  
- ❌ No empty arrays  

The API cleans the output to keep the JSON compact and meaningful.

---

## 🛠️ Common Errors & Fixes

| Error message                                           | Cause                          | Fix                                                                 |
| ------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------- |
| Authorization failed                                  | Invalid/missing API key       | Verify keys in `.env`; ensure each provider key has correct access. |
| Gemini quota exceeded and other models also failed    | Gemini free tier exhausted    | Wait for daily reset or upgrade plan; ensure fallbacks are enabled. |
| Extraction failed with all models                     | All models errored            | Check logs; verify keys, quotas, and image quality/size (<50 MB).   |
| No image provided                                     | Missing file upload           | In Postman, set `image` as File type, not Text.                 |

---

## 🧪 Testing with Postman

1. Method: `POST`  
2. URL: `http://localhost:5000/api/single`  
3. Body → `form-data`:
   - Key: `image` → Type: **File** → Select a card image
   - Key: `model` → Type: **Text** → Value: `mistral` (or `auto`, `nvidia`, `gemini`)
4. Click **Send** and inspect the JSON response.

---

## 📜 License

MIT License — free to use, modify, and deploy.

---

💡 Built for reliability — whether you're processing 1 card or 10,000, this API handles errors gracefully and delivers clean, structured contact data.

Happy parsing! 🚀
