from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        # First, get default token response
        data = super().validate(attrs)

        user = self.user

        # Add complete user information
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'email_verified': user.email_verified,
            'department': user.department,
            'campus': user.campus,
            'phone_number': user.phone_number,
        }

        return data