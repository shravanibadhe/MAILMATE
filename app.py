"""MailMate - a basic-NLP email reply generator (Flask + spaCy)."""
import re
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ---------- NLP pipeline (falls back to rules if the model is missing) ----------
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    HAS_MODEL = True
except Exception:
    import spacy
    nlp = spacy.blank("en")
    HAS_MODEL = False

# Lemma keywords per intent (weight = how strongly a word signals the intent)
INTENTS = {
    "meeting":   {"meeting": 3, "schedule": 2, "call": 2, "catch": 1, "sync": 2, "discuss": 1, "available": 1, "reschedule": 2},
    "interview": {"interview": 4, "candidate": 2, "hiring": 2, "position": 1, "round": 1},
    "leave":     {"leave": 3, "vacation": 3, "holiday": 2, "absent": 2, "sick": 2, "day off": 3},
    "complaint": {"complaint": 4, "issue": 2, "problem": 2, "broken": 3, "refund": 3, "disappointed": 3, "damaged": 3, "error": 2, "fail": 2, "not working": 3},
    "payment":   {"payment": 3, "invoice": 3, "bill": 2, "pay": 2, "due": 1, "receipt": 2, "transaction": 2},
    "order":     {"order": 3, "delivery": 2, "shipping": 2, "track": 2, "package": 2, "shipment": 2},
    "application": {"application": 3, "resume": 3, "cv": 3, "apply": 2, "job": 1, "vacancy": 2},
    "event":     {"event": 3, "invitation": 3, "invite": 3, "conference": 2, "party": 2, "webinar": 2, "workshop": 2, "rsvp": 3},
    "thanks":    {"thank": 2, "thanks": 2, "appreciate": 2, "grateful": 2},
}
NEGATIVE = {"angry", "bad", "broken", "disappointed", "frustrated", "terrible", "worst", "unacceptable", "damaged", "delay", "delayed", "problem", "issue", "fail", "error", "late", "poor", "complaint", "refund"}
POSITIVE = {"great", "thanks", "thank", "happy", "excellent", "appreciate", "pleased", "wonderful", "good", "love", "glad"}
URGENT = {"urgent", "asap", "immediately", "emergency", "critical", "today", "deadline", "priority"}


def analyze(email: str) -> dict:
    doc = nlp(email)
    ents = {"people": [], "dates": [], "times": [], "orgs": [], "money": []}
    label_map = {"PERSON": "people", "DATE": "dates", "TIME": "times", "ORG": "orgs", "MONEY": "money"}
    for ent in doc.ents:
        key = label_map.get(ent.label_)
        if key and ent.text.strip() not in ents[key]:
            ents[key].append(ent.text.strip())

    # Regex fallbacks (also useful when the statistical model misses things)
    for t in re.findall(r"\b\d{1,2}(?::\d{2})?\s?(?:am|pm|AM|PM)\b", email):
        if t not in ents["times"]:
            ents["times"].append(t)
    for m in re.findall(r"(?:₹|Rs\.?|\$|€)\s?[\d,]+(?:\.\d+)?", email):
        if m not in ents["money"]:
            ents["money"].append(m)
    ref = re.search(r"(?:order|invoice|ticket|ref(?:erence)?)\s*(?:no\.?|number|id)?\s*[#:]?\s*([A-Z0-9-]{4,})", email, re.I)
    email_addr = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", email)

    # Intent scoring ignores the sign-off block ("Thanks,\nName") so it can't skew results
    body_text = re.sub(r"\n\s*(?:regards|thanks|thank you|sincerely|cheers|best)[,!.]?\s*(?:\n.*)?$", "", email.strip(), flags=re.I)
    # also drop the greeting line ("Good morning,") so "good" is not counted as a positive word
    body_text = re.sub(r"^\s*(?:good (?:morning|afternoon|evening)|hi|hello|dear)[^\n]*\n", "", body_text, flags=re.I)
    body_doc = nlp(body_text)

    # Words / lemmas
    lemmas = [t.lemma_.lower() if HAS_MODEL else t.text.lower() for t in body_doc if not t.is_punct]
    lemma_text = " ".join(lemmas)
    lower = body_text.lower()

    scores = {}
    for intent, kws in INTENTS.items():
        s = sum(w for k, w in kws.items() if k in lemmas or k in lemma_text or k in lower)
        if s:
            scores[intent] = s
    intent = max(scores, key=scores.get) if scores else "general"
    total = sum(scores.values()) or 1
    confidence = round(scores.get(intent, 0) / total * 100) if scores else 40

    neg = sum(1 for l in lemmas if l in NEGATIVE)
    pos = sum(1 for l in lemmas if l in POSITIVE)
    sentiment = "negative" if neg > pos else "positive" if pos > neg else "neutral"
    urgent = any(l in URGENT or l.startswith("urgent") for l in lemmas)
    is_question = "?" in email

    # Sender name: signature line after a sign-off, else first PERSON entity
    sender = ""
    m = re.search(r"(?:regards|thanks|thank you|sincerely|cheers|best)[,!.]?\s*\n+\s*([A-Z][a-zA-Z.\-]+(?:\s[A-Z][a-zA-Z.\-]+)?)\s*$", email.strip(), re.I)
    if m:
        sender = m.group(1).strip()
    elif ents["people"]:
        sender = ents["people"][0]

    return {
        "intent": intent, "confidence": min(confidence, 99), "sentiment": sentiment,
        "urgent": urgent, "question": is_question, "sender": sender,
        "entities": ents, "reference": ref.group(1) if ref else "",
        "emails": email_addr, "words": len(doc), "model": "spaCy en_core_web_sm" if HAS_MODEL else "rule-based fallback",
    }


# ---------- Reply templates ----------
def when(a):
    e = a["entities"]
    bits = []
    if e["dates"]:
        bits.append(f"on {e['dates'][0]}")
    if e["times"]:
        bits.append(f"at {e['times'][0]}")
    return " ".join(bits)


def compose(a: dict, tone: str, action: str, my_name: str) -> str:
    name = a["sender"]
    w = when(a)
    ref = f" (ref. {a['reference']})" if a["reference"] else ""
    intent = a["intent"]
    yes = action == "accept"

    greet = {"formal": f"Dear {name or 'Sir/Madam'},", "friendly": f"Hi {name or 'there'},", "concise": f"Hi {name or 'there'},"}[tone]
    opener = {"formal": "Thank you for your email.", "friendly": "Thanks so much for reaching out!", "concise": ""}[tone]
    if a["sentiment"] == "negative" and intent in ("complaint", "order", "payment", "general"):
        opener = {"formal": "Thank you for bringing this to our attention, and please accept our sincere apologies.",
                  "friendly": "Thanks for letting us know - I'm really sorry about the trouble.",
                  "concise": "Sorry for the trouble."}[tone]

    body = []
    if intent == "meeting":
        if yes:
            body = [f"I'm available{(' ' + w) if w else ''} and happy to meet.", "Please send a calendar invite with the details."]
        else:
            body = [f"Unfortunately I'm unable to make it{(' ' + w) if w else ''}.", "Could you suggest a couple of other slots this week?"]
    elif intent == "interview":
        body = [f"I confirm my availability{(' ' + w) if w else ''} for the interview.", "Kindly share the venue or meeting link and any documents I should bring."] if yes else \
               [f"I regret that I can't attend{(' ' + w) if w else ''}.", "Would it be possible to reschedule to another date?"]
    elif intent == "leave":
        body = [f"Your leave request{(' ' + w) if w else ''} has been approved.", "Please hand over any pending work before you go."] if yes else \
               [f"I'm sorry, but we can't approve leave{(' ' + w) if w else ''} due to current workload.", "Let's talk about alternative dates."]
    elif intent == "complaint":
        body = [f"I've logged your concern{ref} and escalated it to the right team.", "You can expect an update within 24-48 hours."]
    elif intent == "payment":
        body = [f"We've received your message about the payment{ref}.", "Our accounts team will verify it and confirm shortly."]
    elif intent == "order":
        body = [f"Your order{ref} is being processed.", "We'll send tracking details as soon as it ships."]
    elif intent == "application":
        body = ["We've received your application and our recruitment team is reviewing your profile.", "If shortlisted, we'll contact you about next steps."]
    elif intent == "event":
        body = [f"I'd be delighted to attend{(' ' + w) if w else ''}.", "Please share any additional details."] if yes else \
               [f"Sadly I won't be able to attend{(' ' + w) if w else ''}.", "Thank you for thinking of me, and I hope it goes well."]
    elif intent == "thanks":
        body = ["You're very welcome - happy to help.", "Let me know if there's anything else you need."]
    else:
        body = ["I've read your message and will get back to you with a detailed response soon."]
    if a["question"] and intent == "general":
        body.append("I'll look into your questions and reply shortly.")
    if a["urgent"]:
        body.append("I understand this is urgent and will prioritise it.")

    if tone == "concise":
        body = body[:2]
    closing = {"formal": "Kind regards,", "friendly": "Cheers,", "concise": "Thanks,"}[tone]
    parts = [greet, opener] + [" ".join(body)] if tone != "formal" else [greet, opener, *body]
    text = "\n\n".join(p for p in parts if p)
    return f"{text}\n\n{closing}\n{my_name or '[Your Name]'}"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    if not email:
        return jsonify(error="Please paste an email first."), 400
    a = analyze(email)
    reply = compose(a, data.get("tone", "formal"), data.get("action", "accept"), (data.get("name") or "").strip())
    return jsonify(reply=reply, analysis=a)


if __name__ == "__main__":
    app.run(debug=True)
