from flask import request, jsonify
from models import SharedCalendar, db

def configure_routes(app):
    @app.route("/share", methods=['POST'])
    def share():
        req_data = request.get_json()

        if req_data is None:
            return jsonify({'error': 'Missing JSON data'}), 400

        req_owner = req_data['owner']
        req_shared = req_data['shared']
        cal = SharedCalendar.query.filter_by(owner=req_owner, shared=req_shared).first()

        if cal:
            return jsonify({'message': 'Already shared'}), 409

        # TODO: Check if the user exists
 
        new_cal = SharedCalendar()
        new_cal.owner = req_owner
        new_cal.shared = req_shared
        db.session.add(new_cal)
        db.session.commit()
        return jsonify({'message': 'Calendar shared'}), 200
