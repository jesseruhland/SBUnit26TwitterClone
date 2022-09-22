"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

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


class UserViewTestCase(TestCase):
    """Test views for users."""

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


    def test_anon_homepage(self):
        """Does this route display the anon homepage if user not logged in?"""
        with self.client as c:
            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<h4>New to Warbler?</h4>", html)
    

    def test_homepage(self):
        """Does this route display the homepage if user logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", html)


    def test_signup_form(self):
        """Does this route display the signup form?"""
        with self.client as c:
            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Join Warbler today.", html)


    def test_signup_submission(self):
        """Does this handle signup?"""
        with self.client as c:
            resp = c.post('/signup', data={"username":"testuser2", "email":"test2@test.com", "password":"testuser2", "image_url":None})

            user = User.query.filter_by(username="testuser2").one()
            self.assertEqual(resp.status_code, 302)
            self.assertIsInstance(user, User)


    def test_login_form(self):
        """Does this route display the login form?"""
        with self.client as c:
            resp = c.get('/login')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Welcome back.", html)


    def test_login_submission(self):
        """Does this handle login?"""
        with self.client as c:
            resp = c.post('/login', data={"username":"testuser", "password":"testuser"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello, testuser!", html)


    def test_logout(self):
        """Does this handle logout?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("You have successfully logged out!", html)


    def test_users_page(self):
        """Does this page display all users?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/users')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="card user-card">', html)


    def test_users_profile(self):
        """Does this page show a user profile?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f'/users/{self.testuser.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser', html)
            self.assertIn(f'href="/users/{self.testuser.id}/likes"', html)


    def test_following_logged_in(self):
        """Does following work properly when logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            u = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
            db.session.add(u)
            db.session.commit()

            resp = c.post(f"/users/follow/{u.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser2', html)
            self.assertIn('Unfollow', html)
    

    def test_following_not_logged_in(self):
        """Does this page redirect if no user is logged in?"""
        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_followers_logged_in(self):
        """Does followers page work properly when logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            u = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
            db.session.add(u)
            db.session.commit()

            f = Follows(user_being_followed_id=u.id, user_following_id=self.testuser.id)
            db.session.add(f)
            db.session.commit()

            resp = c.get(f"/users/{u.id}/followers", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser', html)


    def test_followers_not_logged_in(self):
        """Does this page redirect if no user is logged in?"""
        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_new_follow_not_logged_in(self):
        """Does this page redirect if no user is logged in?"""
        with self.client as c:
            u = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
            db.session.add(u)
            db.session.commit()

            resp = c.post(f"/users/follow/{u.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_stop_following_logged_in(self):
        """Does stop following work properly when logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            u = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
            db.session.add(u)
            db.session.commit()

            f = Follows(user_being_followed_id=u.id, user_following_id=self.testuser.id)
            db.session.add(f)
            db.session.commit()

            resp = c.post(f"/users/stop-following/{u.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('@testuser2', html)
            self.assertNotIn('Unfollow', html)
        

    def test_likes_not_logged_in(self):
        """Does this page redirect if no user is logged in?"""
        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}/likes', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_liking_logged_in(self):
        """Does liking work properly when logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            u = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
            db.session.add(u)
            db.session.commit()

            m = Message(text="test text", user_id=u.id)
            db.session.add(m)
            db.session.commit()

            resp = c.post(f"/users/add_like/{m.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser2', html)
            self.assertIn('star', html)

    
    def test_remove_like_logged_in(self):
        """Does un-liking work properly when logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            u = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
            db.session.add(u)
            db.session.commit()

            m = Message(text="test text", user_id=u.id)
            db.session.add(m)
            db.session.commit()

            l = Likes(user_id=self.testuser.id, message_id=m.id)
            db.session.add(l)
            db.session.commit()

            resp = c.post(f"/users/remove_like/{m.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('@testuser2', html)
            self.assertNotIn('star', html)


    def test_user_profile_form_logged_in(self):
        """Does this route display the user profile form if user logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/users/profile')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("form", html)


    def test_user_profile_form_not_logged_in(self):
        """Does this route redirect if user not logged in?"""
        with self.client as c:
            resp = c.get('/users/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_user_profile_form_submission_logged_in(self):
        """Does this route update the user profile if user logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post('/users/profile', data={"username":"NewUserName", "password":"testuser"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@NewUserName", html)


    def test_user_profile_form_submission_not_logged_in(self):
        """Does this route redirect if user not logged in?"""
        with self.client as c:
            resp = c.get('/users/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)


    def test_user_delete_logged_in(self):
        """Does this route delete user profile if user logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Join Warbler today.", html)


    def test_user_delete_not_logged_in(self):
        """Does this route redirect if user not logged in?"""
        with self.client as c:
            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)