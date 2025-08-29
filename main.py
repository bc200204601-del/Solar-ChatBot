import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Load Data ---
INSTALLERS_FILE = "server/data/installers_pk_rwp.json"
FAQ_FILE = "server/data/faqs.json"

with open(INSTALLERS_FILE, "r", encoding="utf-8") as f:
    installers_data = json.load(f)

with open(FAQ_FILE, "r", encoding="utf-8") as f:
    faqs_data = json.load(f)


# --- Routes ---
@app.route("/", methods=["GET"])
def home():
    return "✅ Solar Chatbot Webhook is running!"


@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(silent=True, force=True)
    intent = req.get("queryResult", {}).get("intent", {}).get("displayName", "")

    if intent == "Get_System_Size":
        return handle_get_system_size(req)

    elif intent == "Check_Cost":
        return handle_check_cost(req)

    elif intent == "Find_Installer":
        return handle_find_installer()

    elif intent == "Learn_Net_Metering":
        return handle_learn_net_metering()

    elif intent == "Solar_FAQ":
        return handle_solar_faq(req)

    return jsonify({"fulfillmentText": "Sorry, I didn't understand that."})


# --- Intent Handlers ---
def handle_get_system_size(req):
    params = req.get("queryResult", {}).get("parameters", {})
    area = params.get("area")
    units = params.get("units")
    bill = params.get("bill")

    if area:
        return jsonify({"fulfillmentText": f"Based on {area} marla area, you may need a 5–7 kW system."})
    elif units:
        return jsonify({"fulfillmentText": f"With {units} monthly units, approx. 3–5 kW system is suitable."})
    elif bill:
        return jsonify({"fulfillmentText": f"With a monthly bill of PKR {bill}, a 5–10 kW system is recommended."})
    else:
        return jsonify({"fulfillmentText": "Can you provide area (marla/sqft), monthly units, or bill amount?"})


def handle_check_cost(req):
    params = req.get("queryResult", {}).get("parameters", {})
    size = int(params.get("size", 0))

    cost_table = {
        3: {"system": "3kW", "price": 650000, "breakdown": {"Panels": 400000, "Inverter": 120000, "Installation": 80000, "Misc": 50000}},
        5: {"system": "5kW", "price": 950000, "breakdown": {"Panels": 600000, "Inverter": 150000, "Installation": 120000, "Misc": 80000}},
        10: {"system": "10kW", "price": 1750000, "breakdown": {"Panels": 1100000, "Inverter": 250000, "Installation": 250000, "Misc": 150000}},
        15: {"system": "15kW", "price": 2500000, "breakdown": {"Panels": 1600000, "Inverter": 350000, "Installation": 350000, "Misc": 200000}},
        20: {"system": "20kW", "price": 3200000, "breakdown": {"Panels": 2000000, "Inverter": 500000, "Installation": 450000, "Misc": 250000}},
    }

    if size in cost_table:
        data = cost_table[size]
        breakdown_text = "\n".join([f"- {k}: PKR {v:,}" for k, v in data["breakdown"].items()])
        reply = f"💰 Estimated cost for {data['system']} = PKR {data['price']:,}\nBreakdown:\n{breakdown_text}"
        return jsonify({"fulfillmentText": reply})
    else:
        return jsonify({"fulfillmentText": "Please choose from 3, 5, 10, 15, or 20 kW systems."})


def handle_find_installer():
    reply = "🔧 Top Solar Installers in Rawalpindi:\n"
    for inst in installers_data["installers"][:3]:
        reply += f"- {inst['name']} 📞 {inst['phone']} 📍 {inst['address']}\n"
    return jsonify({"fulfillmentText": reply})


def handle_learn_net_metering():
    return jsonify({
        "fulfillmentText": (
            "⚡ Net Metering allows you to sell excess electricity back to the grid. "
            "In Pakistan, NEPRA regulates it. You apply through your DISCO, install a bi-directional meter, "
            "and get credit for extra units. Approval takes 1–2 months."
        )
    })


def handle_solar_faq(req):
    params = req.get("queryResult", {}).get("parameters", {})
    topic = params.get("faq_topic", "").lower()

    for faq in faqs_data["faqs"]:
        if topic in faq["topic"].lower():
            return jsonify({"fulfillmentText": faq["answer"]})

    return jsonify({"fulfillmentText": "I don’t have information on that FAQ yet."})


# --- Start App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # ✅ dynamic port for Render
    app.run(host="0.0.0.0", port=port)
