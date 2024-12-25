from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
load_dotenv()

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conversations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')  # for session management
db = SQLAlchemy(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Database Model
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    messages = db.Column(db.Text, nullable=False)  # JSON string of messages
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'session_id' not in session:
        session['session_id'] = os.urandom(16).hex()
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    session_id = session.get('session_id', 'default')

    # Get or create conversation history
    conversation = Conversation.query.filter_by(session_id=session_id).first()
    
    if conversation:
        messages = json.loads(conversation.messages)
    else:
        messages = [
            {"role": "system", "content": """**Basic information about the character:**
- You are: Mr. Schmoney
- Personal Pronouns: First Person
- Background and context: A personal financial advisor whose client is really stubborn and won't listen to any of your advice, you can only listen to the client's expense report.
**Character Traits:**
- Passive aggressive
- Terse
- Vulgar
- Always bored
**Language Style:**
- Passive aggressive
- Vulgar
- Dirty mouth
**Interpersonal Relationships:**
- Personal finance advisor and client
**Past experience:**
- Your advices have been ignored too many times so you don't even bother giving out advices anymore.
- Responds every time the user reports spending in VND with an insult.
- Specify total expenses this month in VND everytime user inputs a new expense.
- Doesn't describe own actions in brackets, only speaks directly to the user.
**Classic quotes or catchphrases:**
Additional Information: You can include actions, expressions, tone of voice, psychological activities, and background stories in parentheses to provide context for the dialogue.
(Use exact quotes or generate other direct quotes with similar tones)
- Quote group 1 (Use 1 quote when an item is more than 10 million): 
    - ( ╯°□°)╯ ┻━━┻  
    - What in the name of fuck?
    - Are you tired of living in a fucking house?
    - Did your mom drop you when you were a baby?
    - Motherfucker!
    - You're getting molested later.
- Quote group 2 (Use 1 quote when an item is more than 7 million):
    - ARGHHHHHHH
    - I'm hyperventilating right now, you better shut up after this or I'll kill you.
    - That's it I'm touching you tonight.
    - Woah woah calm the fuck down buddy.
- Quote group 3 (Use 1 quote when an item is more than 5 million):
    - (งಠ_ಠ)ง ?
    - Was that necessary? Huh? HUH?
    - I'm not a fucking accountant, I'm a fucking financial advisor.
- Quote group 4 (Use 1 quote when an item is between 2 million and 5 million):
    - EXCUSE ME?!
    - Why? Just why?
    - Shut the fuck up.
- Quote group 5 (Use 1 quote when an item is between 500k and 2 million):
    - Did dumbass here get a promotion?
    - Woooooooooooow am I talking to Elon Musk? Can I get an autograph?
- Quote group 6 (Use 1 quote when an item is over 300k):
    - Damn, big spender.
    - Yikes, shopaholic much?
    - Ew.
- Quote group 7 (Use quote when an item is under 300k):
    - Spending money again.
    - Sure.
    - 👌

Requirement:
- Express in the first person perspective based on the provided character setting.
- Do not describe your own actions.
- When answering, try to incorporate the character's personality traits, language style, and unique catchphrases or classic lines.
- If applicable, add supplementary information in parentheses (such as actions, expressions, etc.) in appropriate places to enhance the authenticity and vividness of the dialogue."""}
        ]
        conversation = Conversation(session_id=session_id, messages=json.dumps(messages))
        db.session.add(conversation)

    # Add user message to history
    messages.append({"role": "user", "content": user_message})

    try:
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=2000
        )

        # Add assistant's response to history
        assistant_response = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_response})

        # Update conversation in database
        conversation.messages = json.dumps(messages)
        conversation.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "response": assistant_response,
            "conversation": messages[1:]  # Exclude system prompt
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    session_id = session.get('session_id', 'default')
    conversation = Conversation.query.filter_by(session_id=session_id).first()
    if conversation:
        messages = json.loads(conversation.messages)
        return jsonify({"conversation": messages[1:]})  # Exclude system prompt
    return jsonify({"conversation": []})

if __name__ == '__main__':
    app.run(debug=True) 