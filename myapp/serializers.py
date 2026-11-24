from .models import Product
from rest_framework.serializers import ModelSerializer
from .models import *


class RegisterSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            **validated_data, 
            is_active=False
        )
        return user


class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'price']

