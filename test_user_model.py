"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError


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
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?
        Does the repr method work as expected?
        """

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
        self.assertEqual(repr(u), f"<User #{u.id}: {u.username}, {u.email}>")

    def test_following(self):
        """Does is_following successfully detect when user1 is following user2?
        Does is_following successfully detect when user1 is not following user2?
        Does is_followed_by successfully detect when user1 is followed by user2?
        Does is_followed_by successfully detect when user1 is not followed by user2?
        """

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )

        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        follow = Follows(user_being_followed_id=u2.id, user_following_id=u.id)

        db.session.add(follow)

        self.assertEqual(u.following, [u2])
        self.assertEqual(u2.following, [])
        self.assertEqual(u.is_following(u2), True)
        self.assertEqual(u2.is_following(u), False)
        self.assertEqual(u2.is_followed_by(u), True)
        self.assertEqual(u.is_followed_by(u2), False)

    def test_user_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""

        u = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url=""
        )
        
        db.session.commit()

        self.assertIsInstance(u, User)
    
    def test_user_signup_invalid(self):
        """Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""

        with self.assertRaises(IntegrityError):

            u = User.signup(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD",
                image_url=""
            )
            
            db.session.commit()

            u2 = User.signup(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD",
                image_url=""
            )

            db.session.commit()

        with self.assertRaises(Exception):

            u = User.signup(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD",
            )
            
    def test_user_authenticate(self):
        """Does User.authenticate successfully return a user when given a valid username and password?
        Does User.authenticate fail to return a user when the username is invalid?
        Does User.authenticate fail to return a user when the password is invalid?
        """

        u = User.signup(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD",
                image_url=""
            )
            
        db.session.commit()

        user = User.authenticate(username=u.username, password="HASHED_PASSWORD")

        not_user = User.authenticate(username=u.username, password="password")

        self.assertEqual(u, user)
        self.assertIsInstance(user, User)
        self.assertEqual(not_user, False)
        self.assertNotIsInstance(not_user, User)






