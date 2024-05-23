from flask import request, jsonify
from models import User, db
import sqlalchemy.exc

def configure_routes(app):
    @app.route("/login", methods=['POST'])
    def login():
        req_data = request.get_json()

        if req_data is None:
            return jsonify({'error': 'Missing JSON data'}), 400

        req_username = req_data.get('username')
        req_password = req_data.get('password')


        if not req_username or not req_password:
            return jsonify({'error': 'Missing username or password'}), 400

        user = User.query.filter_by(username=req_username).first()
        if not user:
            return jsonify({'message': 'User doesn\'t exist'}), 401
        elif user.password != req_password:
            return jsonify({'message': 'Wrong password'}), 401
        else:
            return jsonify({'message': 'Login successful'}), 200

    @app.route('/register', methods=['POST'])
    def register():
        try:
            req_data = request.get_json()
            if req_data is None:
                return jsonify({'error': 'Missing JSON data'}), 400

            req_username = req_data.get('username')
            req_password = req_data.get('password')

            if not req_username or not req_password:
                return jsonify({'error': 'Missing username or password'}), 400

            if User.query.filter_by(username=req_username).first():
                return jsonify({'message': 'User already exists'}), 409

            new_user = User()
            new_user.username = req_username
            new_user.password = req_password
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'message': 'Registration successful'}), 200
        except sqlalchemy.exc.SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Database error', 'details': str(e)}), 500
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


    @app.route("/user/<username>", methods=['GET'])
    def get_user(username):

        if not username:
            return jsonify({'error': 'Missing username'}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'message': 'User doesn\'t exist'}), 400
        else:
            return jsonify({'message': 'User found'}), 200
