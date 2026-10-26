from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase

from .models import Dealer, Review

User = get_user_model()


class PublicDealerAPITests(TestCase):
    def setUp(self):
        self.kansas = Dealer.objects.create(
            source_id="test:ks:one",
            name="Kansas Test Dealer",
            city="Wichita",
            state="Kansas",
            state_code="KS",
        )
        Dealer.objects.create(
            source_id="test:mo:one",
            name="Missouri Test Dealer",
            city="Kansas City",
            state="Missouri",
            state_code="MO",
        )

    def test_health_and_admin_login_page(self):
        self.assertEqual(self.client.get("/djangoapp/health").status_code, 200)
        self.assertEqual(self.client.get("/admin/login/").status_code, 200)

    def test_dealer_list_and_state_filter(self):
        response = self.client.get("/djangoapp/get_dealers")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

        for state in ("Kansas", "KS", "kansas"):
            filtered = self.client.get("/djangoapp/get_dealers", {"state": state})
            self.assertEqual(filtered.status_code, 200)
            self.assertEqual([row["name"] for row in filtered.json()], ["Kansas Test Dealer"])

    def test_dealer_detail_and_reviews_query_validation(self):
        detail = self.client.get(f"/djangoapp/get_dealers/{self.kansas.pk}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["name"], "Kansas Test Dealer")
        self.assertEqual(self.client.get("/djangoapp/get_dealers/9999").status_code, 404)
        self.assertEqual(self.client.get("/djangoapp/get_reviews").status_code, 400)
        self.assertEqual(
            self.client.get("/djangoapp/get_reviews", {"dealerId": self.kansas.pk}).json(),
            [],
        )
        self.assertEqual(self.client.get("/djangoapp/get_reviews", {"dealerId": "9999"}).status_code, 404)

    def test_sentiment_analysis_uses_vader_for_exact_text(self):
        response = self.client.post(
            "/djangoapp/analyze_review",
            {"review": "Fantastic services"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["review"], "Fantastic services")
        self.assertEqual(response.json()["sentiment"], "positive")
        self.assertIn("compound", response.json()["scores"])

    def test_car_catalog_returns_course_make_model_pairs(self):
        response = self.client.get("/djangoapp/get_cars")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()["CarModels"]), 0)
        self.assertEqual(set(response.json()["CarModels"][0]), {"CarModel", "CarMake"})
        self.assertGreater(len(response.json()["makes"]), 0)

    def test_car_catalog_rejects_non_integer_make_id(self):
        self.assertEqual(self.client.get("/djangoapp/get_cars", {"makeId": "9999"}).status_code, 400)


class CourseRubricEndpointTests(TestCase):
    def setUp(self):
        call_command("seed_course_data", verbosity=0)

    def test_official_course_dealer_responses(self):
        all_dealers = self.client.get("/fetchDealers")
        self.assertEqual(all_dealers.status_code, 200)
        self.assertEqual(len(all_dealers.json()), 50)
        dealer = self.client.get("/fetchDealer/1")
        self.assertEqual(dealer.json()["full_name"], "Holdlamis Car Dealership")
        kansas = self.client.get("/fetchDealers/Kansas")
        self.assertTrue(all(row["state"] == "Kansas" for row in kansas.json()))

    def test_reviews_and_sentiment_use_expected_shapes(self):
        reviews = self.client.get("/fetchReviews/dealer/15")
        self.assertGreater(len(reviews.json()), 0)
        self.assertIn("review", reviews.json()[0])
        self.assertEqual(
            self.client.get("/analyze/Fantastic%20services").json(),
            {"sentiment": "positive"},
        )


class AuthenticationAndReviewTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.dealer = Dealer.objects.create(
            source_id="test:ks:review",
            name="Review Test Dealer",
            city="Topeka",
            state="Kansas",
            state_code="KS",
        )

    def csrf_token(self):
        response = self.client.get("/djangoapp/csrf")
        self.assertEqual(response.status_code, 200)
        return response.json()["csrfToken"]

    def registration_data(self):
        return {
            "username": "capstone-reviewer",
            "first_name": "Review",
            "last_name": "Tester",
            "email": "reviewer@example.test",
            "password": "Zebra-Forest-81!Sample",
        }

    def test_register_requires_csrf_and_creates_user_with_hashed_password(self):
        denied = self.client.post(
            "/djangoapp/register",
            self.registration_data(),
            content_type="application/json",
        )
        self.assertEqual(denied.status_code, 403)

        token = self.csrf_token()
        response = self.client.post(
            "/djangoapp/register",
            self.registration_data(),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="capstone-reviewer")
        self.assertTrue(user.check_password(self.registration_data()["password"]))
        self.assertNotEqual(user.password, self.registration_data()["password"])

    def test_login_logout_and_persisted_review(self):
        user = User.objects.create_user(
            username="signed-in-reviewer",
            password="Zebra-Forest-81!Sample",
            email="signedin@example.test",
            first_name="Signed",
            last_name="In",
        )
        token = self.csrf_token()
        login_response = self.client.post(
            "/djangoapp/login",
            {"userName": user.username, "password": "Zebra-Forest-81!Sample"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["userName"], user.username)
        self.assertEqual(login_response.json()["status"], "Authenticated")
        self.assertTrue(self.client.get("/djangoapp/session").json()["authenticated"])

        review_token = self.csrf_token()
        review_response = self.client.post(
            "/djangoapp/add_review",
            {"dealer_id": self.dealer.pk, "text": "A useful test review."},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=review_token,
        )
        self.assertEqual(review_response.status_code, 201)
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.get().text, "A useful test review.")

        logout_response = self.client.get("/djangoapp/logout")
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(logout_response.json(), {"userName": ""})
        self.assertFalse(self.client.get("/djangoapp/session").json()["authenticated"])

    def test_review_requires_login_and_valid_text(self):
        anonymous = self.client.post(
            "/djangoapp/add_review",
            {"dealer_id": self.dealer.pk, "text": "Review"},
            content_type="application/json",
        )
        self.assertIn(anonymous.status_code, (401, 403))
        self.assertEqual(Review.objects.count(), 0)

    def test_review_rejects_unknown_dealer(self):
        user = User.objects.create_user(username="valid-user", password="Zebra-Forest-81!Sample")
        self.client.force_login(user)
        token = self.csrf_token()
        response = self.client.post(
            "/djangoapp/add_review",
            {"dealer_id": 9999, "text": "Review"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 404)

