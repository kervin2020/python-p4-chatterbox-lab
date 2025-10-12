from flask import Flask, request, make_response, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
import os

from models import db, Message

app = Flask(__name__)

# Use in-memory database for testing, file database for production
import sys
if 'pytest' in sys.modules:
    # Running in test environment - use in-memory database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    # Use absolute path for database to ensure it works in all environments
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

CORS(app)
migrate = Migrate(app, db)

db.init_app(app)

# Create a function to initialize the database
def init_db():
    with app.app_context():
        try:
            db.create_all()
            # If the database is empty, seed it with some data
            if Message.query.count() == 0:
                from faker import Faker
                fake = Faker()
                usernames = [fake.first_name() for i in range(4)]
                if "Duane" not in usernames:
                    usernames.append("Duane")
                
                messages = []
                for i in range(20):
                    message = Message(
                        body=fake.sentence(),
                        username=usernames[i % len(usernames)],
                    )
                    messages.append(message)
                
                db.session.add_all(messages)
                db.session.commit()
        except Exception as e:
            # If there's an error creating tables, try to continue
            # This handles cases where the database might already exist or have issues
            pass

# Initialize database immediately
init_db()

@app.route('/messages', methods=['GET'])
def messages():
    '''Returns all messages sorted by created_at in ascending order'''
    messages = Message.query.order_by(Message.created_at.asc()).all()
    return jsonify([message.to_dict() for message in messages])

@app.route('/messages', methods=['POST'])
def create_message():
    '''Creates a new message with body and username from request JSON'''
    try:
        data = request.get_json()
        
        if not data or 'body' not in data or 'username' not in data:
            return jsonify({"error": "Missing required fields: body and username"}), 400
        
        message = Message(
            body=data['body'],
            username=data['username']
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify(message.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create message"}), 400

@app.route('/messages/<int:id>', methods=['PATCH'])
def update_message(id):
    '''Updates the body of a message and returns the updated message'''
    try:
        message = db.session.get(Message, id)
        if not message:
            return jsonify({"error": "Message not found"}), 404
        
        data = request.get_json()
        if not data or 'body' not in data:
            return jsonify({"error": "Missing required field: body"}), 400
        
        message.body = data['body']
        db.session.commit()
        
        return jsonify(message.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update message"}), 400

@app.route('/messages/<int:id>', methods=['DELETE'])
def delete_message(id):
    '''Deletes a message from the database'''
    try:
        message = db.session.get(Message, id)
        if not message:
            return jsonify({"error": "Message not found"}), 404
        
        db.session.delete(message)
        db.session.commit()
        
        return "", 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete message"}), 400

if __name__ == '__main__':
    app.run(port=5555)