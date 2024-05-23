from flask import Flask, render_template, redirect, request, url_for, jsonify
import requests
import sys

app = Flask(__name__)


# The Username & Password of the currently logged-in User, this is used as a pseudo-cookie, as such this is not session-specific.
username = None
password = None

session_data = dict()


def save_to_session(key, value):
    session_data[key] = value


def load_from_session(key):
    return session_data.pop(key) if key in session_data else None  # Pop to ensure that it is only used once


def succesful_request(r):
    return r.status_code == 200


@app.route("/")
def home():
    global username

    if username is None:
        return render_template('login.html')
    else:
        try:
            # Assuming the event service is part of the same application
            response = requests.get("http://event-service:5000/event/public")
            if response.status_code == 200:
                public_events = [tuple(event) for event in response.json()]
            else:
                public_events = []  # Failed to fetch events, handle accordingly
        except requests.exceptions.RequestException:
            public_events = []  # Failed to fetch events, handle accordingly

        return render_template('home.html', username=username, events=public_events)


@app.route("/event", methods=['POST'])
def create_event():
    title, description, date, publicprivate, invites = request.form['title'], request.form['description'], request.form['date'], request.form['publicprivate'], request.form['invites']
    try:
        global username
        response = requests.post("http://event-service:5000/event", json={
            'title': title,
            'description': description,
            'date': date,
            'publicprivate': publicprivate,
            'invites': invites,
            'organizer': username,
        })

        if response.status_code == 200:
            return redirect('/')
        else:
            return render_template('create_event.html', title=title, description=description, date=date, publicprivate=publicprivate, invites=invites)
    except:
        return render_template('create_event.html', title=title, description=description, date=date, publicprivate=publicprivate, invites=invites)

@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    global username
    calendar_user = request.form['calendar_user'] if 'calendar_user' in request.form else username

    # ================================
    # FEATURE (calendar based on username)
    #
    # Retrieve the calendar of a certain user. The webpage expects a list of (id, title, date, organizer, status, Public/Private) tuples.
    # Try to keep in mind failure of the underlying microservice
    # =================================
    try:
        response = requests.post(f"http://calendar-service:5000/calendar/{calendar_user}", json={
            'caller': username,
        })
        if response.status_code == 200:
            calendar = response.json()
            success = True 
        else:
            calendar = None
            success = False
    except:
        calendar = None
        success = False # TODO: this might change depending on if the calendar is shared with you

    return render_template('calendar.html', username=username, password=password, calendar_user=calendar_user, calendar=calendar, success=success)

@app.route('/share', methods=['GET'])
def share_page():
    return render_template('share.html', username=username, password=password, success=None)

@app.route('/share', methods=['POST'])
def share():
    global username
    if username is None:
        return redirect('/')

    shared = request.form['username']

    try:
        response = requests.post("http://calendar-service:5000/share", json={
            'owner': username,
            'shared': shared
        })
        success = response.status_code == 200
    except requests.exceptions.RequestException:
        success = False

    save_to_session('success', success)

    return render_template('share.html', username=username, password=password, success=success)


@app.route('/event/<eventid>')
def view_event(eventid):

    # ================================
    # FEATURE (event details)
    #
    # Retrieve additional information for a certain event parameterized by an id. The webpage expects a (title, date, organizer, status, (invitee, participating)) tuples.
    # Try to keep in mind failure of the underlying microservice
    # =================================
    
    try:
        global username
        response = requests.get(f"http://event-service:5000/event/{eventid}", json={
            'username': username,
        })

        success = response.status_code == 200
        if success:
            data = response.json()
            event = [data['title'], data['date'], data['organizer'], data['status'],data['invites']]
        else:
            event = None
    except:
        success = False 
        event = None



    return render_template('event.html', username=username, password=password, event=event, success = success)

@app.route("/login", methods=['POST'])
def login():
    req_username, req_password = request.form['username'], request.form['password']
    try:
        response = requests.post("http://authentication-service:5000/login", json={
            'username': req_username,
            'password': req_password
        })
        success = response.status_code == 200
    except requests.exceptions.RequestException:
        success = False

    save_to_session('success', success)
    if success:
        global username, password

        username = req_username
        password = req_password

    return redirect('/')

@app.route("/register", methods=['POST'])
def register():
    req_username, req_password = request.form['username'], request.form['password']
    try:
        response = requests.post("http://authentication-service:5000/register", json={
            'username': req_username,
            'password': req_password
        })
        success = response.status_code == 200
    except requests.exceptions.RequestException:
        success = False

    save_to_session('success', success)
    if success:
        global username, password

        username = req_username
        password = req_password

    return redirect('/')

@app.route('/invites', methods=['GET'])
def invites():
    #==============================
    # FEATURE (list invites)
    #
    # retrieve a list with all events you are invited to and have not yet responded to
    #==============================

    try:
        global username
        response = requests.post(f"http://event-service:5000/invites", json={
            'username': username,
        })

        success = response.status_code == 200
        if success:
            my_invites = [(invite['event_id'], invite['title'], invite['date'], invite['organizer'], invite['privacy']) for invite in response.json().get('invites')]
        else:
            my_invites = []
    except:
        success = False 
        my_invites = []

    return render_template('invites.html', username=username, password=password, invites=my_invites)

@app.route('/invites', methods=['POST'])
def process_invite():
    data = request.get_json()
    if not data:
        return jsonify({'error': f'This is a mistake in the template code'}), 400

    eventId = data.get('event')[0]
    status = data.get('status')
    global username

    if not eventId or not status:
        return jsonify({'error': f'Missing event ID {eventId} or status {status}'}), 400

    try:
        response = requests.post(f"http://event-service:5000/event/respond/{str(eventId)}", json={
            'username': username,
            'status': status,
        })

        if response.status_code == 200:
            return redirect('/invites')
        else:
            # Log or return detailed response error for debugging
            return jsonify({
                'error': 'Failed to update RSVP',
                'status_code': response.status_code,
                'response_body': response.json()
            }), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/logout")
def logout():
    global username, password

    username = None
    password = None
    return redirect('/')
