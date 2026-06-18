from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret-key"

DATABASE = os.path.join(os.path.dirname(__file__), "health.db")

# Simple in-memory AI-style responses for mental & social health
EMOTION_RESPONSES = {
    "happy": {
        "emoji": "😊",
        "title": "Feeling Good",
        "message": "That's wonderful — notice it, enjoy it, and share it if you like!",
        "exercise": "Smile for 30 seconds and take three deep, slow breaths (inhale 4, exhale 6).",
        "actions": ["Share a thank-you message", "Move your body for 5 minutes", "Write one thing you're grateful for"],
    },
    "sad": {
        "title": "Feeling Sad",
        "message": "It's okay to feel sad. Small comforts and connection can help.",
        "exercise": "Try slow breathing: inhale 4, hold 2, exhale 6 for 3 minutes.",
        "actions": ["Call a friend or family member", "Sit with a warm drink", "Take a short walk"],
    },
    "stressed": {
        "title": "Feeling Stressed",
        "message": "Pause and simplify one task. Small steps reduce overwhelm.",
        "exercise": "Box breathing: inhale 4, hold 4, exhale 4, hold 4 — repeat 4 times.",
        "actions": ["List 3 quick wins", "Try a 5-minute grounding exercise", "Stretch your shoulders and neck"],
    },
    "anxious": {
        "emoji": "😰",
        "title": "Feeling Anxious",
        "message": "Grounding and breathing help bring you back to the present.",
        "exercise": "5–4–3–2–1 grounding: name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste.",
        "actions": ["Practice grounding", "Slowly sip water", "Tell someone how you feel"],
    },
    "angry": {
        "emoji": "😡",
        "title": "Feeling Angry",
        "message": "Pause and create space before reacting; your body needs soothing.",
        "exercise": "Take 6 slow breaths, focusing on releasing tension each exhale.",
        "actions": ["Step away for a minute", "Clench/release fists a few times", "Write down what's upsetting you"],
    },
    "lonely": {
        "emoji": "🤝",
        "title": "Feeling Lonely",
        "message": "Reaching out helps — connection, even small, matters.",
        "exercise": "Send a short message to someone or join a local group online.",
        "actions": ["Message a friend", "Look for a local meetup or support group", "Do a small kindness for someone else"],
    },
    "overwhelmed": {
        "emoji": "😵",
        "title": "Feeling Overwhelmed",
        "message": "Break tasks into tiny steps and give yourself permission to pause.",
        "exercise": "Set a 10-minute timer and focus on one tiny task — then pause.",
        "actions": ["Make a 3-item to-do list", "Practice a 2-minute breathing break", "Ask for help with one task"],
    },
    "confused": {
        "emoji": "🤔",
        "title": "Feeling Confused",
        "message": "Clarifying one small question can create clarity — start there.",
        "exercise": "Write down three questions you have and one possible next step.",
        "actions": ["Research one clear next step", "Ask someone for their view", "Take a short walk to think"],
    },
    "hopeful": {
        "emoji": "🌤️",
        "title": "Feeling Hopeful",
        "message": "Hold onto this feeling and plan a small next step to build it.",
        "exercise": "Spend 2 minutes imagining a positive outcome in detail.",
        "actions": ["Set a small goal", "Share hope with someone", "Record a short voice note about it"],
    },
    "tired": {
        "emoji": "😴",
        "title": "Feeling Tired",
        "message": "Rest is productive — notice what your body needs.",
        "exercise": "Try a 10-minute gentle rest or power nap if possible.",
        "actions": ["Hydrate and have a light snack", "Do a gentle stretch", "Plan a short rest break"],
    },
    "motivated": {
        "title": "Feeling Motivated",
        "message": "Great — use that energy to move one important task forward.",
        "exercise": "Spend 10 focused minutes on a meaningful task (Pomodoro).",
        "actions": ["Start with a 10-minute task", "Celebrate progress", "Share your plan with someone"],
    },
    "depressed": {
        "title": "Feeling Depressed",
        "message": "I'm sorry you're feeling this way. If feelings persist, please reach out to a professional or trusted person.",
        "exercise": "Try a small, gentle activity: sit by a window, notice surroundings, breathe slowly.",
        "actions": ["Tell a trusted person how you feel", "Contact a local helpline or mental health professional", "If you are thinking about harming yourself, seek emergency help immediately"],
        "resources": [
            {"label": "National Helpline (India)", "link": "https://www.nhp.gov.in/"}
        ]
    },
    "default": {
        "title": "Thank you for sharing",
        "message": "Small caring habits help. Try one of the short actions below.",
        "exercise": "Try a simple breathing exercise: inhale for 4, exhale for 6, repeat 5 times.",
        "actions": ["Take a short walk", "Drink water", "Talk to someone you trust"]
    }
}
SOCIAL_SCHEMES = [
    {
        "name": "Aarogyasri Health Scheme",
        "description": "State-level support for serious medical treatments for eligible low-income families.",
        "purpose": "Provides cashless hospital treatment for eligible low-income families for major illnesses and surgeries.",
        "started": "2007",
        "benefits": "Cashless surgeries, coverage for major illnesses, reduced financial burden.",
        "eligibility": "Families below the poverty line or qualifying income slabs as per state rules.",
        "apply": "How to apply: 1) Visit the official portal; 2) Check eligibility with your ration/SECC/ID; 3) Register or visit the local health office; 4) Submit required documents listed on the portal.",
        "link": "https://aarogyasri.telangana.gov.in/"
    },
    {
        "name": "Ayushman Bharat (PM-JAY)",
        "description": "Central health insurance scheme providing hospitalization coverage for eligible families.",
        "purpose": "Offers health insurance coverage for secondary and tertiary care to reduce out-of-pocket expenditure.",
        "started": "2018",
        "benefits": "Hospitalization cover, cashless treatment at empanelled hospitals, financial protection.",
        "eligibility": "Households identified through SECC and other central/state lists.",
        "apply": "How to apply: 1) Visit the PM-JAY portal; 2) Search your name with Aadhaar or ration card; 3) If eligible, note your golden card details or visit nearest public health center for enrollment assistance.",
        "link": "https://www.pmjay.gov.in/"
    },
    {
        "name": "National Health Mission (NHM)",
        "description": "Supports primary health services, immunization, maternal and child health programs.",
        "purpose": "Strengthen primary health care, maternal and child health, and public health systems across states.",
        "started": "2005",
        "benefits": "Improved access to primary care, immunization, maternal and child health services, disease control programs.",
        "eligibility": "Programs under NHM are broadly for all citizens, with special services for rural and vulnerable groups.",
        "apply": "How to access services: 1) Contact your local Primary Health Centre (PHC) or community health worker; 2) Register for specific programs (immunization, maternal care) at the PHC; 3) Follow listed schedules and document requirements on the NHM portal.",
        "link": "https://nhm.gov.in/"
    },
    {
        "name": "Janani Suraksha Yojana (JSY)",
        "description": "A maternity benefit scheme to encourage institutional delivery among pregnant women.",
        "purpose": "Increase institutional deliveries and reduce maternal and neonatal mortality by providing cash incentives.",
        "started": "2005",
        "benefits": "Cash assistance for institutional delivery, better antenatal and postnatal care uptake.",
        "eligibility": "Pregnant women from eligible households; eligibility rules vary by state.",
        "apply": "How to apply: 1) Register at the nearest ANC clinic or PHC during pregnancy; 2) Provide required ID and health records; 3) The facility will guide JSY enrollment and cash assistance process.",
        "link": "https://nhm.gov.in/index1.php?lang=1&level=2&sublinkid=1242&lid=295"
    },
    {
        "name": "National Mental Health Programme (NMHP)",
        "description": "Provides community-based mental health services and support through district mental health programs.",
        "purpose": "Deliver basic mental health care through district and community programs and integrate mental health into general health services.",
        "started": "1982",
        "benefits": "Access to community mental health services, counselling, and improved referral pathways.",
        "eligibility": "Open to all; services prioritized for people with mental health conditions.",
        "apply": "How to access: 1) Visit the district mental health program or nearest government hospital; 2) Ask for outpatient mental health services or counselling; 3) For community support, contact the district mental health coordinator listed on the NMHP portal.",
        "link": "https://www.nhp.gov.in/mental-health_pg"
    },
    {
        "name": "TB Free Treatment & Support",
        "description": "Free diagnosis and treatment for tuberculosis under the national TB elimination program.",
        "purpose": "Provide free diagnosis, treatment and follow-up for TB to eliminate the disease as a public health problem.",
        "started": "Ongoing (national TB program era since 1990s; RNTCP scaled in late 1990s)",
        "benefits": "Free testing, free medication, treatment support and follow-up, reduced transmission.",
        "eligibility": "All individuals suspected of or diagnosed with TB are eligible for free services.",
        "apply": "How to access: 1) Visit the nearest TB diagnostic center or government hospital; 2) Get tested under the program; 3) If positive, treatment and follow-up are provided free of charge; details on the portal.",
        "link": "https://tbcindia.gov.in/"
    },
    {
        "name": "Disability Welfare & Pension Schemes",
        "description": "Financial support and rehabilitation services for persons with disabilities (state and central schemes).",
        "purpose": "Provide financial assistance, pensions, and rehabilitation/support services to persons with disabilities.",
        "started": "Various state/central schemes (ongoing)",
        "benefits": "Monthly pensions, assistive devices, rehabilitation, and access to inclusive services.",
        "eligibility": "Individuals with certified disabilities as per government definitions.",
        "apply": "How to apply: 1) Obtain disability certificate from authorized medical board; 2) Visit the social welfare office or state portal; 3) Submit application form, disability certificate, and ID proof; 4) Follow instructions on the state welfare portal.",
        "link": "https://disabilityaffairs.gov.in/"
    }
]

FIRST_AID = [
    {
        "topic": "Snake Bite",
        "advice": "Stay calm, keep the bitten limb still and lower than the heart, remove tight jewelry, do not cut or suck the wound, and get to the hospital immediately.",
    },
    {
        "topic": "Road Accident",
        "advice": "Check if the person is breathing, apply firm pressure to stop bleeding, do not move the head or neck, and call emergency help right away.",
    },
    {
        "topic": "Burns",
        "advice": "Cool the burn under running water for at least 10 minutes, cover it gently with clean cloth, do not pop blisters, and seek medical care for large or deep burns.",
    },
    {
        "topic": "Choking",
        "advice": "If the person cannot breathe, give 5 firm back blows between the shoulder blades, then 5 abdominal thrusts until the object is cleared.",
    },
    {
        "topic": "Fracture",
        "advice": "Keep the injured limb still, pad it with cloth or soft material, avoid moving it, and transport to a medical facility for proper care.",
    },
    {
        "topic": "Heart Attack",
        "advice": "Call emergency services immediately, make the person sit comfortably, loosen tight clothing, and keep them calm until help arrives.",
    },
    {
        "topic": "Poisoning",
        "advice": "Do not induce vomiting unless instructed by a professional; immediately call emergency services or a poison control center and provide information about the substance.",
    }
]

HOSPITALS = [
    {
        "name": "City General Hospital",
        "pincode": "500001",
        "budget": "low",
        "address": "1 Main St, City Center",
        "phone": "+91-40-11111111",
        "services": "Emergency, General Medicine, Orthopedics"
    },
    {
        "name": "Green Health Clinic",
        "pincode": "500002",
        "budget": "medium",
        "address": "12 Green Road",
        "phone": "+91-40-22222222",
        "services": "Outpatient, Pediatrics"
    },
    {
        "name": "Sunrise Medical Center",
        "pincode": "500003",
        "budget": "high",
        "address": "45 Sunrise Ave",
        "phone": "+91-40-33333333",
        "services": "Surgery, ICU, Cardiology"
    },
    {
        "name": "Care Plus Hospital",
        "pincode": "500004",
        "budget": "low",
        "address": "9 Care St",
        "phone": "+91-40-44444444",
        "services": "Primary Care, Diagnostics"
    },
    {
        "name": "Harmony Health Clinic",
        "pincode": "500005",
        "budget": "medium",
        "address": "77 Harmony Lane",
        "phone": "+91-40-55555555",
        "services": "Wellness, Counseling"
    }
]

PHYSICAL_CONDITIONS = [
    {"condition": "Back Pain", "tips": ["💪 Keep a straight posture.", "🧘 Do gentle stretches daily.", "🛌 Rest when painful."]},
    {"condition": "Cold & Cough", "tips": ["💧 Drink warm fluids.", "😴 Rest well.", "🤒 See a doctor for high fever."]},
    {"condition": "Headache", "tips": ["💧 Stay hydrated.", "🔇 Rest in a quiet room.", "🖥️ Reduce screen time."]},
    {"condition": "Fever", "tips": ["🤒 Monitor temperature.", "💧 Drink fluids.", "🩺 Visit clinic if >38°C for 2 days."]},
    {"condition": "Stomach Ache", "tips": ["🍵 Sip warm water.", "🥣 Eat light, bland food.", "🚨 Seek care for severe pain/vomiting."]},
    {"condition": "Allergy", "tips": ["⚠️ Avoid triggers.", "🧴 Use antihistamines if prescribed.", "🌿 Keep windows closed during high pollen."]},
    {"condition": "Sprain", "tips": ["❄️ Apply ice for 10–15 min.", "🩹 Compress and elevate.", "🩺 See doctor if swelling severe."]}
]

HELPFUL_TIPS = [
    "🍎 Eat balanced meals with fruits and protein.",
    "🏃 Stay active for 30 minutes most days.",
    "💧 Drink water and sleep regularly.",
    "🗣️ Talk to someone you trust when stressed."
]


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS medicine_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            medicine TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem TEXT NOT NULL,
            suggestion TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    # Ensure 'author' column exists in community_posts (migrate if needed)
    cursor.execute("PRAGMA table_info(community_posts)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'author' not in cols:
        try:
            cursor.execute("ALTER TABLE community_posts ADD COLUMN author TEXT DEFAULT 'Other'")
        except Exception:
            pass
    # Create new structured tables for problems and suggestions
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem TEXT NOT NULL,
            author TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER NOT NULL,
            suggestion TEXT NOT NULL,
            author TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(problem_id) REFERENCES community_problems(id)
        )
        """
    )
    # Migrate existing community_posts into new tables (best-effort)
    try:
        cursor.execute("SELECT id, problem, suggestion, author, created_at FROM community_posts")
        rows = cursor.fetchall()
        for r in rows:
            _id, problem_text, suggestion_text, author_text, created_at = r
            author_text = author_text if author_text else 'Other'
            cursor.execute("SELECT id FROM community_problems WHERE problem = ?", (problem_text,))
            found = cursor.fetchone()
            if found:
                pid = found[0]
            else:
                cursor.execute(
                    "INSERT INTO community_problems (problem, author, created_at) VALUES (?, ?, ?)",
                    (problem_text, author_text, created_at)
                )
                pid = cursor.lastrowid
            cursor.execute(
                "INSERT INTO community_suggestions (problem_id, suggestion, author, created_at) VALUES (?, ?, ?, ?)",
                (pid, suggestion_text, author_text, created_at)
            )
    except Exception:
        pass
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/home")
def index():
    return render_template("index.html")


@app.route("/physical")
def physical():
    conn = get_db_connection()
    reminders = conn.execute("SELECT * FROM medicine_reminders ORDER BY created_at DESC").fetchall()
    problems = conn.execute("SELECT * FROM community_problems ORDER BY created_at DESC").fetchall()
    suggestions = conn.execute("SELECT * FROM community_suggestions ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template(
        "physical.html",
        physical_conditions=PHYSICAL_CONDITIONS,
        reminders=reminders,
        problems=problems,
        suggestions=suggestions
    )


@app.route("/mental")
def mental():
    return render_template("mental_section.html")


@app.route("/social")
def social():
    return render_template(
        "social.html",
        schemes=SOCIAL_SCHEMES,
        first_aid=FIRST_AID,
        
    )


@app.route("/health-tips", methods=["POST"])
def health_tips():
    condition = request.form.get("condition")
    if not condition:
        flash("Please select a health issue to get tips.", "error")
        return redirect(url_for("home"))
    result = next((item for item in PHYSICAL_CONDITIONS if item["condition"] == condition), None)
    tips = result["tips"] if result else ["Rest, drink water, and see a doctor if symptoms worsen."]
    return render_template("tips.html", condition=condition, tips=tips)


@app.route("/add-reminder", methods=["POST"])
def add_reminder():
    name = request.form.get("name")
    medicine = request.form.get("medicine")
    time = request.form.get("time")
    if not name or not medicine or not time:
        flash("All fields are required for medicine reminders.", "error")
        return redirect(url_for("home") + "#medicine-reminder")
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO medicine_reminders (name, medicine, time, created_at) VALUES (?, ?, ?, ?)",
        (name, medicine, time, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    flash("Medicine reminder set successfully.", "success")
    return redirect(url_for("home") + "#medicine-reminder")


@app.route("/find-hospitals", methods=["POST"])
def find_hospitals():
    pincode = request.form.get("pincode")
    budget = request.form.get("budget")
    if not pincode or not budget:
        flash("Please enter a pincode and budget to find hospitals.", "error")
        return redirect(url_for("home") + "#hospital-search")
    note = None
    pincode = pincode.strip()

    # 1) exact pincode + budget
    matches = [h for h in HOSPITALS if h["pincode"] == pincode and h["budget"] == budget]
    if matches:
        return render_template("hospitals.html", pincode=pincode, budget=budget, hospitals=matches, note=None)

    # 2) exact pincode (any budget)
    matches = [h for h in HOSPITALS if h["pincode"] == pincode]
    if matches:
        note = "No hospitals in this pincode match the selected budget; showing all hospitals in this pincode."
        return render_template("hospitals.html", pincode=pincode, budget=budget, hospitals=matches, note=note)

    # 3) prefix (first 3 digits) + budget
    prefix = pincode[:3]
    matches = [h for h in HOSPITALS if h["pincode"].startswith(prefix) and h["budget"] == budget]
    if matches:
        note = "Showing regional (prefix) matches for your area."
        return render_template("hospitals.html", pincode=pincode, budget=budget, hospitals=matches, note=note)

    # 4) prefix (any budget)
    matches = [h for h in HOSPITALS if h["pincode"].startswith(prefix)]
    if matches:
        note = "No nearby hospitals matched the selected budget; showing regional hospitals by pincode prefix."
        return render_template("hospitals.html", pincode=pincode, budget=budget, hospitals=matches, note=note)

    # 5) numeric proximity (within a small range) — budget first
    try:
        pnum = int(pincode)
        nearby = sorted(HOSPITALS, key=lambda h: abs(int(h["pincode"]) - pnum))
        matches = [h for h in nearby if abs(int(h["pincode"]) - pnum) <= 10 and h["budget"] == budget]
        if matches:
            note = "Showing hospitals close by (numeric proximity) matching your budget."
            return render_template("hospitals.html", pincode=pincode, budget=budget, hospitals=matches, note=note)
        matches = [h for h in nearby if abs(int(h["pincode"]) - pnum) <= 10]
        if matches:
            note = "Showing nearby hospitals regardless of budget."
            return render_template("hospitals.html", pincode=pincode, budget=budget, hospitals=matches, note=note)
    except ValueError:
        # non-numeric pincode; skip numeric proximity
        pass

    # 6) budget-only anywhere
    matches = [h for h in HOSPITALS if h["budget"] == budget]
    if matches:
        note = "No nearby hospitals found; showing hospitals that match your budget."
        return render_template("hospitals.html", pincode=pincode, budget=budget, hospitals=matches, note=note)

    # 7) final fallback: all hospitals
    matches = HOSPITALS
    note = "No matches found for the given pincode and budget — showing all hospitals."
    return render_template("hospitals.html", pincode=pincode, budget=budget, hospitals=matches, note=note)


@app.route("/community", methods=["POST"])
def add_problem():
    problem = request.form.get("problem")
    author = request.form.get("author") or "Other"
    if not problem:
        flash("Please describe the health problem.", "error")
        return redirect(url_for("physical") + "#community-post")
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO community_problems (problem, author, created_at) VALUES (?, ?, ?)",
        (problem, author, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    flash("Problem posted. Others can now add suggestions.", "success")
    return redirect(url_for("physical") + "#community-post")


@app.route("/add-suggestion", methods=["POST"])
def add_suggestion():
    problem_id = request.form.get("problem_id")
    suggestion = request.form.get("suggestion")
    author = request.form.get("author") or "Other"
    if not problem_id or not suggestion:
        flash("Please provide a suggestion and select the problem.", "error")
        return redirect(url_for("physical") + "#community-post")
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO community_suggestions (problem_id, suggestion, author, created_at) VALUES (?, ?, ?, ?)",
        (problem_id, suggestion, author, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    flash("Suggestion added. Thank you for helping others!", "success")
    return redirect(url_for("physical") + "#community-post")


@app.route('/delete-reminder/<int:reminder_id>', methods=['POST'])
def delete_reminder(reminder_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM medicine_reminders WHERE id = ?', (reminder_id,))
    conn.commit()
    conn.close()
    flash('Reminder deleted.', 'success')
    return redirect(url_for('home') + '#medicine-reminder')


@app.route("/mental-ai", methods=["POST"])
def mental_ai():
    feeling = request.form.get("feeling")
    if not feeling:
        flash("Please select your feeling to get a caring response.", "error")
        return redirect(url_for("home") + "#mental-health")
    response = EMOTION_RESPONSES.get(feeling.lower(), EMOTION_RESPONSES["default"])
    return render_template("mental.html", feeling=feeling, response=response)


@app.route("/api/reminders")
def api_reminders():
    conn = get_db_connection()
    reminders = conn.execute("SELECT * FROM medicine_reminders ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in reminders])


if __name__ == "__main__":
    app.run(debug=True)
