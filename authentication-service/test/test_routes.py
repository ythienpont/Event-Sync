import pytest
from flask import Flask
from app.models import db, User
from app.routes import configure_routes

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    db.init_app(app)

    with app.app_context():
        db.create_all()
        sample_user = User()
        sample_user.username = "testuser"
        sample_user.set_password("testpassword")
        db.session.add(sample_user)
        db.session.commit()

    configure_routes(app)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_success(client):
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})
    assert response.status_code == 200
    assert b'Login successful' in response.data

def test_login_failure(client):
    response = client.post('/login', data={'username': 'testuser', 'password': 'wrongpassword'})
    assert response.status_code == 401
    assert b'Login failed' in response.data

def test_register_failure(client):
    response = client.post('/register', data={'username': 'testuser', 'password': 'newpassword'})
    assert response.status_code == 409
    assert b'User already exists' in response.data

def test_register_success(client):
    response = client.post('/register', data={'username': 'newuser', 'password': 'newpassword'})
    assert response.status_code == 200
    assert b'Registration successful' in response.data
