from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from authentication.views import DatabaseTestView

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
]