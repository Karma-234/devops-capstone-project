"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service import talisman
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        talisman.force_https = False
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        """It should Read a single Account"""
        test_account = AccountFactory()

        # 1) Create an account first
        post_response = self.client.post(
            BASE_URL,
            json=test_account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        # 2) Get generated id from response JSON
        created = post_response.get_json()
        account_id = created["id"]

        # 3) Read that account back by id
        get_response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        # 4) Validate returned JSON matches what was sent
        data = get_response.get_json()
        self.assertEqual(data["id"], account_id)
        self.assertEqual(data["name"], test_account.name)
        self.assertEqual(data["email"], test_account.email)
        self.assertEqual(data["address"], test_account.address)
        self.assertEqual(data["phone_number"], test_account.phone_number)
        self.assertEqual(data["date_joined"], str(test_account.date_joined))
    
    def test_account_not_found(self):
        """It should return 404 when requesting an account that does not exist"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    
    def test_update_account(self):
        """It should Update an existing Account"""
        account = AccountFactory()
        create_resp = self.client.post(
        BASE_URL,
        json=account.serialize(),
        content_type="application/json"
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        created = create_resp.get_json()

        account_id = created["id"]
        update_data = created.copy()
        update_data["name"] = "Updated Name"
        update_data["email"] = "updated@example.com"
        update_resp = self.client.put(
        f"{BASE_URL}/{account_id}",
        json=update_data,
        content_type="application/json"
        )
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)

        updated = update_resp.get_json()
        self.assertEqual(updated["id"], account_id)
        self.assertEqual(updated["name"], "Updated Name")
        self.assertEqual(updated["email"], "updated@example.com")
        self.assertEqual(updated["address"], update_data["address"])
        self.assertEqual(updated["phone_number"], update_data["phone_number"])
        self.assertEqual(updated["date_joined"], update_data["date_joined"])

    def test_update_account_not_found(self):
        """It should not Update an Account that does not exist"""
        account = AccountFactory()
        response = self.client.put(
        f"{BASE_URL}/0",
        json=account.serialize(),
        content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_account_wrong_content_type(self):
        """It should not Update an Account with wrong media type"""
        account = AccountFactory()
        create_resp = self.client.post(
        BASE_URL,
        json=account.serialize(),
        content_type="application/json"
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        created = create_resp.get_json()
        account_id = created["id"]

        response = self.client.put(
        f"{BASE_URL}/{account_id}",
        json=created,
        content_type="text/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_delete_account(self):
        """It should Delete an Account"""
        account = self._create_accounts(1)[0]

        response = self.client.delete(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_account_not_found(self):
        """It should return 204 even when the Account does not exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list_accounts(self):
        """It should return a list of Accounts"""
        self._create_accounts(5)

        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_list_accounts_empty(self):
        """It should return an empty list when no Accounts exist"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(len(data), 0)
    
    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)
    def test_cors_security(self):
        """It should return CORS header"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')