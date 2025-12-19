# Zest – Multi‑Provider AI API

A Flask‑based backend service for experimenting with multiple AI providers (Google Generative AI, OpenAI, Mistral) and supporting utilities like image processing, phone number parsing, and secure environment management.

---

## 🚀 Features
- REST API built with **Flask**
- **CORS** enabled for cross‑origin requests
- Integration with:
  - Google Generative AI (`google-generativeai`)
  - OpenAI (`openai`)
  - Mistral AI (`mistralai`)
- Image processing with **Pillow**
- Secure environment variable handling via **python‑dotenv**
- Phone number parsing and validation with **phonenumbers**
- Modular design for easy extension

---

## 📦 Requirements
Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt