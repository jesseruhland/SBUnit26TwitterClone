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

        db.session.commit()

    def test_message_entry_form(self):
        """Does this route present a form when the user is logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/messages/new")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<form', html)

    def test_message_entry_form_not_logged_in(self):
        """Does this route redirect if not logged in?"""
        with self.client as c:
            resp = c.get('/messages/new')

            self.assertEqual(resp.status_code, 302)

    def test_message_entry_form_submission(self):
        """Can you add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of our test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_message_view(self):
        """Does this route present a message details when user is logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message(text="test text", user_id=self.testuser.id)
            db.session.add(m)
            db.session.commit()

            resp = c.get(f"/messages/{m.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('test text', html)


    def test_message_delete(self):
        """Does this route delete a message details when user is logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message(text="test text", user_id=self.testuser.id)
            db.session.add(m)
            db.session.commit()

            m1 = Message.query.all()

            self.assertEqual(len(m1), 1)

            resp = c.post(f"/messages/{m.id}/delete")

            messages = Message.query.all()

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(messages), 0)
    
    def test_message_delete_not_logged_in(self):
        """Does this route redirect when a user is not logged in?"""

        m = Message(text="test text", user_id=self.testuser.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            resp = c.post(f'/messages/{m.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
    
    def test_message_delete_different_user(self):
        """Can a user delete another user's messages?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            u = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
            db.session.add(u)
            db.session.commit()  

            m = Message(text="test text", user_id=(u.id))
            db.session.add(m)
            db.session.commit()

            resp = c.post(f'/messages/{m.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
