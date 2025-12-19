import os
import json
import re
import io
import base64
import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import openai
from mistralai import Mistral
from PIL import Image
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import phonenumbers
from phonenumbers import NumberParseException
from google.api_core.exceptions import ResourceExhausted  
from openai import PermissionDeniedError 
from mistralai.models.sdkerror import SDKError  
from google.api_core.exceptions import ResourceExhausted, InvalidArgument

# -----------------------------------------------------------------------------
# APP & CONFIG
# -----------------------------------------------------------------------------

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# Configure logging: INFO to stdout, include timestamps and level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = app.logger  # reuse Flask logger (already bound to Werkzeug)

# -----------------------------------------------------------------------------
# API KEYS & CLIENTS
# -----------------------------------------------------------------------------

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY")
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")

if not GEMINI_KEY:
    logger.error("Missing GEMINI_API_KEY in .env")
    raise ValueError("Missing GEMINI_API_KEY in .env")
if not NVIDIA_KEY:
    logger.error("Missing NVIDIA_API_KEY in .env")
    raise ValueError("Missing NVIDIA_API_KEY in .env")
if not MISTRAL_KEY:
    logger.error("Missing MISTRAL_API_KEY in .env")
    raise ValueError("Missing MISTRAL_API_KEY in .env")

# Gemini
genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")

# NVIDIA (OpenAI compatible)
nvidia_client = openai.OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_KEY,
)

# Mistral
mistral_client = Mistral(api_key=MISTRAL_KEY)

logger.info("Model clients initialized successfully")

# -----------------------------------------------------------------------------
# SHARED PROMPT
# -----------------------------------------------------------------------------

PROMPT = (
    "You are an expert OCR and business card parser. Extract ONLY the following fields as JSON:\n"
    "- 'name': Full name\n"
    "- 'title': Job title\n"
    "- 'company': Legal company name\n"
    "- 'address': Full postal address (if present)\n"
    "- 'phoneNumbers': List of full international phone numbers (if any)\n"
    "- 'email': Email address (if present)\n"
    "- 'website': Official website (if present)\n\n"
    "Rules:\n"
    "- ONLY include a field if its value is present and valid.\n"
    "- NEVER output null, empty string, or empty array.\n"
    "- Return ONLY valid JSON. No markdown, no explanations."
)

# -----------------------------------------------------------------------------
# HELPERS: NORMALIZATION & PARSING
# -----------------------------------------------------------------------------

def normalize_phone(phone: str) -> str:
    """Normalize phone number using libphonenumber; log failures."""
    if not phone or not isinstance(phone, str):
        return ""
    cleaned = re.sub(
        r"^(?:mob|mobile|ph|phone|tel)[:\s]*", "", phone, flags=re.IGNORECASE
    )
    for region in [None, "IN", "US", "GB", "CA", "AU"]:
        try:
            parsed = phonenumbers.parse(cleaned, region)
            if phonenumbers.is_valid_number(parsed):
                fmt = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                return fmt
        except NumberParseException:
            continue
        except Exception as e:
            logger.warning(f"Unexpected error normalizing phone '{phone}': {e}")
            break
    logger.debug(f"normalize_phone: returning original '{phone.strip()}'")
    return phone.strip()

def clean_address(address: str) -> str:
    """Remove phone like fragments and normalize whitespace/punctuation."""
    if not address or not isinstance(address, str):
        return ""
    cleaned = re.sub(
        r"(?i)\b(mb|mob|mobile|ph|phone|tel)[:\s]*[\d\s\-\+\(\)]{8,}",
        "",
        address,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.rstrip(".,; ")
    return cleaned

def clean_output(data: dict) -> dict:
    """Remove null, empty string, empty list values."""
    cleaned = {}
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        if isinstance(v, list) and len(v) == 0:
            continue
        cleaned[k] = v
    return cleaned

def normalize_output(raw_data: dict, model_name: str, tokens=None) -> dict:
    """Build unified result dict + run normalization and cleaning, with logging."""
    logger.debug(f"normalize_output: raw_data from {model_name} = {raw_data}")

    # Phones
    phones_input = raw_data.get("phoneNumbers")
    phone_list = []
    if isinstance(phones_input, str):
        phone_list = [phones_input]
    elif isinstance(phones_input, list):
        phone_list = [str(p) for p in phones_input if p]

    normalized_phones = [normalize_phone(p) for p in phone_list]
    normalized_phones = [p for p in normalized_phones if p]

    # Address
    addr = raw_data.get("address")
    clean_addr = ""
    if isinstance(addr, str):
        clean_addr = clean_address(addr)
    elif isinstance(addr, list):
        if addr and isinstance(addr[0], dict):
            dist = (addr[0].get("authorizedDistributor") or "").strip()
            corp = (addr[0].get("corporateOffice") or "").strip()
            clean_addr = clean_address(dist if dist else corp)
        else:
            combined = " | ".join(str(a).strip() for a in addr if a)
            clean_addr = clean_address(combined)
    else:
        clean_addr = clean_address(str(addr)) if addr else ""

    result = {
        "name": raw_data.get("name"),
        "title": raw_data.get("title"),
        "company": raw_data.get("company"),
        "email": raw_data.get("email"),
        "website": raw_data.get("website"),
        "address": clean_addr,
        "phoneNumbers": normalized_phones,
        "tokens": tokens,
        "model": model_name,
    }

    cleaned = clean_output(result)
    logger.debug(f"normalize_output: cleaned result for {model_name} = {cleaned}")
    return cleaned

def extract_json_from_text(text: str):
    """Try multiple strategies to recover JSON; log where it fails."""
    text = text.strip()
    logger.debug(f"extract_json_from_text: raw text snippet = {text[:200]}")

    # direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # `````` fenced block
    match = re.search(r"``````", text, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            logger.debug("extract_json_from_text: fenced block parse failed")

    # first {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            logger.debug("extract_json_from_text: curly brace block parse failed")

    logger.warning("extract_json_from_text: could not find valid JSON")
    return None

def image_to_bytes(image_path: str) -> bytes:
    """Open local image and return JPEG bytes; log basic info."""
    logger.info(f"image_to_bytes: loading image from {image_path}")
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        byte_io = io.BytesIO()
        img.save(byte_io, format="JPEG", quality=95)
        return byte_io.getvalue()

def image_to_base64(image_path: str) -> str:
    """Read file and return base64 string; log path."""
    logger.info(f"image_to_base64: reading {image_path}")
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def save_temp_image(file) -> str:
    """Save uploaded file to temp/ and return path; log filename and path."""
    os.makedirs("temp", exist_ok=True)
    filename = secure_filename(file.filename)
    timestamp = int(time.time() * 1000)
    temp_path = os.path.join("temp", f"card_{timestamp}_{filename}")
    logger.info(f"save_temp_image: saving upload as {temp_path}")
    file.save(temp_path)
    return temp_path

# -----------------------------------------------------------------------------
# PER MODEL EXTRACTION
# -----------------------------------------------------------------------------

def extract_with_nvidia(image_path: str):
    logger.info(f"extract_with_nvidia: starting for {image_path}")
    try:
        img_b64 = image_to_base64(image_path)
        response = nvidia_client.chat.completions.create(
            model="microsoft/phi-3.5-vision-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }],
            max_tokens=1000,
            temperature=0.1,
        )
        raw_text = response.choices[0].message.content
        raw_json = extract_json_from_text(raw_text)
        if not raw_json:
            logger.warning("extract_with_nvidia: JSON parse failed")
            return None
        tokens = getattr(response, "usage", None)
        token_count = tokens.total_tokens if tokens else None
        result = normalize_output(raw_json, "nvidia", token_count)
        logger.info("extract_with_nvidia: success")
        return result

    except PermissionDeniedError as e:
        logger.error(f"extract_with_nvidia: auth/403 error: {e}", exc_info=True)
        return {"_error": "nvidia_auth_failed"}

    except Exception as e:
        logger.error(f"extract_with_nvidia: exception: {e}", exc_info=True)
        return None

def extract_with_mistral(image_path: str):
    logger.info(f"extract_with_mistral: starting for {image_path}")
    try:
        img_b64 = image_to_base64(image_path)
        response = mistral_client.chat.complete(
            model="mistral-large-2512",
            messages=[
                {"role": "system", "content": PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract the business card details as JSON.",
                        },
                    ],
                },
            ],
            temperature=0.1,
            max_tokens=1000,
        )
        raw_text = response.choices[0].message.content
        raw_json = extract_json_from_text(raw_text)
        if not raw_json:
            logger.warning(
                f"extract_with_mistral: JSON parse failed. Snippet: {raw_text[:150]}..."
            )
            return None
        result = normalize_output(raw_json, "mistral")
        logger.info("extract_with_mistral: success")
        return result

    except SDKError as e:
        # 401 / 403 from Mistral
        if "Status 401" in str(e) or "Status 403" in str(e):
            logger.error(f"extract_with_mistral: auth error: {e}", exc_info=True)
            return {"_error": "mistral_auth_failed"}
        logger.error(f"extract_with_mistral: SDKError: {e}", exc_info=True)
        return None

    except Exception as e:
        logger.error(f"extract_with_mistral: exception: {e}", exc_info=True)
        return None

def extract_with_gemini(image_path: str):
    logger.info(f"extract_with_gemini: starting for {image_path}")
    try:
        image_bytes = image_to_bytes(image_path)
        response = gemini_model.generate_content(
            [PROMPT, {"inline_data": {"mime_type": "image/jpeg", "data": image_bytes}}],
            safety_settings={
                k: "BLOCK_NONE"
                for k in [
                    "HARM_CATEGORY_HARASSMENT",
                    "HARM_CATEGORY_HATE_SPEECH",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "HARM_CATEGORY_DANGEROUS_CONTENT",
                ]
            },
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        )
        raw = json.loads(response.text)
        tokens = getattr(response, "usage_metadata", None)
        token_count = tokens.total_token_count if tokens else None
        result = normalize_output(raw, "gemini", token_count)
        logger.info("extract_with_gemini: success")
        return result

    except ResourceExhausted as e:
        logger.error(f"extract_with_gemini: quota/429 error: {e}", exc_info=True)
        return {"_error": "gemini_quota_exceeded"}

    except InvalidArgument as e:
        # Includes invalid API key
        logger.error(f"extract_with_gemini: invalid key/400: {e}", exc_info=True)
        return {"_error": "gemini_auth_failed"}

    except Exception as e:
        logger.error(f"extract_with_gemini: exception: {e}", exc_info=True)
        return None

# -----------------------------------------------------------------------------
# DISPATCH LOGIC
# -----------------------------------------------------------------------------

def extract_card(image_path: str, model_choice: str = "auto"):
    logger.info(f"extract_card: model_choice={model_choice}, image={image_path}")

    if model_choice == "gemini":
        order = ["gemini", "nvidia", "mistral"]
    elif model_choice == "nvidia":
        order = ["nvidia", "mistral", "gemini"]
    elif model_choice == "mistral":
        order = ["mistral", "nvidia", "gemini"]
    else:
        order = ["nvidia", "mistral", "gemini"]

    last_model = "failed"
    auth_errors = set()   # track which providers failed auth/quota

    for model in order:
        last_model = model
        logger.info(f"extract_card: trying {model} for {image_path}")

        try:
            if model == "gemini":
                result = extract_with_gemini(image_path)
            elif model == "nvidia":
                result = extract_with_nvidia(image_path)
            elif model == "mistral":
                result = extract_with_mistral(image_path)
            else:
                logger.warning(f"extract_card: unknown model '{model}'")
                continue
        except Exception as e:
            logger.error(
                f"extract_card: {model} raised unexpected exception: {e}",
                exc_info=True,
            )
            result = None

        # Handle our special error flags
        if isinstance(result, dict) and "_error" in result:
            auth_errors.add(result["_error"])
            logger.warning(f"extract_card: {model} returned error flag {result['_error']}")
            continue

        if result:
            logger.info(f"extract_card: {model} succeeded for {image_path}")
            return result, model

        logger.warning(f"extract_card: {model} returned no result for {image_path}")

    logger.error(f"extract_card: all models failed for {image_path}")

    # If every model we tried hit auth/quota problems, surface that
    if auth_errors:
        return None, ",".join(sorted(auth_errors))

    return None, last_model

# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Simple health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "models": ["nvidia", "mistral", "gemini"],
            "endpoints": ["/api/single", "/api/batch"],
        }
    )

@app.route("/api/single", methods=["POST"])
def extract_single():
    try:
        logger.info("/api/single: request received")
        model_choice = request.form.get("model", "auto")
        file = request.files.get("image")

        if not file or not file.filename:
            logger.warning("/api/single: no image provided")
            return jsonify({"success": False, "error": "No image provided"}), 400

        temp_path = save_temp_image(file)

        try:
            result, used_model = extract_card(temp_path, model_choice)
        finally:
            if os.path.exists(temp_path):
                logger.info(f"/api/single: deleting temp file {temp_path}")
                os.remove(temp_path)

        if result is None:
            # Default error
            error_msg = "Extraction failed with all models"

            # Specific flags from extract_card (e.g. gemini_quota_exceeded, *_auth_failed)
            if "gemini_quota_exceeded" in used_model:
                error_msg = "Gemini quota exceeded and other models also failed"
            elif "auth_failed" in used_model:
                error_msg = "Authorization failed for one or more providers; check API keys"

            logger.error(f"/api/single: {error_msg} for file {file.filename}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": error_msg,
                        "model_used": used_model,
                    }
                ),
                500,
            )

        logger.info(
            f"/api/single: success with model={used_model} for file {file.filename}"
        )
        return jsonify(
            {
                "success": True,
                "data": result,
                "model_used": used_model,
                "filename": file.filename,
            }
        )

    except Exception as e:
        logger.error(f"/api/single: unexpected error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Internal server error"}), 500
    

@app.route("/api/batch", methods=["POST"])
def extract_batch():
    """
    POST form-data:
      - images: multiple files
      - model: 'auto' | 'nvidia' | 'mistral' | 'gemini' (optional, default=auto)
    """
    try:
        logger.info("/api/batch: request received")
        model_choice = request.form.get("model", "auto")
        files = request.files.getlist("images")

        if not files or all(not f.filename for f in files):
            logger.warning("/api/batch: no images provided")
            return jsonify({"success": False, "error": "No images provided"}), 400

        results = []
        temp_paths = []

        for file in files:
            if not file.filename:
                continue

            temp_path = save_temp_image(file)
            temp_paths.append(temp_path)

            result, used_model = extract_card(temp_path, model_choice)

            # Build per file error message similar to /api/single
            if result is None:
                error_msg = "Extraction failed with all models"
                if "gemini_quota_exceeded" in used_model:
                    error_msg = "Gemini quota exceeded and other models also failed"
                elif "auth_failed" in used_model:
                    error_msg = "Authorization failed for one or more providers; check API keys"

                logger.error(
                    f"/api/batch: {error_msg} for {file.filename} (model_used={used_model})"
                )
            else:
                error_msg = None
                logger.info(
                    f"/api/batch: success for {file.filename} using {used_model}"
                )

            results.append(
                {
                    "filename": file.filename,
                    "success": result is not None,
                    "data": result,
                    "model_used": used_model,
                    "error": error_msg,
                }
            )

        # Cleanup temp files
        for path in temp_paths:
            try:
                os.remove(path)
                logger.debug(f"/api/batch: deleted temp file {path}")
            except OSError as e:
                logger.warning(f"/api/batch: failed to delete temp file {path}: {e}")

        return jsonify({"success": True, "total": len(results), "results": results})

    except Exception as e:
        logger.error(f"/api/batch: unexpected error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Internal server error"}), 500

        # Cleanup temp files
        for path in temp_paths:
            try:
                os.remove(path)
                logger.debug(f"/api/batch: deleted temp file {path}")
            except OSError as e:
                logger.warning(f"/api/batch: failed to delete temp file {path}: {e}")

        return jsonify({"success": True, "total": len(results), "results": results})

    except Exception as e:
        logger.error(f"/api/batch: unexpected error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Internal server error"}), 500

# -----------------------------------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    logger.info("Starting Flask app on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
