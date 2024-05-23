from flask import request, jsonify
from models import Event, RSVP, db
from datetime import datetime
import sqlalchemy.exc


def configure_routes(app):
    @app.route("/event", methods=['POST'])
    def create_event():
        req_data = request.get_json()
        if req_data is None:
            return jsonify({'error': 'Missing JSON data'}), 400

        required_fields = ['title', 'description', 'date', 'publicprivate', 'invites', 'organizer']
        if not all(field in req_data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            title = req_data['title']
            description = req_data['description']
            date = datetime.strptime(req_data['date'], '%Y-%m-%d')
            publicprivate = req_data['publicprivate'].lower() in ['true', '1', 'public']
            invites = req_data['invites'].split(';')
            organizer = req_data['organizer']

            event = Event(title=title, description=description, date=date, public=publicprivate, organizer=organizer)
            db.session.add(event)
            db.session.flush()

            for username in invites:
                if username:
                    rsvp = RSVP(event_id=event.id, username=username)
                    db.session.add(rsvp)

            db.session.commit()
            return jsonify({'message': 'Event created', 'event_id': event.id}), 200
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        except sqlalchemy.exc.SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Database error', 'message': str(e)}), 500
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    @app.route("/event/<int:event_id>")
    def view_event(event_id):
        try:
            event = Event.query.filter_by(id=event_id).first()
            if not event:
                return jsonify({'message': 'Event not found'}), 404

            req_data = request.get_json()
            if req_data is None:
                return jsonify({'error': 'Missing JSON data'}), 400

            username = req_data.get('username')
            if not username:
                return jsonify({'error': 'Missing username'}), 400

            is_organizer = (event.organizer == username)
            is_invited = RSVP.query.filter_by(event_id=event_id, username=username).count() > 0
            has_access = is_organizer or is_invited or event.public

            if not has_access:
                return jsonify({'error': 'No access'}), 403

            event_details = {
                'title': event.title,
                'date': event.date.strftime('%Y-%m-%d'),
                'organizer': event.organizer,
                'status': 'Public' if event.public else 'Private',
                'invites': [(rsvp.username, rsvp.status) for rsvp in event.invites]
            }

            return jsonify(event_details), 200
        except sqlalchemy.exc.SQLAlchemyError as e:
            return jsonify({'error': 'Database error', 'message': str(e)}), 500
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    @app.route("/event/public")
    def public_events():
        try:
            events = Event.query.filter_by(public=True).all()
            events_list = [(event.title, event.date.strftime('%Y-%m-%d'), event.organizer) for event in events]
            return jsonify(events_list), 200
        except sqlalchemy.exc.SQLAlchemyError as e:
            return jsonify({'error': 'Database error', 'message': str(e)}), 500
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    @app.route("/event/user-events/<username>", methods=['GET'])
    def get_user_events(username):
        try:
            organized_events = Event.query.filter_by(organizer=username).all()
            invited_events = Event.query.join(RSVP).filter(RSVP.username == username, RSVP.status.in_(['Will Attend', 'Maybe'])).all()
            events = list(set(organized_events + invited_events))

            event_details = [
                (event.id, event.title, event.date.strftime('%Y-%m-%d'), event.organizer, 'Organizing' if event.organizer == username else RSVP.query.filter_by(event_id=event.id, username=username).first().status, 'Public' if event.public else 'Private')
                for event in events
            ]
            return jsonify(event_details), 200
        except sqlalchemy.exc.SQLAlchemyError as e:
            return jsonify({'error': 'Database error', 'message': str(e)}), 500
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    @app.route('/invites', methods=['GET', 'POST'])
    def invites():
        try:
            req_data = request.get_json()
            if req_data is None:
                return jsonify({'error': 'Missing JSON data'}), 400

            username = req_data.get('username')
            if not username:
                return jsonify({'error': 'Missing username'}), 400

            pending_invites = RSVP.query.filter_by(username=username, status='Maybe').join(Event).all()
            invites_info = [
                {
                    'event_id': invite.event.id,
                    'title': invite.event.title,
                    'date': invite.event.date.strftime('%Y-%m-%d'),
                    'organizer': invite.event.organizer,
                    'privacy': 'Private' if not invite.event.public else 'Public'
                }
                for invite in pending_invites
            ]

            return jsonify({'invites': invites_info}), 200
        except sqlalchemy.exc.SQLAlchemyError as e:
            return jsonify({'error': 'Database error', 'message': str(e)}), 500
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    @app.route('/event/respond/<event_id>', methods=['POST'])
    def update_rsvp(event_id):
        try:
            event_id = int(event_id)
            req_data = request.get_json()
            if not req_data:
                return jsonify({'error': 'Missing JSON data'}), 400

            username = req_data.get('username')
            new_status = req_data.get('status')

            if not username or not new_status:
                return jsonify({'error': 'Missing required parameters'}), 400

            if new_status == 'Participate':
                new_status = 'Will Attend'
            elif new_status == 'Maybe Participate':
                new_status = 'Maybe'
            elif new_status == 'Don\'t Participate':
                new_status = 'Will Not Attend'
            else:
                return jsonify({'error': f'Invalid status: {new_status}'}), 400

            rsvp = RSVP.query.filter_by(event_id=event_id, username=username).first()
            if rsvp:
                try:
                    rsvp.status = new_status
                    db.session.commit()
                    return jsonify({'message': 'RSVP updated successfully'}), 200
                except sqlalchemy.exc.SQLAlchemyError as e:
                    db.session.rollback()
                    return jsonify({'error': 'Database error', 'message': str(e)}), 500
            else:
                return jsonify({'error': 'RSVP not found'}), 404
        except ValueError:
            return jsonify({'error': 'Invalid event ID'}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
