"""User View tests."""

import os
from unittest import TestCase
from models import db, connect_db, Message, User, Follows, Likes
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
app.config['WTF_CSRF_ENABLED'] = False

db.create_all()

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.id = 12345

        self.u1 = User.signup("u1", "test1@test1.com", "pwd1", None)
        self.u1.id = 11111
        self.u2 = User.signup("u2", "test2@test2.com", "pwd2", None)
        self.u2.id = 22222
        # self.u3 = User.signup("u3", "test3@test3.com", "pwd3", None)
        # self.u4 = User.signup("u4", "test4@test4.com", "pwd4", None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_users_index(self):
        """Test view for users index."""

        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@u1", str(resp.data))
            self.assertIn("@u2", str(resp.data))

    def test_user_show(self):
        """Test view for user details page."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            res = c.get(f'/users/{self.testuser.id}')

            self.assertEqual(res.status_code, 200)
            self.assertIn('@testuser', str(res.data))

    def test_user_follower_view(self):
        """Test view for user's followers page."""

        f = Follows(user_being_followed_id=self.testuser.id, user_following_id=self.u1.id)
        db.session.add(f)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            res = c.get(f'/users/{self.testuser.id}/followers')
            self.assertEqual(res.status_code, 200)
            self.assertIn('u1', str(res.data))
            
    def test_user_follower_logged_out(self):
        """Test view for user's followers page without being logged in."""

        with self.client as c:
            res = c.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))
            
    def test_user_following_view(self):
        """Test view for user's following page."""

        f = Follows(user_being_followed_id=self.u1.id, user_following_id=self.testuser.id)
        db.session.add(f)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            res = c.get(f'/users/{self.testuser.id}/following')
            self.assertEqual(res.status_code, 200)
            self.assertIn('u1', str(res.data))

    def test_user_following_logged_out(self):
        """Test view for user's following page without being logged in."""

        with self.client as c:
            res = c.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))

    def test_add_like(self):
        """Test add like functionality."""

        m = Message(id=33333, text="test", user_id=self.u1.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/33333/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==33333).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser.id)

    def test_remove_like(self):
        """Test remove like functionality."""

        msg = Message(id=33333, text="test", user_id=self.u1.id)
        db.session.add(msg)
        db.session.commit()

        like = Likes(user_id=self.testuser.id, message_id=33333)
        db.session.add(like)
        db.session.commit()

        m = Message.query.get(33333)

        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser.id)

        l = Likes.query.filter(Likes.user_id==self.testuser.id and Likes.message_id==m.id).one()

        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)


