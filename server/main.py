import os, math, json
from flask import Flask, request, jsonify
app = Flask(__name__)

# --- Tunables ---
SUN_HOURS_RWP = 5.5
PERFORMANCE_RATIO = 0.8
PKR_PER_KWH_TARIFF = 55.0
PKR_PER_KW_INSTALLED = 200000.0
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Session memory
sessions = {}

def estimate_system_size_kw(session_id, monthly_bill_pkr=None, monthly_units_kwh=None, rooftop_area_m2=None):
    if session_id not in sessions:
        sessions[session_id] = {}
    s = sessions[session_id]
    
    # Store any new parameters in session (only if provided)
    if monthly_bill_pkr is not None:
        s['bill'] = monthly_bill_pkr
    if monthly_units_kwh is not None:
        s['units'] = monthly_units_kwh
    if rooftop_area_m2 is not None:
        s['area'] = rooftop_area_m2
    
    # Always use session data if available
    monthly_bill_pkr = s.get('bill')
    monthly_units_kwh = s.get('units')
    rooftop_area_m2 = s.get('area')
    
    # Convert Dialogflow parameters to expected format
    if monthly_units_kwh and isinstance(monthly_units_kwh, dict):
        # Handle Dialogflow unit-energy format
        amount = monthly_units_kwh.get('amount', 0)
        unit = monthly_units_kwh.get('unit', '')
        if unit in ['units', 'kWh']:
            monthly_units_kwh = amount
            s['units'] = amount  # Store the numeric value
        else:
            monthly_units_kwh = None
    
    if rooftop_area_m2 and isinstance(rooftop_area_m2, dict):
        # Handle Dialogflow unit-area format - keep in original units for display
        amount = rooftop_area_m2.get('amount', 0)
        unit = rooftop_area_m2.get('unit', '')
        if unit == 'sq ft':
            rooftop_area_m2 = amount  # Keep in sq ft for calculation
            s['area_display'] = f"{amount} sq ft"
            s['area'] = amount  # Store the numeric value
        elif unit == 'marla':
            rooftop_area_m2 = amount * 20.903  # Convert to m² for calculation
            s['area_display'] = f"{amount} marla"
            s['area'] = rooftop_area_m2  # Store the converted value
        else:
            rooftop_area_m2 = amount
            s['area_display'] = f"{amount} {unit}"
            s['area'] = amount
    
    # Convert monthly_bill_pkr to float if it's a string
    if isinstance(monthly_bill_pkr, str):
        try:
            monthly_bill_pkr = float(monthly_bill_pkr.replace('Rs', '').replace(',', '').strip())
            s['bill'] = monthly_bill_pkr
        except (ValueError, TypeError):
            monthly_bill_pkr = None
    
    if monthly_units_kwh:
        daily_kwh = monthly_units_kwh / 30.0
    elif monthly_bill_pkr:
        monthly_units_kwh = monthly_bill_pkr / PKR_PER_KWH_TARIFF
        daily_kwh = monthly_units_kwh / 30.0
    elif rooftop_area_m2:
        # For roof area only, use 100 sq ft per kW rule
        if isinstance(rooftop_area_m2, (int, float)):
            # If it's already a number (converted from marla), use it
            return max(0.5, round(rooftop_area_m2 / 10.0, 1))
        else:
            # If it's still in sq ft, convert to m² first
            return max(0.5, round(rooftop_area_m2 * 0.092903 / 10.0, 1))
    else:
        return 0
    
    kw = daily_kwh / (SUN_HOURS_RWP * PERFORMANCE_RATIO)
    size_kw = max(0.5, round(kw, 1))
    
    # Store size in session for later use
    s['size_kw'] = size_kw
    return size_kw

def estimate_cost_pkr(size_kw):
    if size_kw <= 0:
        return 0
    base = size_kw * PKR_PER_KW_INSTALLED
    if size_kw >= 5:
        base *= 0.97
    return math.ceil(base / 1000.0) * 1000

# Installer database
INSTALLERS = {
    'rawalpindi': [
        {'name': 'Premier Solar Solutions', 'contact': '051-111-123-456', 'rating': '4.8/5', 'address': '6th Road, Rawalpindi'},
        {'name': 'RWP Solar Tech', 'contact': '051-555-789-012', 'rating': '4.6/5', 'address': 'Commercial Market, Saddar'},
        {'name': 'Green Energy Pak', 'contact': '0333-123-4567', 'rating': '4.7/5', 'address': 'Bahria Town Phase 7'}
    ],
    'islamabad': [
        {'name': 'Capital Solar Systems', 'contact': '051-222-345-678', 'rating': '4.9/5', 'address': 'F-10 Markaz'},
        {'name': 'Islamabad Solar', 'contact': '0331-987-6543', 'rating': '4.5/5', 'address': 'Blue Area'},
        {'name': 'Solar Solutions Islamabad', 'contact': '0333-555-1234', 'rating': '4.7/5', 'address': 'G-11 Markaz'}
    ],
    'bahria town': [
        {'name': 'Bahria Solar Experts', 'contact': '0345-555-1234', 'rating': '4.7/5', 'address': 'Bahria Town Phase 8'},
        {'name': 'Green Energy Bahria', 'contact': '0332-444-5678', 'rating': '4.6/5', 'address': 'Bahria Town Phase 4'}
    ],
    'taxila': [
        {'name': 'Taxila Solar Solutions', 'contact': '0333-666-7890', 'rating': '4.5/5', 'address': 'Taxila City'}
    ]
}

def find_installers(location=None):
    if not location:
        location = 'rawalpindi'  # Default location
    
    location = location.lower()
    installers = INSTALLERS.get(location, INSTALLERS['rawalpindi'])
    
    response = f"🔧 Top Solar Installers in {location.title()}:\n\n"
    for i, installer in enumerate(installers, 1):
        response += f"{i}. {installer['name']}\n"
        response += f"   📞 {installer['contact']}\n"
        response += f"   ⭐ Rating: {installer['rating']}\n"
        response += f"   🏠 {installer['address']}\n\n"
    
    response += "💡 Recommendations:\n"
    response += "• Get quotes from at least 3 companies\n"
    response += "• Verify warranty terms (minimum 10 years on panels)\n"
    response += "• Check if they handle net metering paperwork\n"
    response += "• Ask about after-sales service response time\n\n"
    response += "📞 Need help choosing? Call 051-111-000-111"
    
    return response

DEFAULT_FAQS = [
    {"q":"Net Metering","a":"Export excess solar to the grid and get bill credits."},
    {"q":"Maintenance","a":"Panels require periodic cleaning and checks."},
    {"q":"Panel Lifespan","a":"~25 years; inverters ~10–12 years."},
    {"q":"Payback Period","a":"Typically 3–6 years depending on usage and cost."}
]

def load_json(path, fallback):
    try:
        with open(path,'r',encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return fallback

@app.post('/webhook')
def webhook():
    req = request.get_json(force=True) or {}
    intent = req.get('queryResult', {}).get('intent', {}).get('displayName','')
    params = req.get('queryResult', {}).get('parameters',{})
    session_id = req.get('session','default')
    
    # Optional auth
    expected_token = os.environ.get('WEBHOOK_TOKEN')
    auth_header = request.headers.get('Authorization')
    if expected_token and auth_header != f"Bearer {expected_token}":
        return jsonify({"fulfillmentText":"Unauthorized."}), 401

    # --- Intents ---
    if intent == 'Get_System_Size':
        # Get session data
        if session_id not in sessions:
            sessions[session_id] = {}
        session_data = sessions[session_id]
        
        # Extract parameters from Dialogflow
        energy_usage = params.get('energy_usage')
        roof_area = params.get('roof_area')
        monthly_bill = params.get('monthly_bill')
        
        # Convert energy_usage to monthly_units_kwh
        monthly_units_kwh = None
        if energy_usage and isinstance(energy_usage, dict):
            amount = energy_usage.get('amount', 0)
            unit = energy_usage.get('unit', '')
            if unit in ['units', 'kWh']:
                monthly_units_kwh = amount
        
        # Keep roof_area as is (Dialogflow will provide it as dict)
        rooftop_area_m2 = roof_area
        
        # Convert monthly_bill to float
        monthly_bill_pkr = None
        if monthly_bill:
            try:
                monthly_bill_pkr = float(monthly_bill)
            except (ValueError, TypeError):
                monthly_bill_pkr = None
        
        # Calculate system size with all available data
        size_kw = estimate_system_size_kw(
            session_id,
            monthly_bill_pkr,
            monthly_units_kwh,
            rooftop_area_m2
        )
        
        if size_kw > 0:
            text = f"Estimated system size: ~{size_kw} kW for Rawalpindi ☀️"
            
            # Add what we used for calculation
            used_params = []
            if session_data.get('units'):
                used_params.append(f"{session_data.get('units')} units/month")
            if session_data.get('bill'):
                used_params.append(f"bill of PKR {session_data.get('bill')}")
            if session_data.get('area_display'):
                used_params.append(f"roof area of {session_data.get('area_display')}")
            
            if used_params:
                text += f"\n(Based on {', '.join(used_params)})"
        else:
            # Check what information we still need
            missing = []
            if not session_data.get('bill') and not session_data.get('units'):
                missing.append("monthly electricity consumption (in units) or monthly bill amount (in PKR)")
            if not session_data.get('area'):
                missing.append("roof area in sq ft or marla")
            
            if missing:
                text = f"I need more information to calculate system size. Please provide {', '.join(missing)}."
            else:
                text = "I need more information to calculate system size. Please provide your monthly electricity consumption (in units) or monthly bill amount (in PKR), or roof area in sq ft or marla."
        return jsonify({"fulfillmentText": text})
    
    elif intent == 'Check_Cost':
        # Try to get size from parameters first
        size_kw = params.get('size_kw')
        
        # If not in parameters, try to get from session
        if not size_kw and session_id in sessions and 'size_kw' in sessions[session_id]:
            size_kw = sessions[session_id]['size_kw']
        
        # If still not available, try to estimate from session data
        if not size_kw:
            size_kw = estimate_system_size_kw(session_id)
        
        if size_kw <= 0:
            return jsonify({"fulfillmentText":"Please provide monthly bill/units or rooftop area to estimate cost."})
        
        cost = estimate_cost_pkr(size_kw)
        text = f"Estimated turnkey cost for {size_kw} kW: ~PKR {cost:,.0f}"
        return jsonify({"fulfillmentText": text})
    
    elif intent == 'Find_Installer':
        location = params.get('location')
        if not location:
            return jsonify({"fulfillmentText": "I can help you find solar installers in your area! Please specify your location (e.g., Rawalpindi, Islamabad, Bahria Town)."})
        
        text = find_installers(location)
        return jsonify({"fulfillmentText": text})
    
    elif intent == 'Learn_Net_Metering':
        text = (
            "⚡ Net Metering in Pakistan:\n"
            "Sell excess solar to the grid and get credits.\n"
            "Process: Panels produce electricity → excess sent to grid → credits offset your bill.\n"
            "Rawalpindi application:\n"
            "1) Contact IESCO 051-111-000-000\n"
            "2) Submit CNIC, ownership proof, electricity bill, system details\n"
            "3) Install bi-directional meter PKR 25k–40k\n"
            "4) NEPRA approval, start earning credits\n"
            "Financial benefits: 19–22 PKR/unit, reduce bills 70–100%, ROI 20–25% annually."
        )
        return jsonify({"fulfillmentText": text})
    
    elif intent == 'Solar_FAQ':
        faq_topic = params.get('faq_topic')
        if not faq_topic:
            return jsonify({"fulfillmentText": "I can help with maintenance, warranty, battery, panels, inverter, installation, cost, or savings. What topic would you like to know about?"})
        
        # Try to load specific topic
        faqs = load_json(os.path.join(DATA_DIR,'faqs.json'), DEFAULT_FAQS)
        matching_faq = next((f for f in faqs if f['q'].lower() == faq_topic.lower()), None)
        
        if matching_faq:
            text = f"💡 {matching_faq['q']}: {matching_faq['a']}"
        else:
            text = f"I don't have information about '{faq_topic}' in my FAQ database. I can help with maintenance, warranty, battery, panels, inverter, installation, cost, or savings."
        
        return jsonify({"fulfillmentText": text})
    
    return jsonify({"fulfillmentText":"I can help with system size, cost, installers, net metering, and FAQs."})

@app.get('/')
def health():
    return 'OK',200

if __name__=='__main__':
    port=int(os.environ.get('PORT',8080))
    app.run(host='0.0.0.0', port=port)