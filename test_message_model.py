"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
# from sqlalchemy.exc import IntegrityError


from models import db, User, Message, Follows, Likes

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


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.user = u

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="test text",
            user_id=self.user.id
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertIsInstance(m, Message)
        self.assertEqual(m.text, "test text")
        self.assertEqual(m.user_id, self.user.id)
        self.assertEqual(m.user, self.user)

    def test_message_likes(self):
        """Does user message liking work as expected?"""

        m = Message(
            text="test text",
            user_id=self.user.id
        )

        db.session.add(m)
        db.session.commit()

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add(u2)
        db.session.commit()

        l = Likes(user_id=u2.id, message_id=m.id)

        db.session.add(l)
        db.session.commit()

        self.assertEqual(len(u2.likes), 1)
        self.assertEqual(len(self.user.likes), 0)
        self.assertEqual(len(m.likes), 1)
        self.assertIsInstance(l, Likes)

        Likes.query.delete()
        db.session.commit()

        self.assertEqual(len(u2.likes), 0)
        self.assertEqual(len(self.user.likes), 0)
        self.assertEqual(len(m.likes), 0)
