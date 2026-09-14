from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from authentication.views import DatabaseTestView
from authentication.views import InitialiserComptesView
from config import settings

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
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
