import os
import kaidenkai
import unittest
import tempfile
from sqlalchemy.sql import insert
from werkzeug import generate_password_hash

class KaidenkaiTestCase(unittest.TestCase):

# ----------------------- set up and tear down ----------------------- #
    def setUp(self):
        self.db_fd, p = tempfile.mkstemp()
        kaidenkai.app.config['DATABASE'] = 'sqlite:///' + p
        kaidenkai.app.config['TESTING'] = True
        self.app = kaidenkai.app.test_client()

        with kaidenkai.app.app_context():
            kaidenkai.init_db()
            db = kaidenkai.get_db()
            ins = kaidenkai.users.insert().values(
                username='admin',
                name='Nidhoggr, the net serpent',
                password=generate_password_hash('default'),
                bio='Devourer of packets')
            db.execute(ins)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(kaidenkai.app.config['DATABASE'][10:])

# ------------------------------ Utils ------------------------------- #

    def login(self, username, password):
        """helper to log in"""
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        """helper to log out"""
        return self.app.get('/logout', follow_redirects=True)


# ------------------------------ Tests ------------------------------- #

    # Check that we get the proper output when the database is emtpy 
    def test_empty_db(self):
        """check that we get the right message when the post database
           is empty"""
        rv = self.app.get('/')
        assert 'No entries here so far' in rv.data

    # Check that we can log in and out, and that login fails
    # for invalid credentials
    def test_login_logout(self):
        """make sure login/logout works"""
        rv = self.login('admin', 'default')
        assert 'You were logged in' in rv.data
        rv = self.logout()
        assert 'You were logged out' in rv.data
        rv = self.login('adminx', 'default')
        assert 'Invalid username' in rv.data
        rv = self.login('admin', 'defaultx')
        assert 'Invalid password' in rv.data

    # Check that messages can be posted, and will allow html in the body
    # but not the title
    def test_messages(self):
        """make sure posting works"""
        self.login('admin', 'default')
        rv = self.app.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</strong> allowed here'
            ), follow_redirects=True)
        assert 'No entries here so far' not in rv.data
        assert '&lt;Hello&gt;' in rv.data
        assert '<strong>HTML</strong> allowed here' in rv.data


if __name__ == '__main__':
    unittest.main()

