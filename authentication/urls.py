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
    
    path('auth/google/', GoogleAuthView.as_view()),
    path('auth/login/', EmailLoginView.as_view()),
    path('auth/token/refresh/', TokenRefreshView.as_view()),

    
    path('marches/', MarcheListView.as_view()),
    path('marches/<int:pk>/', MarcheDetailView.as_view()),

   
    path('soumissions/', SoumissionView.as_view()),
    path('marches/<int:marche_pk>/soumissions/', SoumissionMarcheView.as_view()),

    
    path('evaluateur/dossiers/', DossierEvaluateurView.as_view()),
    path('evaluateur/evaluer/', EvaluationView.as_view()),
    path('evaluateur/stats/', StatsEvaluateurView.as_view()),

   
    path('admin/utilisateurs/', AdminUtilisateursView.as_view()),
    path('admin/changer-email/', AdminChangerEmailView.as_view()),
    path('admin/changer-mdp/', AdminChangerMdpView.as_view()),
    path('admin/creer-compte/', AdminCreerCompteView.as_view()),
]