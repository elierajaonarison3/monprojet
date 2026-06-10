# authentication/serializers.py

from rest_framework import serializers
from .models import Marche, Soumission, Evaluation


# ════════════════════════════════════════════════════════════
# MARCHÉ
# ════════════════════════════════════════════════════════════
class MarcheSerializer(serializers.ModelSerializer):
    jours_restants  = serializers.SerializerMethodField()
    cree_par_email  = serializers.SerializerMethodField()
    fichier_pdf_url = serializers.SerializerMethodField()

    class Meta:
        model  = Marche
        fields = [
            'id', 'id_marche', 'titre', 'detail',
            'categorie', 'budget', 'date_fin', 'statut',
            'fichier_pdf', 'fichier_pdf_url',
            'cree_par_email', 'cree_le', 'modifie_le',
            'jours_restants',
        ]
        read_only_fields = [
            'id_marche', 'statut', 'cree_le', 'modifie_le'
        ]

    def get_jours_restants(self, obj):
        from django.utils import timezone
        delta = obj.date_fin - timezone.now()
        return delta.days

    def get_cree_par_email(self, obj):
        return obj.cree_par.email if obj.cree_par else None

    def get_fichier_pdf_url(self, obj):
        if obj.fichier_pdf:
            request = self.context.get('request')
            return request.build_absolute_uri(
                obj.fichier_pdf.url) if request else obj.fichier_pdf.url
        return None


# ════════════════════════════════════════════════════════════
# SOUMISSION
# ════════════════════════════════════════════════════════════
class SoumissionSerializer(serializers.ModelSerializer):
    marche_titre      = serializers.SerializerMethodField()
    marche_id         = serializers.SerializerMethodField()
    fournisseur_email = serializers.SerializerMethodField()
    fichier_pdf_url   = serializers.SerializerMethodField()

    class Meta:
        model  = Soumission
        fields = [
            'id', 'marche', 'marche_titre', 'marche_id',
            'fournisseur', 'fournisseur_email',
            'montant', 'note',
            'fichier_pdf', 'fichier_pdf_url',
            'statut', 'soumis_le',
        ]
        read_only_fields = [
            'fournisseur', 'statut', 'soumis_le'
        ]

    def get_marche_titre(self, obj):
        return obj.marche.titre

    def get_marche_id(self, obj):
        return obj.marche.id_marche

    def get_fournisseur_email(self, obj):
        return obj.fournisseur.email

    def get_fichier_pdf_url(self, obj):
        if obj.fichier_pdf:
            request = self.context.get('request')
            return request.build_absolute_uri(
                obj.fichier_pdf.url) if request else obj.fichier_pdf.url
        return None


# ════════════════════════════════════════════════════════════
# ÉVALUATION
# ════════════════════════════════════════════════════════════
class EvaluationSerializer(serializers.ModelSerializer):
    score_moyen = serializers.ReadOnlyField()

    class Meta:
        model  = Evaluation
        fields = [
            'id', 'soumission',
            'note_technique', 'note_financiere',
            'note_experience', 'commentaire',
            'decision', 'score_moyen',
            'evalue_le', 'modifie_le',
        ]
        read_only_fields = [
            'evaluateur', 'evalue_le', 'modifie_le'
        ]


# ════════════════════════════════════════════════════════════
# DOSSIER ÉVALUATEUR
# ════════════════════════════════════════════════════════════
class DossierEvaluateurSerializer(serializers.ModelSerializer):
    marche_titre        = serializers.CharField(
        source='marche.titre')
    marche_id           = serializers.CharField(
        source='marche.id_marche')
    budget_marche       = serializers.DecimalField(
        source='marche.budget',
        max_digits=15, decimal_places=2)
    fournisseur_nom     = serializers.SerializerMethodField()
    fournisseur_email   = serializers.CharField(
        source='fournisseur.email')
    fournisseur_societe = serializers.SerializerMethodField()
    evaluation          = EvaluationSerializer(read_only=True)
    statut_evaluation   = serializers.SerializerMethodField()
    fichier_pdf_url     = serializers.SerializerMethodField()

    class Meta:
        model  = Soumission
        fields = [
            'id', 'marche', 'marche_titre', 'marche_id',
            'budget_marche', 'montant',
            'fournisseur', 'fournisseur_nom',
            'fournisseur_email', 'fournisseur_societe',
            'note', 'fichier_pdf', 'fichier_pdf_url',
            'statut', 'soumis_le',
            'evaluation', 'statut_evaluation',
        ]

    def get_fournisseur_nom(self, obj):
        nom = f"{obj.fournisseur.first_name} {obj.fournisseur.last_name}".strip()
        return nom or obj.fournisseur.username

    def get_fournisseur_societe(self, obj):
        return obj.fournisseur.username

    def get_statut_evaluation(self, obj):
        try:
            obj.evaluation
            return 'évalué'
        except Exception:
            return 'en_attente'

    def get_fichier_pdf_url(self, obj):
        if obj.fichier_pdf:
            request = self.context.get('request')
            return request.build_absolute_uri(
                obj.fichier_pdf.url) if request else obj.fichier_pdf.url
        return None