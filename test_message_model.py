"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "test1@test1.com", "pwd1", None)
        u1.id = 1111

        m1 = Message(text="msg1", user_id=1111)
        m1.id = 12345

        m2 = Message(text="msg2", user_id=1111)
        m2.id = 54321

        db.session.add_all([u1, m1, m2])
        db.session.commit()

        m1 = Message.query.get(m1.id)
        m2 = Message.query.get(m2.id)

        self.u1 = u1
        self.m1 = m1
        self.m2 = m2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

# Basic Message Tests

    def test_message_model(self):
        """Does basic model work?"""

        self.assertEqual(self.m1.text, "msg1")
        self.assertEqual(self.m2.text, "msg2")
        self.assertEqual(self.m2.user_id, 1111)
        self.assertEqual(self.m2.user_id, 1111)
        self.assertEqual(len(self.u1.messages), 2)


# Message Like Tests

    def test_message_likes(self):
        """Test relationship with user likes to messages."""

        self.u1.likes.append(self.m1)
        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == self.u1.id).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, self.m1.id)