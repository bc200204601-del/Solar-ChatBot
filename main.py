from flask import Flask, request, jsonify
import json, os

app = Flask(__name__)

# Paths to JSON data files
FAQS_PATH = os.path.join("server", "data", "faqs.json")
INSTALLERS_PATH = os.path.join("server", "data", "installers_pk_rwp.json")

# Load FAQs
if os.path.exists(FAQS_PATH):
    with open(FAQS_PATH, "r", encoding="utf-8") as f:
        FAQS = json.load(f)
else:
    FAQS = {}

# Load Installers
if os.path.exists(INSTALLERS_PATH):
    with open(INSTALLERS_PATH, "r", encoding="utf-8") as f:
        INSTALLERS = json.load(f)
else:
    INSTALLERS = []


@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint for Dialogflow"""
    req = request.get_json(silent=True, force=True)
    intent = req.get("queryResult", {}).get("intent", {}).get("displayName", "")
    parameters = req.get("queryResult", {}).get("parameters", {})
    response_text = "⚠️ Sorry, I didn’t understand that."

    # --- Intent: Get System Size ---
    if intent == "Get_System_Size":
        area = parameters.get("area")
        units = parameters.get("units")
        bill = parameters.get("bill")
        response_text = (
            f"📐 Based on your input:\n"
            f"- Area: {area} sqft\n- Units: {units}\n- Bill: PKR {bill}\n\n"
            "👉 Recommended: ~5kW system."
        )

    # --- Intent: Check Cost ---
    elif intent == "Check_Cost":
        size = int(parameters.get("size", 0))
        costs = {
            3: {"total": 650000, "panels": 400000, "inverter": 150000, "installation": 100000},
            5: {"total": 950000, "panels": 600000, "inverter": 200000, "installation": 150000},
            10: {"total": 1750000, "panels": 1200000, "inverter": 350000, "installation": 200000},
            15: {"total": 2500000, "panels": 1800000, "inverter": 500000, "installation": 200000},
            20: {"total": 3200000, "panels": 2300000, "inverter": 600000, "installation": 300000},
        }
        if size in costs:
            b = costs[size]
            response_text = (
                f"💡 Cost for {size}kW system:\n"
                f"• Panels: PKR {b['panels']:,}\n"
                f"• Inverter: PKR {b['inverter']:,}\n"
                f"• Installation: PKR {b['installation']:,}\n"
                f"👉 Total: PKR {b['total']:,}"
            )
        else:
            response_text = "Please pick 3, 5, 10, 15, or 20 kW."

    # --- Intent: Learn Net Metering ---
    elif intent == "Learn_Net_Metering":
        response_text = (
            "⚡ Net Metering in Pakistan:\n"
            "1. Apply to DISCO (e.g. IESCO)\n"
            "2. Install bi-directional meter\n"
            "3. Get NEPRA approval\n"
            "4. Sell excess units back to grid"
        )

    # --- Intent: Find Installer ---
    elif intent == "Find_Installer":
        if INSTALLERS:
            response_text = "🏢 Top Solar Installers in Rawalpindi:\n"
            for inst in INSTALLERS:
                response_text += f"- {inst['name']} 📞 {inst['phone']} 📍 {inst['address']}\n"
        else:
            response_text = "Installer data not found."

    # --- Intent: FAQs ---
    elif intent == "Solar_FAQ":
        topic = parameters.get("faq_topic", "").lower()
        response_text = FAQS.get(
            topic,
            "FAQ not found. Try asking about 'maintenance', 'cloudy day', or 'lifespan'."
        )

    return jsonify({"fulfillmentText": response_text})


if __name__ == "__main__":
    # Flask app will run on port 5000 (for Render/ngrok)
    app.run(host="0.0.0.0", port=5000, debug=True)
