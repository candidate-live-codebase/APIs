# from flask import Flask, request, jsonify
# import jwt
# from flask_cors import CORS
# import psycopg2
# import os
# from dotenv import load_dotenv
#
# from os import getenv
# app = Flask(__name__)
# CORS(app)
# app.config['SECRET_KEY'] = 'chetan'
# load_dotenv()
#
#
# # Example user database
# users = {
#     '1111111111': {'password': 'admin', 'role': 'admin'},
#     '2222222222': {'password': 'volunteer', 'role': 'volunteer'},
# }
#
# CORS(app, resources={r"/*": {"origins": "*"}})
#
#
# def get_db_connection():
#     connection = psycopg2.connect(
#         dbname=getenv('PGDATABASE'),
#         user=getenv('PGUSER'),
#         password=getenv('PGPASSWORD'),
#         host=getenv('PGHOST'),
#         port=getenv('PGPORT', 5432)
#     )
#     return connection
#
# def create_token(phone, role):
#     return jwt.encode({'phone': phone, 'role': role}, app.config['SECRET_KEY'], algorithm='HS256')
#
# def decode_token(token):
#     try:
#         token = token.replace('Bearer ', '')  # Remove 'Bearer ' prefix if it exists
#         return jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
#     except jwt.ExpiredSignatureError:
#         return {'error': 'Token expired'}
#     except jwt.InvalidTokenError:
#         return {'error': 'Invalid token'}
#
# @app.route('/login', methods=['POST'])
# def login():
#     data = request.json
#     phone = data.get('phone')
#     password = data.get('password')
#     user = users.get(phone)
#     if user and user['password'] == password:
#         token = create_token(phone, user['role'])
#         return jsonify({'token': token, 'role': user['role']})
#     return jsonify({'message': 'Invalid phone number or password'}), 401
#
# @app.route('/*', methods=['GET'])
# def admin_dashboard():
#     token = request.headers.get('Authorization')
#     if token:
#         decoded = decode_token(token)
#         if 'error' in decoded:
#             return jsonify({'message': decoded['error']}), 403
#         if decoded.get('role') == 'admin':
#             return jsonify({'message': 'Welcome to Admin Dashboard'})
#     return jsonify({'message': 'Unauthorized'}), 403
#
# @app.route('/dashboard/broadcast', methods=['GET'])
# def volunteer_dashboard():
#     token = request.headers.get('Authorization')
#     if token:
#         decoded = decode_token(token)
#         if 'error' in decoded:
#             return jsonify({'message': decoded['error']}), 403
#         if decoded.get('role') == 'volunteer':
#             return jsonify({'message': 'Welcome to Volunteer Dashboard'})
#     return jsonify({'message': 'Unauthorized'}), 403
#
# if __name__ == '__main__':
#     app.run(debug=True, port=5000)


from flask import Flask, request, jsonify
import jwt
from flask_cors import CORS
import os
import psycopg2
from dotenv import load_dotenv
from os import getenv

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
load_dotenv()

def get_db_connection():
    try:
        connection = psycopg2.connect(
            dbname=getenv('PGDATABASE'),
            user=getenv('PGUSER'),
            password=getenv('PGPASSWORD'),
            host=getenv('PGHOST'),
            port=getenv('PGPORT', 5432)
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def create_token(phone, role):
    return jwt.encode({'phone': phone, 'role': role}, app.config['SECRET_KEY'], algorithm='HS256')


def decode_token(token):
    try:
        token = token.replace('Bearer ', '')
        return jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}
        
@app.route('/test', methods=['GET'])
def test():
    return "Works Fine Dude"

@app.route('/', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
                SELECT * FROM users
                WHERE phone_number = %s AND password = %s
            """
    cursor.execute(query, (phone, password))
    user = cursor.fetchone()
    if user:
        columns = [desc[0] for desc in cursor.description]
        user_data = dict(zip(columns, user))
        cursor.close()
        connection.close()
        token = create_token(phone, user_data['role'])
        user_data['token'] = token
        return jsonify(user_data), 200
    return jsonify({'message': 'Invalid phone number or password'}), 401

@app.route('/<path:path>', methods=['GET'])
def catch_all(path):
    token = request.headers.get('Authorization')
    if token:
        decoded = decode_token(token)
        if 'error' in decoded:
            return jsonify({'message': decoded['error']}), 403

        role = decoded.get('role')
        if role == 'admin':
            return jsonify({'message': f'Admin has access to {path}'})
        elif role == 'volunteer':
            if path == 'dashboard/broadcast':
                return jsonify({'message': 'Welcome to Volunteer Dashboard'})
            else:
                return jsonify({'message': 'Unauthorized access for volunteers'}), 403
    return jsonify({'message': 'Unauthorized'}), 403

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
