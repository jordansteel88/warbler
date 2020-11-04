"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "test1@test1.com", "pwd1", None)
        u1.id = 1111

        u2 = User.signup("test2", "test2@test2.com", "pwd2", None)
        u2.id = 2222

        db.session.add_all([u1, u2])
        db.session.commit()

        u1 = User.query.get(u1.id)
        u2 = User.query.get(u2.id)

        self.u1 = u1
        self.u2 = u2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

# Basic Model Tests

    def test_repr(self):
        """Does __repr__ output as expected?"""

        repr = self.u1.__repr__()
        self.assertEqual(repr, '<User #1111: test1, test1@test1.com>')

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

# Follows Tests

    def test_is_following(self):
        """Does the is_following method detect follows both way?"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.following), 0)
    
    def test_is_followed_by(self):
        """Does the is_followed_by method detect follows both ways?"""

        self.u1.followers.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 0)
        self.assertEqual(len(self.u2.followers), 0)
        self.assertEqual(len(self.u1.followers), 1)
        self.assertEqual(len(self.u2.following), 1)

# User Signup Tests

    def test_valid_user_signup(self):
        """Test for valid signup credentials."""

        valid = User.signup("valid", "valid@valid.com", "valid", None)   
        valid.id = 12345
        db.session.commit()

        valid = User.query.get(12345)

        self.assertEqual(valid.username, "valid")
        self.assertEqual(valid.email, "valid@valid.com")
        self.assertTrue(valid.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        """Test for invalid username."""

        invalid = User.signup(None, "valid@valid.com", "valid", None)
        
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        """Test for invalid email."""

        invalid = User.signup("valid", None, "valid", None)
        
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        """Test for invalid password."""

        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", None, None)

# User Auth Tests

    def test_valid_auth(self):
        """Test for valid authentication."""

        user = User.query.get(1111)
        valid_auth = User.authenticate(self.u1.username, "pwd1")

        self.assertEqual(user, valid_auth)

    def test_invalid_username_auth(self):
        """Test for invalid username."""

        user = User.query.get(1111)
        invalid_auth = User.authenticate("invalid", "pwd1")

        self.assertNotEqual(user, invalid_auth)    
    
    def test_invalid_auth(self):
        """Test for invalid password."""

        user = User.query.get(1111)
        invalid_auth = User.authenticate(self.u1.username, "invalid")

        self.assertNotEqual(user, invalid_auth)