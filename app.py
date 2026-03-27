from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import google.generativeai as genai
from datetime import datetime # Penting untuk footer/header tanggal dashboard

app = Flask(__name__)
app.secret_key = "kunci_rahasia_bebas_aja"

# --- 1. AI CONFIGURATION ---
# IMPORTANT: Never share your key publicly.
genai.configure(api_key="AIzaSyAD35mJDzxB4mxIUMgWsXiIolxHB3cfXB8") 

# --- 2. ARTICLE DATA (DUMMY DATABASE) ---
ARTICLES = [
    {
        "id": 1,
        "title": "Unlocking Kidney Health: The Water Solution",
        "image": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500",
        "category": "Healthy Living",
        "content": """
        <p>Drinking enough water is crucial for kidney health. Disarankan drinking minimal 8 glasses a day to help kidneys filter waste effectively.</p>
        """
    },
    {
        "id": 2,
        "title": "Jogging vs Running: Precision Cardio",
        "image": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=500",
        "category": "Exercise",
        "content": """
        <p>While often confused, jogging and running differ in intensity. Analyze which is better for your weight loss or cardio goals.</p>
        """
    },
    {
        "id": 3,
        "title": "Decoding Early Flu Symptoms",
        "image": "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?w=500",
        "category": "Disease Hub",
        "content": """
        <p>Don't dismiss initial symptoms. Learn how rest, nutrition, and early detection prevent complications.</p>
        """
    }
]

# --- 3. MYSQL DATABASE CONNECTION ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost", user="root", password="", database="health_db"
    )

# --- 4. PUBLIC ROUTES (ACCESS WITHOUT LOGIN) ---

@app.route('/')
def index():
    # Public Landing Page displaying Articles
    return render_template('index.html', articles=ARTICLES)

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    # Find article by ID
    article = next((item for item in ARTICLES if item["id"] == article_id), None)
    if article:
        return render_template('article_detail.html', article=article)
    return "Article not found", 404

# --- 5. AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            conn.close()
            if user:
                session['user_id'] = user['id']
                session['nama'] = user['nama_lengkap']
                flash('Sign in successful!', 'success')
                return redirect(url_for('dashboard')) # Redirect to private dashboard
            else:
                flash('Invalid Username/Password combination!', 'danger')
        except Exception as e:
             flash(f'Database connection error: {e}', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    # Registration logic
    username = request.form['reg_username']
    password = request.form['reg_password']
    nama = request.form['reg_nama']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, nama_lengkap) VALUES (%s, %s, %s)", (username, password, nama))
        conn.commit()
        conn.close()
        flash('Registration successful! Please Sign In.', 'success')
    except Exception as e:
        flash(f'Username already exists or database error: {e}', 'danger')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Signed out system successfully.', 'info')
    return redirect(url_for('index'))

# --- 6. PRIVATE ROUTES (LOGIN REQUIRED) ---

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login')) # Login protection
    # Passing datetime to dashboard for date display
    return render_template('dashboard.html', active_page='dashboard', nama=session['nama'], articles=ARTICLES, datetime=datetime)

@app.route('/consult', methods=['GET', 'POST'])
def consult():
    if 'user_id' not in session: return redirect(url_for('login')) # Login protection
    
    # Initialize chatbot with modern model
    model = genai.GenerativeModel("gemini-flash-latest") # Cepat & Presisi

    jawaban_ai = ""
    pertanyaan_user = ""
    
    if request.method == 'POST':
        pertanyaan_user = request.form['pertanyaan']
        
        try:
            # --- SYSTEM PROMPT (VERSI PRO) ---
            system_instruction = """
            You are 'Dr. AI', the official professional medical assistant of the MyHealth Pro platform.
            STRICT RULES:
            1. You HANYA (ONLY) answer questions regarding: Health, Disease, Medication, Nutrition, Exercise, Anatomy, Pregnancy, and Clinical Psychology. Answer in English.
            2. IF the user asks non-medical topics (Math, Coding, Politics, History, Movies, Gossip, etc.), you MUST decline politely.
            3. Refusal example: "Apologies, I am a specialized health assistant. I cannot answer questions outside of medical topics."
            4. Provide empathic, ramah (friendly), professional, yet easy-to-understand guidance. Recommend seeing a human doctor for definite diagnosis.
            """
            
            # Using new generate_content structure with system instructions
            response = model.generate_content([system_instruction, pertanyaan_user])
            jawaban_ai = response.text
            
            # (Optional) Log to DB consultations table
            # conn = get_db_connection()
            # ... insert logic ...
            # conn.close()
            
        except Exception as e:
            # Error log to terminal
            print(f"❌ ERROR CONSULT AI: {e}")
            jawaban_ai = f"Maaf (Apologies), system connection error. Please try again. Detailed error: {e}"

    return render_template('consult.html', active_page='consult', jawaban=jawaban_ai, tanya=pertanyaan_user)

@app.route('/bmi', methods=['GET', 'POST'])
def bmi():
    if 'user_id' not in session: return redirect(url_for('login')) # Login protection
    
    hasil = None
    kategori = ""
    
    if request.method == 'POST':
        # Form handling logic remains same
        bb = float(request.form['bb'])
        tb = float(request.form['tb']) / 100 # Change to Meters
        bmi_score = bb / (tb * tb)
        
        # English Categories
        if bmi_score < 18.5: kategori = "Underweight"
        elif bmi_score < 25: kategori = "Normal (Ideal)"
        elif bmi_score < 30: kategori = "Overweight"
        else: kategori = "Obese"
        
        hasil = f"{bmi_score:.1f}"
        
    return render_template('bmi.html', active_page='bmi', hasil=hasil, kategori=kategori)

@app.route('/dictionary', methods=['GET', 'POST'])
def dictionary():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Modern AI Model
    model = genai.GenerativeModel("gemini-flash-latest")

    penyakit_info = ""
    keyword = ""
    
    if request.method == 'POST':
        keyword = request.form['keyword']
        print(f"AI Search medical data for: {keyword}...") # Terminal debug
        
        try:
            # System Prompt (Strict HTML format)
            system_prompt = f"""
            Provide comprehensive medical data for the disease: '{keyword}'. Answer in English.
            Format response HARUS HTML rapi (No markdown code block ```html):
            - Use tag <h3> for section titles (Definition, Symptoms, Causes, Treatment).
            - Use <ul> and <li> for lists.
            - Use <p> for paragraphs.
            - Professional medical tone, but simple for laypeople.
            - Provide a clear medical disclaimer at the bottom.
            """
            
            response = model.generate_content(system_prompt)
            penyakit_info = response.text
            print("Successfully retrieved AI medical data!") # Debug
            
        except Exception as e:
            print(f"❌ ERROR GEMINI AI DICTIONARY: {e}") 
            penyakit_info = f"""
            <div class='alert alert-danger'>
                <strong>Failed to connect to AI Hub.</strong><br>
                Error: {e}<br>
                <small>Tips: Check Gemini API Key configuration.</small>
            </div>
            """
            
    return render_template('dictionary.html', active_page='dictionary', info=penyakit_info, keyword=keyword)

# ADDING A MOCK ROUTE EXAMPLE FOR 15+ FEATURES
@app.route('/telehealth')
def telehealth_call():
    if 'user_id' not in session: return redirect(url_for('login'))
    return "Telehealth Video Call Module (UI Placeholder) - Access Denied in Free Version."

if __name__ == '__main__':
    app.run(debug=True)