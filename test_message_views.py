"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.id = 12345

        db.session.commit()

    def test_message_view(self):
        """Test valid message id view."""

        msg = Message(id=12345, text="test", user_id=self.testuser.id)
        
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            m = Message.query.get(12345)
            res = c.get(f'/messages/{m.id}')

            self.assertEqual(res.status_code, 200)
            self.assertIn(m.text, str(res.data))

    def test_invalid_message_show(self):
        """Test invalid message id view."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            res = c.get('/messages/01010101')

            self.assertEqual(res.status_code, 404)

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            res = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(res.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
            
    def test_add_message_logged_out(self):
        """Test adding message without being logged in."""      

        with self.client as c:
            res = c.post('/messages/new', data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))

    def test_delete_message(self):
        """Can user delete a message?"""

        msg = Message(id=12345, text="test", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            res = c.post('/messages/12345/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            m = Message.query.get(12345)
            self.assertIsNone(m)

    def test_delete_message_logged_out(self):
        """Test deleting a message without being logged in."""

        unauthorized = User.signup(username="unauthorized",
                                   email="unauthorized@unauthorized.com",
                                   password="unauthorized",
                                   image_url=None)
        unauthorized.id = 55555

        msg = Message(id=12345, text="test", user_id=self.testuser.id)

        db.session.add_all([unauthorized, msg])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 55555

            res = c.post('/messages/12345/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))

            m = Message.query.get(12345)
            self.assertIsNotNone(m)
            
    def test_delete_message_different_user(self):
        """Test deleting a message without authentication."""

        unauthorized = User.signup(username="unauthorized",
                                   email="unauthorized@unauthorized.com",
                                   password="unauthorized",
                                   image_url=None)
        unauthorized.id = 55555

        msg = Message(id=12345, text="test", user_id=self.testuser.id)

        db.session.add_all([unauthorized, msg])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 55555

            res = c.post('/messages/12345/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))

            m = Message.query.get(12345)
            self.assertIsNotNone(m)


