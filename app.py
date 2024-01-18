from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, session
from flask_mysqldb import MySQL
import fitz  # PyMuPDF
import openai
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import re
import sun

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Waleed@1999'
app.config['MYSQL_DB'] = 'policy'
app.config['MYSQL_HOST'] = 'localhost'

mysql = MySQL()
mysql.init_app(app)

UPLOAD_FOLDER ='uploads'
ALLOWED_EXTENSIONS = {'txt'}  # allowed file types

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
app.secret_key = os.getenv('SECRET_KEY')  # Use environment variable for secret key
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/get_sunburst')
def get_sunburst():
    return render_template('chart.html')

@app.route('/get_sunburst_data')
def get_sunburst_data():
    fig = sun.create_sunburst()
    graphJSON = fig.to_json()
    return jsonify(graphJSON=graphJSON)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Connect to the database
        cursor = mysql.connection.cursor()
        
        # Execute the query
        cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
        
        # Commit changes and close the connection
        mysql.connection.commit()
        cursor.close()

        # Redirect to the login page
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        password = request.form['password']

        # Connect to the database
        cursor = mysql.connection.cursor()
        
        # Execute query to find user by username
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        # Close cursor
        cursor.close()
        print(f"Fetched User: {user}")  # Debug print

        # Check if user exists and password matches
        if user and user[3] == password:  
            # User is authenticated
            print("Login successful")  # Debug print
            session['logged_in'] = True
            session['username'] = user[1]  
            flash('You were successfully logged in', 'success')
            return redirect(url_for('index'))  # Redirect to the index page or dashboard
        else:
            # Invalid credentials
            print("Login failed")  # Debug print
            flash('Wrong login credentials', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def truncate_tables():
    tables = ['personal_belongings', 'personal_not_covered_data', 'events_data', 'events_not_covered_data', 'coverage', 'annual', 'hover', 'dwelling']
    cursor = mysql.connection.cursor()
    for table in tables:
        cursor.execute(f'TRUNCATE TABLE {table}')
    mysql.connection.commit()
    cursor.close()

def insert_items(items, table_name, column_name):
    cursor = mysql.connection.cursor()
    for item in items:
        item = item.strip()  # Remove leading/trailing whitespace
        cursor.execute(f"INSERT INTO {table_name} ({column_name}) VALUES (%s)", (item,))
    mysql.connection.commit()
    cursor.close()

def parse_and_store_summary(summary):
    # Attempt to split the summary into parts based on the prompt numbers
    try:
        parts = re.split(r'\d+\)', summary)[1:]  # Split by '1)', '2)', etc. and ignore the first empty part
        if len(parts) < 9:
            raise ValueError("Summary does not contain all expected parts.")

        # Extract items from each part
        covered_items = [item.strip() for item in parts[0].split(",") if item.strip()]
        not_covered_items = [item.strip() for item in parts[1].split(",") if item.strip()]
        covered_events = [item.strip() for item in parts[2].split(",") if item.strip()]
        not_covered_events = [item.strip() for item in parts[3].split(",") if item.strip()]
        property_excluded_items = [item.strip() for item in parts[4].split(",") if item.strip()]
        coverage = [item.strip() for item in parts[5].split(",") if item.strip()]
        annual = [item.strip() for item in parts[6].split(",") if item.strip()]
        hover = [item.strip() for item in parts[7].split("*") if item.strip()]
        dwelling = [item.strip() for item in parts[8].split("*") if item.strip()]
    

        # Insert items into respective database tables
        insert_items(covered_items, 'personal_belongings', 'item_name')
        insert_items(not_covered_items, 'personal_not_covered_data', 'item_name')
        insert_items(covered_events, 'events_data', 'event_name')
        insert_items(not_covered_events, 'events_not_covered_data', 'event_name')
        insert_items(property_excluded_items, 'property_excluded_data', 'property_name')
        insert_items(coverage, 'coverage', 'total_coverage')
        insert_items(annual, 'annual', 'total_annual')
        insert_items(hover, 'hover', 'hover_data')
        insert_items(dwelling, 'dwelling', 'dwelling_address')
    except Exception as e:
        print(f"Error parsing summary: {e}")
        
'''
def extract_text_pymupdf(pdf_file_path):
    doc = fitz.open(pdf_file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text
'''
@app.route('/summarize', methods=['POST'])
def summarize():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        #file.save(save_path)

        # Check if file exists to avoid overwriting
        counter = 1
        while os.path.exists(save_path):
            name, extension = os.path.splitext(filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{name}_{counter}{extension}")
            counter += 1

        file.save(save_path)

        with open(save_path, 'r', encoding='utf-8') as file:
            extracted_text = file.read()

        truncate_tables()
        summary = summarize_text(extracted_text)# Parse the summary output
        print(summary)
        parse_and_store_summary(summary)
        
        # Rest of the existing code
        return jsonify({"summary": summary, "extractedText": extracted_text[:500]})


def summarize_text(text):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Here is the document context, only answer from the the context: " + text},
            {"role": "user", "content": 
            '''
            1) list all of the personal belongings covered under this insurance policy seperated by a commas in a database friendly manner. No need to use full sentences, just list the items. dont include conjunctions words, just seperate the data by commas
            2) list all of the personal belongings not covered under this insurance policy seperated by a commas in a database friendly manner. No need to use full sentences, just list the items. dont include conjunctions words, just seperate the data by commas
            3) list all of the events covered under this insurance policy seperated by a commas in a database friendly manner. No need to use full sentences, just list the items. dont include conjunctions words, just seperate the data by commas.
            4) list all of the events not covered under this insurance policy seperated by a commas in a database friendly manner. No need to use full sentences, just list the items. dont include conjunctions words, just seperate the data by commas.
            5) list all of the propeties excluded under this insurance policy seperated by a commas in a database friendly manner. No need to use full sentences, just list the items. dont include conjunctions words, just seperate the data by commas. some examples would be: Structures for business or farming purposes, Retaining Walls, Animals, birds or fish, Solar Panels, Wind Turbines
            6) what is the total overall coverage of this policy? only provide the number, no words or full sentences are needed
            7) what is the total overall annual premium of this policy? only provide the number, no words or full sentences are needed
            8) referencing the personal belongings items listed in 1), provide the combined/item limit coverage amount from the policy for each item. Seperate the ammounts by a star '*'. only provide the numbers, no full sentences needed. match the number of the listed personal belongings to their covered amounts. if the item's coverage amount is not excplictly mentioned, put 'unknown coverage'
            9) what is the address of the primary dwelling mentioned in this policy? only provide the address, for example '21 jump street'
            '''
            }
        ]
    )

    print("Total Tokens:", response.usage.total_tokens)
    return response.choices[0].message.content

if __name__ == '__main__':
    
    app.run(debug=False)