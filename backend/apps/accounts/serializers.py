from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Creates a new user with a hashed password."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
        )

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "The two password fields did not match."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Read/write representation of the logged-in user's own profile."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "avatar",
            "date_of_birth",
            "is_email_verified",
            "is_staff",
            "date_joined",
        )
        read_only_fields = ("id", "email", "is_email_verified", "is_staff", "date_joined")

    def get_full_name(self, obj):
        return obj.get_full_name().strip() or obj.username


class LoginSerializer(serializers.Serializer):
    """Validates a username/email + password pair."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, trim_whitespace=False, style={"input_type": "password"}
    )

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        from django.contrib.auth import authenticate

        # Allow login with either username or email.
        lookup = {}
        if "@" in username:
            lookup["email"] = username.lower()
        else:
            lookup["username"] = username

        try:
            user_obj = User.objects.get(**lookup)
            user = authenticate(request=self.context.get("request"), username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is None:
            raise serializers.ValidationError(
                {"detail": "Unable to log in with the provided credentials."}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "This account has been deactivated."}
            )

        attrs["user"] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, style={"input_type": "password"})
    new_password = serializers.CharField(
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(
        required=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs.get("old_password")):
            raise serializers.ValidationError(
                {"old_password": "Your current password is incorrect."}
            )
        if attrs.get("new_password") != attrs.get("new_password_confirm"):
            raise serializers.ValidationError(
                {"new_password_confirm": "The two password fields did not match."}
            )
        password_validation.validate_password(attrs["new_password"], user)
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Requests a password-reset email for an existing account."""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            # Do not reveal whether an account exists (security).
            raise serializers.ValidationError("If that email exists, a reset link was sent.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirms a reset using the token from the email link."""

    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(
        required=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        if attrs.get("new_password") != attrs.get("new_password_confirm"):
            raise serializers.ValidationError(
                {"new_password_confirm": "The two password fields did not match."}
            )
        return attrs
