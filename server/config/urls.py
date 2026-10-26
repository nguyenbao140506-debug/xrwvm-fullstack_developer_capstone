from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import include, path, re_path
from django.views.generic import TemplateView

from dealerships import views


def frontend_index(request, *args, **kwargs):
    """Serve the built React app; explain how to start Vite during local development."""
    if (settings.FRONTEND_DIST / "index.html").is_file():
        return TemplateView.as_view(template_name="index.html")(request, *args, **kwargs)
    if settings.DEBUG:
        return HttpResponse(
            "<h1>Car Dealership Capstone API</h1>"
            "<p>Start the React frontend with <code>npm run dev</code> in server/frontend.</p>"
            '<p><a href="/djangoapp/health">API health</a></p>'
        )
    return HttpResponseNotFound("Frontend build is missing.")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("djangoapp/", include("djangoapp.urls")),
    path("fetchDealers", views.fetch_dealers, name="course-dealers"),
    path("fetchDealers/", views.fetch_dealers, name="course-dealers-slash"),
    path("fetchDealers/<str:state>", views.fetch_dealers, name="course-dealers-by-state"),
    path("fetchDealer/<int:dealer_id>", views.fetch_dealer, name="course-dealer"),
    path("fetchReviews/dealer/<int:dealer_id>", views.fetch_reviews, name="course-reviews"),
    re_path(r"^analyze/(?P<text>.+)$", views.analyze_path, name="course-sentiment"),
    path("", frontend_index, name="home"),
    re_path(r"^(?!admin/|djangoapp/|static/).*$", frontend_index, name="frontend-route"),
]
