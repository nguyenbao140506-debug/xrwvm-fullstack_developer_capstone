from django.urls import path

from . import views

app_name = "dealerships"

urlpatterns = [
    path("health", views.health, name="health"),
    path("csrf", views.csrf_token, name="csrf"),
    path("session", views.session_status, name="session"),
    path("register", views.RegisterView.as_view(), name="register"),
    path("login", views.LoginView.as_view(), name="login"),
    path("logout", views.LogoutView.as_view(), name="logout"),
    path("get_dealers", views.dealer_list, name="dealer-list"),
    path("get_dealers/<int:dealer_id>", views.dealer_detail, name="dealer-detail"),
    path("get_dealers/<str:state>", views.dealers_by_state, name="dealers-by-state"),
    path("get_reviews", views.dealer_reviews, name="dealer-reviews"),
    path("add_review", views.add_review, name="add-review"),
    path("analyze_review", views.analyze_review, name="analyze-review"),
    path("get_cars", views.car_catalog, name="car-catalog"),
    path("analyze_review/<path:text>", views.analyze_path, name="analyze-review-get"),
]
