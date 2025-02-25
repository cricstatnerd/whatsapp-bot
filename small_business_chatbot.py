import json
import requests
import datetime
import random
import os
from flask import Flask, request
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# WhatsApp API Details
WHATSAPP_API_URL = "https://graph.facebook.com/v22.0/571743046022511/messages"
ACCESS_TOKEN = "EACEpzJHv3qwBOyXS3gb3E8zzcKl6c8huGwzHgjbEWj0p6gP3mIHE3LJvgnBGCPjDYTDtIqqd3TeuvQkR5qRLpOCj8VbIOJTFKgcZA7aZApCbZB2VYipL5vbZBC7hZApzA5PC71sWa3GNdWYMiSz032004397g9mu88ezVX1TZALNJmi0YBHjroaTtBo25Ifz6GZCgZDZD"

# Load API key from environment variable
HF_API_KEY = os.getenv("HF_API_KEY")

if not HF_API_KEY:
    raise ValueError("⚠️ ERROR: Hugging Face API Key is missing! Set it as an environment variable.")

# Google Sheets Web App URLs
FAQ_SHEET_URL = "https://script.google.com/macros/s/AKfycbxIuDDwPa9-apnE3W-0j23tTOwKsCsEhSelfKE6eV60h-1HrVGb8zZSsta9qX0aaFYf/exec"
LEAD_LOGGING_URL = "https://script.google.com/macros/s/YOUR_GOOGLE_SHEET_EXEC_URL/exec"

# Load Sentence Transformer model for FAQ Matching
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Function to fetch FAQs from Google Sheets
def fetch_faqs():
    response = requests.get(FAQ_SHEET_URL)
    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, dict) and "faqs" in data:
                return data["faqs"]  # Ensure it's a list of FAQs
            elif isinstance(data, list):
                return data  # Already a list of FAQs
            else:
                print("Unexpected FAQ data format:", data)
                return []
        except json.JSONDecodeError:
            print("Error parsing JSON response")
            return []
    print("Failed to fetch FAQs, status code:", response.status_code)
    return []

# Function to find the best matching FAQ
def find_best_faq(query, faqs):
    questions = [faq['Question'] for faq in faqs]
    embeddings = model.encode(questions, convert_to_tensor=True)
    query_embedding = model.encode(query, convert_to_tensor=True)
    scores = util.pytorch_cos_sim(query_embedding, embeddings)[0]
    
    best_match_idx = scores.argmax().item()
    best_score = scores[best_match_idx].item()
    
    if best_score > 0.7:  # If similarity score is high, return FAQ answer
        return faqs[best_match_idx]['Answer']
    else:
        return None  # If not confident, return None so AI generates a response

# Function to get AI-generated response from Hugging Face
def generate_ai_response(query):
    api_url = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": query}

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            response_data = response.json()
            if isinstance(response_data, list) and "generated_text" in response_data[0]:
                return response_data[0]['generated_text']
            else:
                print("Unexpected AI response format:", response_data)
                return "AI response error. Please try again."
        except json.JSONDecodeError:
            print("Error parsing AI response")
            return "AI response error. Please try again."
    else:
        print(f"AI API Error {response.status_code}: {response.text}")
        return "I'm not sure, but I'll get back to you!"

# Function to log leads to Google Sheets
def log_to_google_sheets(phone_number, query, response_text, lead_score, assigned_employee):
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "phone_number": phone_number,
        "query": query,
        "response": response_text,  # Log AI-generated or FAQ response
        "lead_score": lead_score,
        "assigned_employee": assigned_employee
    }
    requests.post(LEAD_LOGGING_URL, json=data)

# Function to assign lead score
def assign_lead_score(query):
    high_intent_keywords = ["buy", "purchase", "order", "pricing", "cost"]
    medium_intent_keywords = ["details", "info", "features", "availability"]
    
    if any(word in query.lower() for word in high_intent_keywords):
        return 90
    elif any(word in query.lower() for word in medium_intent_keywords):
        return 60
    return 30

# Function to send WhatsApp message
def send_whatsapp_message(phone_number, message):
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
    return response.status_code == 200

# WhatsApp Webhook to receive messages
@app.route("/webhook", methods=["GET", "POST"])
def whatsapp_webhook():
    if request.method == "GET":
        token_sent = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token_sent == "12345":
            return challenge, 200
        return "Verification token mismatch", 403

    data = request.get_json()
    if data and "entry" in data:
        for entry in data["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "messages" in value:
                    for message in value["messages"]:
                        phone_number = message["from"]
                        query = message["text"]["body"]
                        
                        # Fetch FAQs and get best response
                        faqs = fetch_faqs()
                        faq_response = find_best_faq(query, faqs)

                        if faq_response:
                            response_text = faq_response  # Use FAQ answer
                        else:
                            response_text = generate_ai_response(query)  # Generate AI answer

                        # Assign lead score and log to Google Sheets
                        lead_score = assign_lead_score(query)
                        assigned_employee = random.choice(["Sales Rep 1", "Sales Rep 2", "Sales Rep 3"])
                        log_to_google_sheets(phone_number, query, response_text, lead_score, assigned_employee)
                        
                        send_whatsapp_message(phone_number, response_text)
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Bot is Live!", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)