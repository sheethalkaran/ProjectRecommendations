import os
import pandas as pd
from flask import Flask, render_template, request, redirect
import fitz  # PyMuPDF
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy 


# Initialize Flask app
app = Flask(__name__)

# Load spaCy NLP model for skill extraction
nlp = spacy.load("en_core_web_sm")  
# Configure file upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load dataset containing project details and skills
dataset_path = 'uploads/project_dataset.csv'
df = pd.read_csv(dataset_path)

# Define columns for skills in dataset
skills_columns = ['skill1', 'skill2', 'skill3', 'skill4', 'skill5', 'skill6']



# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from PDF, DOCX, and TXT resumes
def extract_text_from_resume(file_path):
    text = ""

    # If PDF, use PyMuPDF to extract text
    if file_path.endswith('.pdf'):
        doc = fitz.open(file_path)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text("text")

    # If DOCX, use python-docx to extract text
    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text

    # If TXT, simply read the file contents
    elif file_path.endswith('.txt'):
        with open(file_path, 'r') as file:
            text = file.read()

    return text

# Function to extract skills from resume text using spaCy
def extract_skills_from_text(text):
    # Process text with spaCy to identify entities
    doc = nlp(text)

    # Combine all skill columns from the dataset into one list
    all_skills = pd.concat([df[skill] for skill in skills_columns]).dropna().unique().tolist()

    # Convert skills to lowercase for case-insensitive matching
    all_skills_lower = [skill.lower() for skill in all_skills]

    # Find matching skills from the text entities
    skills_found = [entity.text.lower() for entity in doc.ents if entity.text.lower() in all_skills_lower]

    return list(set(skills_found))  # Remove duplicates and return

# Function to recommend projects based on user's skills using cosine similarity
def get_project_recommendations(user_skills):
    recommendations = []

    # Clean and normalize user skills
    user_skills = [skill.strip().lower() for skill in user_skills]

    # Combine project skills into a single string and lower case
    df['combined_skills'] = df[skills_columns].fillna('').agg(' '.join, axis=1).str.lower()

    # Use TF-IDF vectorizer to vectorize skills
    tfidf = TfidfVectorizer()
    skill_corpus = [' '.join(user_skills)] + df['combined_skills'].tolist()
    tfidf_matrix = tfidf.fit_transform(skill_corpus)

    # Compute cosine similarity between user's skills and project skills
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Prepare project recommendations
    for idx, similarity in enumerate(cosine_similarities):
        if similarity > 0:  # Include projects with at least some similarity
            project = df.iloc[idx]

            # Extract project skills and identify matching/missing skills
            project_skills = project[skills_columns].fillna('').str.lower().values.tolist()
            matching_skills = [skill for skill in user_skills if skill in project_skills]
            missing_skills = [skill for skill in project_skills if skill not in user_skills]

            recommendations.append({
                'project_name': project['Project Name'],
                'matching_count': len(matching_skills),
                'matching_skills': matching_skills,
                'missing_skills': missing_skills,
                'similarity_score': similarity
            })

    # Sort recommendations by matching count and similarity score
    sorted_recommendations = sorted(recommendations, key=lambda x: (-x['matching_count'], -x['similarity_score']))

    return sorted_recommendations[:10]  # Return top 10 recommendations




# Home route to display available skills for selection
@app.route('/')
def index():
    skills_list = pd.concat([df[skill] for skill in skills_columns]).dropna().unique().tolist()
    return render_template('index.html', all_skills=skills_list)


# Route to handle resume upload and text extraction
@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return 'No file part', 400

    file = request.files['resume']
    if file.filename == '':
        return 'No selected file', 400

    if file and allowed_file(file.filename):
        # Save the uploaded file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Extract text from the resume and identify skills
        text = extract_text_from_resume(file_path)
        skills = extract_skills_from_text(text)

        if not skills:
            return "No skills extracted from resume. Please check your resume content.", 400

        # Redirect to the next page with extracted skills
        skills_string = ','.join(skills)
        return redirect(f"/submit_skills?skills={skills_string}")
    else:
        return 'File format not supported', 400


# Route to display project recommendations based on submitted skills
@app.route('/submit_skills', methods=['GET', 'POST'])
def submit_skills():
    try:
        if request.method == 'POST':
            skills_string = request.form.get('skills', '')
        else:
            skills_string = request.args.get('skills', '')

        if not skills_string:
            return redirect('/')  # Redirect if no skills are provided

        # Split and clean the skills string
        skills = [skill.strip() for skill in skills_string.split(',') if skill.strip()]

        # Get project recommendations
        top_projects = get_project_recommendations(skills)

        return render_template('recommendations.html', top_projects=top_projects, skills=skills)
    except Exception as e:
        return "An error occurred, please try again.", 500



if __name__ == "__main__":
    app.run(debug=True)
