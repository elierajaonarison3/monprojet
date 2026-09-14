from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from authentication.views import DatabaseTestView
from authentication.views import InitialiserComptesView


def home(request):
    return JsonResponse({
        "message": "API Marche Public fonctionne",
        "status": "OK"
    })


urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/', include('authentication.urls')),
    path('api/test-db/', DatabaseTestView.as_view()),
    path('api/initialiser-comptes/', InitialiserComptesView.as_view()),

    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {
            'document_root': settings.MEDIA_ROOT,
        }
    ),
]