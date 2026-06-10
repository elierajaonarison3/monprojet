# authentication/urls.py
from django.urls import path
from .views import (
    GoogleAuthView, EmailLoginView,
    MarcheListView, MarcheDetailView,
    SoumissionView, SoumissionMarcheView,
    DossierEvaluateurView,
    EvaluationView,
    StatsEvaluateurView,
    AdminUtilisateursView,
    AdminChangerEmailView,
    AdminChangerMdpView,
    AdminCreerCompteView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # ─── Auth ──────────────────────────────────────────
    path('api/auth/google/',
         GoogleAuthView.as_view()),
    path('api/auth/login/',
         EmailLoginView.as_view()),
    path('api/auth/token/refresh/',
         TokenRefreshView.as_view()),
    path('api/marches/',
         MarcheListView.as_view()),
    path('api/marches/<int:pk>/',
         MarcheDetailView.as_view()),

    path('api/soumissions/',
         SoumissionView.as_view()),
    path('api/marches/<int:marche_pk>/soumissions/',
         SoumissionMarcheView.as_view()),

    path('api/evaluateur/dossiers/',
         DossierEvaluateurView.as_view()),
    path('api/evaluateur/evaluer/',
         EvaluationView.as_view()),
    path('api/evaluateur/stats/',
         StatsEvaluateurView.as_view()),
    path('api/admin/utilisateurs/',  
         AdminUtilisateursView.as_view()),
    path('api/admin/changer-email/', 
         AdminChangerEmailView.as_view()),
    path('api/admin/changer-mdp/',   
         AdminChangerMdpView.as_view()),
    path('api/admin/creer-compte/',  
         AdminCreerCompteView.as_view()),
]