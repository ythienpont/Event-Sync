from flask import request, jsonify
from models import SharedCalendar, db
import requests
from sqlalchemy.exc import SQLAlchemyError

def configure_routes(app):
    @app.route("/share", methods=['POST'])
    def share():
        req_data = request.get_json()

        if req_data is None:
            return jsonify({'error': 'Missing JSON data'}), 400

        # Validate required fields
        req_owner = req_data.get('owner')
        req_shared = req_data.get('shared')
        if not req_owner or not req_shared:
            return jsonify({'error': 'Missing required fields: owner and shared'}), 400

        try:
            cal = SharedCalendar.query.filter_by(owner=req_owner, shared=req_shared).first()

            if cal:
                return jsonify({'message': 'Already shared'}), 409

            # TODO: Check if the user exists
            owner_exists = requests.get(f"http://authentication-service:5000/user/{req_owner}").status_code == 200

            if not owner_exists:
                return jsonify({'message': f"{req_owner} doesn't exist"}), 400

            shared_exists = requests.get(f"http://authentication-service:5000/user/{req_shared}").status_code == 200

            if not shared_exists:
                return jsonify({'message': f"{req_shared} doesn't exist"}), 400

            new_cal = SharedCalendar(owner=req_owner, shared=req_shared)
            db.session.add(new_cal)
            db.session.commit()
            return jsonify({'message': 'Calendar shared'}), 200

        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Database error', 'message': str(e)}), 500

    @app.route("/calendar/<username>", methods=['GET', 'POST'])
    def calendar(username):
        req_data = request.get_json()

        if req_data is None:
            return jsonify({'error': 'Missing JSON data'}), 400

        caller = req_data.get('caller')
        if not caller:
            return jsonify({'error': 'Missing required field: caller'}), 400

        try:
            # Check if the caller is the owner or the calendar has been shared with the caller
            calendar_access = caller == username or SharedCalendar.query.filter(
                (SharedCalendar.owner == username) & (SharedCalendar.shared == caller)
            ).first()

            if not calendar_access:
                return jsonify({'error': 'Access Forbidden'}), 403

            response = requests.get(f"http://event-service:5000/event/user-events/{username}")
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            return jsonify({'error': 'External service error', 'message': str(e)}), 502

        except SQLAlchemyError as e:
            return jsonify({'error': 'Database error', 'message': str(e)}), 500

        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
