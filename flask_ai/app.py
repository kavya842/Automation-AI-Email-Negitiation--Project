from flask import Flask, request, jsonify

app = Flask(__name__)

# root route
@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "This is Flask AI Server"}), 200

# health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Flask AI running"})


# classify email
@app.route("/classify_email", methods=["POST"])
def classify_email():
    data = request.get_json()
    body = data.get("body", "").lower()

    if "collab" in body or "sponsor" in body:
        category = "useful"
    else:
        category = "spam"

    return jsonify({"category": category})


# generate reply
@app.route("/generate_reply", methods=["POST"])
def generate_reply():
    data = request.get_json()
    min_price = data.get("min_price", 5000)

    reply = f"""
Hi,

Thanks for reaching out for collaboration.
Our standard collaboration fee starts from ₹{min_price}.
Please let us know if this works for you.

Regards,
Influencer
"""

    return jsonify({
        "reply": reply.strip(),
        "decision": "counter_offer"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
