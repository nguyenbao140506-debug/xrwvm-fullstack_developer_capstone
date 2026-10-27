from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Dealer, Review
from .sentiment import review_sentiment

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email")


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(min_length=3, max_length=150)
    first_name = serializers.CharField(allow_blank=False, max_length=150)
    last_name = serializers.CharField(allow_blank=False, max_length=150)
    email = serializers.EmailField(allow_blank=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password")

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ReviewSerializer(serializers.ModelSerializer):
    sentiment = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    dealer_name = serializers.CharField(source="dealer.name", read_only=True)
    dealership = serializers.IntegerField(source="dealer_id", read_only=True)
    review = serializers.CharField(source="text", read_only=True)
    purchase_date = serializers.DateField(format="%m/%d/%Y", allow_null=True, read_only=True)

    class Meta:
        model = Review
        fields = (
            "id", "dealer", "dealer_name", "author", "text", "created_at",
            "name", "dealership", "review", "purchase", "purchase_date",
            "car_make", "car_model", "car_year", "sentiment",
        )
        read_only_fields = ("id", "dealer_name", "author", "created_at")

    def get_sentiment(self, obj):
        return review_sentiment(obj.text)

    def get_author(self, obj):
        if obj.author_id:
            return obj.author.get_username()
        return obj.name or "Customer"


class DealerSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    zip = serializers.CharField(source="zip_code", read_only=True)
    st = serializers.CharField(source="state_code", read_only=True)
    lat = serializers.FloatField(source="latitude", allow_null=True, read_only=True)
    long = serializers.FloatField(source="longitude", allow_null=True, read_only=True)
    short_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Dealer
        fields = (
            "id", "source_id", "name", "city", "state", "state_code", "address",
            "phone", "website", "latitude", "longitude", "source_url", "reviews",
            "zip", "st", "lat", "long", "short_name", "full_name",
        )
