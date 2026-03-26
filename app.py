import re
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import pdfplumber
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': 'http://localhost:4200'}})

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SKILLS_DB = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
    'Flask', 'Django', 'FastAPI', 'Spring Boot', 'Express.js', 'NestJS', 'Laravel',
    'HTML', 'CSS', 'Angular', 'React', 'Vue.js', 'Next.js', 'Tailwind CSS',
    'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Firebase',
    'Machine Learning', 'Deep Learning', 'NLP', 'Pandas', 'NumPy', 'Scikit-learn', 
    'TensorFlow', 'PyTorch', 'Matplotlib', 'Seaborn', 'Power BI', 'Tableau',
    'Git', 'Docker', 'Kubernetes', 'Jenkins', 'AWS', 'Azure', 'Linux',
    'Figma', 'Adobe XD', 'Jira', 'Agile', 'Scrum', 'Wireframing', 'UI/UX Design'
]

def extract_text(file):
    text=''
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text+=page.extract_text() or ''
    return text

def extract_skills(text):
    text = text.lower()
    found = []
    for skill in SKILLS_DB:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text):
            found.append(skill)
    return list(set(found))

def experience_level(text):
    matches = re.findall(r'(\d+)\s*(?:years?|yrs?|year?)', text.lower()) 
    if matches:
        years = max(int(match) for match in matches)
        if years < 2:
            return 'Entry-level'
        elif 2 <= years < 5:
            return 'Mid-level'
        else:
            return 'Senior-level'
    return 'Fresher'

def generate_questions(data):
    try:
        role = data.get('role')
        experience_level = data.get('experience_level')
        skills = data.get('skills', [])

        if not role or not experience_level or not skills:
            raise ValueError('role, experience_level, and skills are required')

        basic_templates = [
            'What is {skill}?',
            'Explain the core concepts of {skill}.',
            'How have you used {skill} in a project?',
            'What are the advantages of {skill}?',
            'What are common challenges in {skill}?'
        ]

        advanced_templates = [
            'Explain advanced concepts in {skill}.',
            'How do you optimize performance in {skill}?',
            'Explain real-world use cases of {skill}.',
            'What are best practices in {skill}?',
            'How would you debug issues in {skill}?'
        ]

        questions = []

        if experience_level.lower() in ['entry-level', 'fresher']:
            for skill in skills[:5]:
                template = basic_templates[len(questions) % len(basic_templates)]
                questions.append(template.format(skill=skill))
        elif experience_level.lower() in ['mid-level', 'intermediate']:
            for i, skill in enumerate(skills[:5]):
                if i % 2 == 0:
                    template = basic_templates[i % len(basic_templates)]
                else:
                    template = advanced_templates[i % len(advanced_templates)]
                questions.append(template.format(skill=skill))
        else:
            for skill in skills[:5]:
                template = advanced_templates[len(questions) % len(advanced_templates)]
                questions.append(template.format(skill=skill))

        role_questions = {
            'Python Developer': [
                'How do you handle memory management in Python?',
                'Explain Python GIL and its implications.',
                'How do you structure a large Python project?'
            ],
            'Java Developer': [
                'Explain JVM memory management.',
                'How do you handle concurrency in Java?',
                'What design patterns do you commonly use?'
            ],
            'JavaScript Developer': [
                'Explain the event loop in JavaScript.',
                'How do you handle asynchronous operations?',
                'What are closures and how do you use them?'
            ]
        }

        if role in role_questions:
            questions.extend(role_questions[role][:2])

        return questions[:10]

    except Exception as e:
        print('Error in generate_questions:', e)
        raise

@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['resume']
    text=extract_text(file)

    data={
        'skills': extract_skills(text),
        'experience_level': experience_level(text)
    }

    return jsonify(data)

@app.route('/generate-questions', methods=['POST'])
def generate():
    data = request.json or {}
    print('generate-questions request payload:', data)
    try:
        questions = generate_questions(data)
        print('generate-questions response:', questions)
        return jsonify({'questions': questions})
    except ValueError as e:
        print('generate-questions validation error:', e)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print('Error generating questions:', e)
        return jsonify({'error': 'Failed to generate questions'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
