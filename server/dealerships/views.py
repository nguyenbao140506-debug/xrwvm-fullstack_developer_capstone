import json
from pathlib import Path
from datetime import date
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .models import Dealer, Review
from .serializers import DealerSerializer, RegisterSerializer, ReviewSerializer, UserSerializer

sentiment_analyzer = SentimentIntensityAnalyzer()
COURSE_DATA_DIR = Path(settings.BASE_DIR) / "database" / "data"


def _course_data(filename, key):
    try:
        with (COURSE_DATA_DIR / filename).open(encoding="utf-8") as source:
            return json.load(source).get(key, [])
    except (OSError, json.JSONDecodeError):
        return []


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_token(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def session_status(request):
    user = request.user
    return Response({
        "authenticated": bool(user.is_authenticated),
        "user": UserSerializer(user).data if user.is_authenticated else None,
    })


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("userName", request.data.get("username", ""))
        password = request.data.get("password", "")
        if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
            return Response({"detail": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        return Response({
            "userName": user.get_username(),
            "status": "Authenticated",
            "message": "Login successful.",
            "user": UserSerializer(user).data,
        })


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logout(request)
        return Response({"userName": ""})

    def post(self, request):
        logout(request)
        return Response({"userName": "", "message": "Logout successful."})


@api_view(["GET"])
@permission_classes([AllowAny])
def dealer_list(request):
    dealers = Dealer.objects.all()
    state = request.query_params.get("state", "").strip()
    if state:
        dealers = dealers.filter(Q(state__iexact=state) | Q(state_code__iexact=state))
    return Response(DealerSerializer(dealers, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def dealers_by_state(request, state):
    dealers = Dealer.objects.filter(Q(state__iexact=state) | Q(state_code__iexact=state))
    return Response(DealerSerializer(dealers, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def dealer_detail(request, dealer_id):
    try:
        dealer = Dealer.objects.get(pk=dealer_id)
    except Dealer.DoesNotExist:
        return Response({"detail": "Dealer not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(DealerSerializer(dealer).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def dealer_reviews(request):
    raw_id = request.query_params.get("dealerId")
    if not raw_id:
        return Response({"detail": "The dealerId query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        dealer_id = int(raw_id)
    except (TypeError, ValueError):
        return Response({"detail": "dealerId must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
    if not Dealer.objects.filter(pk=dealer_id).exists():
        return Response({"detail": "Dealer not found."}, status=status.HTTP_404_NOT_FOUND)
    reviews = Review.objects.filter(dealer_id=dealer_id).select_related("dealer", "author")
    return Response(ReviewSerializer(reviews, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_review(request):
    dealer_id = request.data.get("dealer_id")
    text = request.data.get("review", request.data.get("text", ""))
    if not dealer_id or not isinstance(text, str) or not text.strip():
        return Response({"detail": "dealer_id and review text are required."}, status=status.HTTP_400_BAD_REQUEST)
    if len(text.strip()) > 2000:
        return Response({"detail": "Review text must be 2000 characters or fewer."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        dealer = Dealer.objects.get(pk=dealer_id)
    except (Dealer.DoesNotExist, ValueError, TypeError):
        return Response({"detail": "Dealer not found."}, status=status.HTTP_404_NOT_FOUND)
    raw_purchase_date = request.data.get("purchase_date") or None
    try:
        purchase_date = date.fromisoformat(raw_purchase_date) if raw_purchase_date else None
    except (TypeError, ValueError):
        return Response({"detail": "purchase_date must use YYYY-MM-DD format."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        car_year = int(request.data["car_year"]) if request.data.get("car_year") else None
    except (TypeError, ValueError):
        return Response({"detail": "car_year must be a number."}, status=status.HTTP_400_BAD_REQUEST)
    review = Review.objects.create(
        dealer=dealer,
        author=request.user,
        name=request.data.get("name") or request.user.get_full_name() or request.user.get_username(),
        text=text.strip(),
        purchase=bool(request.data.get("purchase", False)),
        purchase_date=purchase_date,
        car_make=str(request.data.get("car_make", ""))[:80],
        car_model=str(request.data.get("car_model", ""))[:100],
        car_year=car_year,
    )
    return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def analyze_review(request):
    text = request.data.get("review")
    if not isinstance(text, str) or not text.strip():
        return Response({"detail": "A non-empty review string is required."}, status=status.HTTP_400_BAD_REQUEST)
    scores = sentiment_analyzer.polarity_scores(text.strip())
    compound = scores["compound"]
    label = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"
    return Response({"review": text, "sentiment": label, "scores": scores, "analyzer": "VADER"})


@api_view(["GET"])
@permission_classes([AllowAny])
def analyze_path(request, text):
    scores = sentiment_analyzer.polarity_scores(text)
    compound = scores["compound"]
    label = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"
    return Response({"sentiment": label})


def course_dealer_payload(dealer):
    return {
        "id": dealer.pk,
        "city": dealer.city,
        "state": dealer.state,
        "st": dealer.state_code,
        "address": dealer.address,
        "zip": dealer.zip_code,
        "lat": dealer.latitude,
        "long": dealer.longitude,
        "short_name": dealer.short_name,
        "full_name": dealer.full_name or dealer.name,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def fetch_dealers(request, state=None):
    dealers = Dealer.objects.all()
    selected_state = state or request.query_params.get("state", "")
    if selected_state:
        dealers = dealers.filter(state__iexact=selected_state)
    return Response([course_dealer_payload(dealer) for dealer in dealers])


@api_view(["GET"])
@permission_classes([AllowAny])
def fetch_dealer(request, dealer_id):
    try:
        dealer = Dealer.objects.get(pk=dealer_id)
    except Dealer.DoesNotExist:
        return Response({"detail": "Dealer not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(course_dealer_payload(dealer))


@api_view(["GET"])
@permission_classes([AllowAny])
def fetch_reviews(request, dealer_id):
    reviews = Review.objects.filter(dealer_id=dealer_id).select_related("dealer", "author").order_by("id")
    return Response([
        {
            "name": review.name or (review.author.get_full_name() if review.author_id else "Customer"),
            "dealership": review.dealer_id,
            "review": review.text,
            "purchase": review.purchase,
            "purchase_date": review.purchase_date.strftime("%m/%d/%Y") if review.purchase_date else "",
            "car_make": review.car_make,
            "car_model": review.car_model,
            "car_year": review.car_year,
        }
        for review in reviews
    ])


@api_view(["GET"])
@permission_classes([AllowAny])
def car_catalog(request):
    """Return the course's official car fixture plus grouped data for the React view."""
    rows = _course_data("car_records.json", "cars")
    pairs = []
    seen = set()
    groups = {}
    for row in rows:
        make = row.get("make", "")
        model = row.get("model", "")
        pair = (model, make)
        if make and model and pair not in seen:
            seen.add(pair)
            pairs.append({"CarModel": model, "CarMake": make})
            groups.setdefault(make, []).append(model)
    make_id = request.query_params.get("makeId", "").strip()
    makes = list(groups)
    if make_id:
        try:
            make = makes[int(make_id) - 1]
        except (ValueError, IndexError):
            return Response({"detail": "makeId must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
        models = [{"Model_ID": i, "Model_Name": model} for i, model in enumerate(groups[make], start=1)]
        return Response({"models": models, "CarModels": pairs})
    return Response({
        "CarModels": pairs,
        "makes": [{"MakeId": i, "MakeName": make} for i, make in enumerate(makes, start=1)],
    })
