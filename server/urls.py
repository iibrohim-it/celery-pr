from django.contrib import admin
from django.urls import path, include, re_path

from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.views.generic.base import RedirectView


schema_view = get_schema_view(
    openapi.Info(
        title="My API",
        default_version='v1',
        description="API documentation",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # Swagger JSON / YAML
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'
    ),

    # Swagger UI
    re_path(
        r'^swagger/$',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
    ),

    # ReDoc
    re_path(
        r'^redoc/$',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'
    ),
    path(
    '',
    RedirectView.as_view(
        url='/swagger/',
        permanent=False
    )
),
    # My App URLs
    path('', include('myapp.urls')),
]