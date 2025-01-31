from flask import Flask, request, jsonify
from utils.mongo_utils import add_recipe, get_recipes
from utils.sqlite_utils import log_interaction, get_interaction
from utils.s3_utils import initialize_s3_bucket, upload_to_s3
from utils.dynamo_utils import initialize_dynamodb_table, add_recipe_metadata, get_recipe_metadata
import os
from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")
# Add recipe route
@app.route("/add_recipe", methods=["POST"])
def add_recipe_route():
    data = request.json
    
    # Handle the file upload if present
    if "file" in request.files:
        file = request.files["file"]
        s3_path = upload_to_s3(file)
        data["image_url"] = s3_path
    
    # Add recipe to MongoDB
    add_recipe(data)
    
    # Add metadata to DynamoDB
    recipe_id = data["recipe_id"]
    views = data.get("views", 0)
    likes = data.get("likes", 0)
    tags = data.get("tags", [])
    add_recipe_metadata(recipe_id, views, likes, tags)
    
    return jsonify({"message": "Recipe added successfully!"})

# Get all recipes route
@app.route("/get_recipes", methods=["GET"])
def get_recipes_route():
    recipes = get_recipes()
    return jsonify(recipes)


# Interact with recipe route (like, view, etc.)
@app.route("/interact", methods=["POST"])
def interact():
    data = request.json
    recipe_id = data["recipe_id"]
    action = data["action"]  # e.g., "like", "view"
    log_interaction(recipe_id, action)
    return jsonify({"message": f"{action.capitalize()} logged for recipe {recipe_id}."})

# Get interaction for a recipe
@app.route("/get_interaction/<recipe_id>", methods=["GET"])
def get_interaction_route(recipe_id):
    interaction = get_interaction(recipe_id)
    if interaction:
        return jsonify({"recipe_id": interaction[0], "action": interaction[1]})
    else:
        return jsonify({"message": "No interaction found."}), 404

# File upload route
initialize_s3_bucket()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/upload_file", methods=["POST"])
def upload_file():
    file = request.files["file"]
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(file_path)
    s3_path = upload_to_s3(file_path, file.filename)
    return jsonify({"message": "File uploaded successfully!", "s3_path": s3_path})

# Initialize DynamoDB
initialize_dynamodb_table()

# Add metadata for a recipe
@app.route("/add_metadata/<recipe_id>", methods=["POST"])
def add_metadata(recipe_id):
    data = request.json
    views = data.get("views", 0)
    likes = data.get("likes", 0)
    tags = data.get("tags", [])
    add_recipe_metadata(recipe_id, views, likes, tags)
    return jsonify({"message": "Metadata added successfully!"})

# Get metadata for a recipe
@app.route("/get_metadata/<recipe_id>", methods=["GET"])
def fetch_metadata(recipe_id):
    metadata = get_recipe_metadata(recipe_id)
    return jsonify(metadata)


if __name__ == "__main__":
    app.run(debug=True)
