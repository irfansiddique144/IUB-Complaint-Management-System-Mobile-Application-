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
            
            # FIXED: Extracting serializable fields instead of the raw model instance
            'department': {
                'id': user.department.id,
                'name': user.department.name # Change '.name' to your actual field name if different
            } if user.department else None,
            
            # Assuming campus is also a ForeignKey, apply the same fix
            'campus': user.campus,  # Change '.name' to your actual field name if different
            
            'phone_number': user.phone_number,
        }

        return data