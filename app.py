import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime
from werkzeug.utils import secure_filename
from database import leads_collection, reviews_collection, projects_collection, db

# Portfolio collection
portfolio_collection = db["portfolio_works"]

app = Flask(__name__)
CORS(app)

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_json(data):
    if isinstance(data, list):
        for item in data:
            item["_id"] = str(item["_id"])
    elif isinstance(data, dict):
        data["_id"] = str(data["_id"])
    return data

# Static route uploads access karne ke liye
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== HTML PAGE ROUTES ====================

@app.route('/', methods=['GET'])
def index_page():
    return render_template('index.html')

@app.route('/admin', methods=['GET'])
def admin_page():
    return render_template('admin.html')

# ==================== 1. LEADS APIS ====================

@app.route('/api/leads', methods=['POST'])
def add_lead():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON payload"}), 400

        new_lead = {
            "name": data.get("name"),
            "business_name": data.get("business_name"),
            "phone": data.get("phone"),
            "plan_interested": data.get("plan_interested", "₹7,000 Starter"),
            "status": "New",
            "created_at": datetime.utcnow().strftime("%d-%m-%Y %H:%M")
        }
        result = leads_collection.insert_one(new_lead)
        return jsonify({
            "success": True,
            "message": "RS Technology: Lead saved successfully!",
            "lead_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/leads', methods=['GET'])
def get_all_leads():
    try:
        leads = list(leads_collection.find().sort("_id", -1))
        return jsonify(parse_json(leads)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== 2. REVIEWS APIS ====================

@app.route('/api/reviews', methods=['POST'])
def submit_review():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON payload"}), 400

        new_review = {
            "client_name": data.get("client_name"),
            "business_name": data.get("business_name"),
            "rating": int(data.get("rating", 5)),
            "review_text": data.get("review_text"),
            "status": "Pending",
            "created_at": datetime.utcnow().strftime("%d-%m-%Y")
        }
        result = reviews_collection.insert_one(new_review)
        return jsonify({
            "success": True,
            "message": "Review submitted. RS Technology team will verify it shortly.",
            "review_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/reviews/approved', methods=['GET'])
def get_approved_reviews():
    try:
        reviews = list(reviews_collection.find({"status": "Approved"}).sort("_id", -1))
        return jsonify(parse_json(reviews)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reviews', methods=['GET'])
def get_all_reviews_admin():
    try:
        reviews = list(reviews_collection.find().sort("_id", -1))
        return jsonify(parse_json(reviews)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reviews/<review_id>', methods=['PATCH'])
def update_review_status(review_id):
    try:
        data = request.get_json()
        new_status = data.get("status")
        reviews_collection.update_one(
            {"_id": ObjectId(review_id)},
            {"$set": {"status": new_status}}
        )
        return jsonify({"success": True, "message": f"Status updated to {new_status}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== 3. PORTFOLIO WORK APIS (WITH IMAGE UPLOAD) ====================

@app.route('/api/admin/portfolio', methods=['POST'])
def add_portfolio_work():
    try:
        title = request.form.get("title")
        category = request.form.get("category")
        project_link = request.form.get("project_link", "#")
        description = request.form.get("description", "")

        # Image file check
        if 'image_file' not in request.files:
            return jsonify({"success": False, "error": "Image file select karna zaroori hai"}), 400

        file = request.files['image_file']

        if file.filename == '':
            return jsonify({"success": False, "error": "Koi file select nahi ki gayi"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Unique filename banane ke liye timestamp jodte hain
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            image_url = f"/uploads/{unique_filename}"

            new_work = {
                "title": title,
                "category": category,
                "image_url": image_url,
                "project_link": project_link if project_link else "#",
                "description": description,
                "status": "Live",
                "created_at": datetime.utcnow().strftime("%d-%m-%Y")
            }
            result = portfolio_collection.insert_one(new_work)
            return jsonify({"success": True, "message": "Work image ke sath live ho gaya!", "work_id": str(result.inserted_id)}), 201
        else:
            return jsonify({"success": False, "error": "Invalid file format. Sirf PNG, JPG, JPEG, WEBP allowed hai."}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/portfolio/live', methods=['GET'])
def get_live_portfolio():
    try:
        works = list(portfolio_collection.find({"status": "Live"}).sort("_id", -1))
        return jsonify(parse_json(works)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/portfolio', methods=['GET'])
def get_all_portfolio_admin():
    try:
        works = list(portfolio_collection.find().sort("_id", -1))
        return jsonify(parse_json(works)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/portfolio/<work_id>', methods=['DELETE'])
def delete_portfolio_work(work_id):
    try:
        work = portfolio_collection.find_one({"_id": ObjectId(work_id)})
        if work and "image_url" in work:
            # Local image delete karna
            rel_path = work["image_url"].lstrip("/")
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)
            if os.path.exists(full_path):
                os.remove(full_path)

        portfolio_collection.delete_one({"_id": ObjectId(work_id)})
        return jsonify({"success": True, "message": "Project delete ho gaya!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)