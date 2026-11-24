from .models import Product, CustomUser
from .serializers import ProductSerializer, RegisterSerializer
from .permissions import IsOwner
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse
from .tasks import send_activation_email
from django.db import transaction



class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = self.request.build_absolute_uri(
            reverse('activate', kwargs={
                'uidb64': uid,
                'token': token
            })
        )
        transaction.on_commit(
            lambda: send_activation_email.delay(user.email, url)
        )


class ActivateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=user_id)

        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response(
                {'error': 'Invalid activation link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_active:
            return Response(
                {'message': 'Account already activated'}
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = True
        user.save(update_fields=['is_active'])

        return Response(
            {'message': 'Account activated successfully!'}
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh = request.data.get("refresh")

        if not refresh:
            return Response({"detail": "refresh is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired token!"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwner]

    def list(self, request, *args, **kwargs):
        cache_key = 'product_list'
        data = cache.get(cache_key)

        if data is None:
            # print('data from db')
            serializer = self.get_serializer(self.get_queryset(), many=True)
            data = serializer.data
            cache.set(cache_key, data, 60)
        # else:
        #     print('data from redis')
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        cache_key = f'product_{pk}'
        data = cache.get(cache_key)

        if data is None:
            product = self.get_object()
            data = self.get_serializer(product).data
            cache.set(cache_key, data, 60)
        return Response(data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        cache.clear()

    def perform_update(self, serializer):
        serializer.save()
        cache.clear()

    def perform_destroy(self, instance):
        instance.delete()
        cache.clear()