from flask import Flask, request, render_template, jsonify, session
import openai
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Folder to save uploaded resumes
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for uploading resume
@app.route("/upload-resume", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part in the request."})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected for upload."})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Extract text from the resume
        resume_context = scan_resume(filepath)

        # Save resume context in the session for later use
        session["resume_context"] = resume_context
        app.logger.debug("Saved resume context in session:\n%s", resume_context)

        return jsonify({"success": True, "message": "File uploaded successfully!", "context": resume_context})
    else:
        return jsonify({"success": False, "message": "File type not allowed."})

# Function to scan the resume
def scan_resume(filepath):
    try:
        if filepath.endswith(".pdf"):
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        elif filepath.endswith(".txt"):
            with open(filepath, "r") as file:
                return file.read()
        else:
            return "Unsupported file type."
    except Exception as e:
        return f"Error reading the resume: {e}"

# Route to serve the content of `context.md`
@app.route("/edit-context", methods=["GET"])
def edit_context():
    try:
        with open("context.md", "r") as file:
            context = file.read()
        return render_template("edit_context.html", context=context)
    except Exception as e:
        return f"Error reading context file: {e}"

# Route to save the updated `context.md` content
@app.route("/save-context", methods=["POST"])
def save_context():
    try:
        new_context = request.form.get("context", "")
        with open("context.md", "w") as file:
            file.write(new_context)
        return jsonify({"success": True, "message": "Context updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error saving context file: {e}"})

# Initialize the OpenAI API client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to generate the cover letter
def generate_cover_letter(job_description, resume_context=""):
    try:
        with open("context.md", "r") as file:
            context = file.read()
    except Exception as e:
        return f"Error reading context file: {e}"

    # Combine the context, resume content, and job description
    combined_context = f"""
    {context}

    Resume Context:
    {resume_context}

    Job Description:
    {job_description}

    Write a tailored cover letter based on the above context, resume, and job description.
    """
    app.logger.debug("Combined Context for OpenAI API:\n%s", combined_context)

    try:
        # Generate the cover letter using OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional assistant specialized in writing cover letters."},
                {"role": "user", "content": combined_context}
            ],
            temperature=0.7,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"Error generating cover letter: {e}"

# Home route
@app.route("/")
def home():
    return render_template("index.html")

# Route to generate the cover letter
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    job_description = data.get("job_description", "")

    # Retrieve resume context from the session
    resume_context = session.get("resume_context", "")

    if not job_description:
        return jsonify({"error": "Job description is required."}), 400

    # Generate the cover letter
    cover_letter = generate_cover_letter(job_description, resume_context)

    return jsonify({"cover_letter": cover_letter})

# Debug route to check session data
@app.route("/session-debug", methods=["GET"])
def session_debug():
    return jsonify({"resume_context": session.get("resume_context", "No data in session")})

# Debug route to check cookies
@app.route("/cookies", methods=["GET"])
def cookies():
    return jsonify(request.cookies)

# Set a secret key for session management
app.secret_key = "your_secret_key"

if __name__ == "__main__":
    app.run(debug=True)