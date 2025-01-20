from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import ContractViewSet

schema_view = get_schema_view(
    openapi.Info(
        title = "Gerenciador de Contratos de Crédito Pessoal - API",
        default_version = 'v1',
        description = "Interface para cadastramento e consulta de dados de contratos de crédito pessoal.",
        terms_of_service = "https://www.google.com/policies/terms/",
        contact = openapi.Contact(email = "brunoluizalvesn@gmail.com"),
        license = openapi.License(name = "BSD License"),
    ),
    public = True,
    permission_classes = (permissions.AllowAny,),
)

router = DefaultRouter()
router.register('', ContractViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout = 0), name = 'schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout = 0), name = 'schema-redoc'),
]
