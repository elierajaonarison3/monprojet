# authentication/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import Marche, Soumission, Evaluation
from .serializers import MarcheSerializer, SoumissionSerializer

User = get_user_model()
ROLES_AUTORISES = ['Admin', 'PRMP', 'Évaluateur']


# ════════════════════════════════════════════════════════════
# 1. AUTH — Google OAuth2 (Fournisseurs)
# ════════════════════════════════════════════════════════════
class GoogleAuthView(APIView):
    permission_classes = []

    def post(self, request):
        token = request.data.get('idToken')
        if not token:
            return Response(
                {'error': 'idToken manquant'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            email   = idinfo.get('email')
            name    = idinfo.get('name', '')
            picture = idinfo.get('picture', '')

            if not email:
                return Response(
                    {'error': 'Email non fourni'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username':   email.split('@')[0],
                    'first_name': name.split(' ')[0] if name else '',
                    'last_name':  ' '.join(name.split(' ')[1:]) if name else '',
                }
            )
            refresh = RefreshToken.for_user(user)
            return Response({
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id':      user.id,
                    'email':   user.email,
                    'name':    f'{user.first_name} {user.last_name}'.strip(),
                    'picture': picture,
                    'is_new':  created,
                    'role':    'Fournisseurs',
                }
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )


class EmailLoginView(APIView):
    permission_classes = []

    def post(self, request):
        email    = request.data.get('email')
        password = request.data.get('password')
        role     = request.data.get('role')

        if not email or not password:
            return Response(
                {'error': 'Email et mot de passe requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if role not in ROLES_AUTORISES:
            return Response(
                {'error': 'Rôle non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Identifiants incorrects'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        user = authenticate(
            request,
            username=user_obj.username,
            password=password
        )

        if user is None:
            return Response(
                {'error': 'Identifiants incorrects'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id':    user.id,
                'email': user.email,
                'name':  f'{user.first_name} {user.last_name}'.strip(),
                'role':  role,
            }
        })


class MarcheListView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        return [IsAuthenticated()]

    def get(self, request):
        marches   = Marche.objects.all()
        statut    = request.query_params.get('statut')
        categorie = request.query_params.get('categorie')
        search    = request.query_params.get('search')

        for m in marches:
            ancien = m.statut
            if m.date_fin < timezone.now():
                m.statut = 'expire'
            elif (m.date_fin - timezone.now()).days <= 5:
                m.statut = 'bientot'
            else:
                m.statut = 'actif'
            if m.statut != ancien:
                m.save(update_fields=['statut'])

        if statut and statut != 'tous':
            marches = marches.filter(statut=statut)
        if categorie and categorie != 'Tous':
            marches = marches.filter(categorie=categorie)
        if search:
            marches = marches.filter(
                Q(titre__icontains=search) |
                Q(id_marche__icontains=search) |
                Q(detail__icontains=search)
            )

        serializer = MarcheSerializer(
            marches, many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentification requise'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = MarcheSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(cree_par=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ════════════════════════════════════════════════════════════
# 4. MARCHÉS — Détail + Modification + Suppression
# ════════════════════════════════════════════════════════════
class MarcheDetailView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Marche.objects.get(pk=pk)
        except Marche.DoesNotExist:
            return None

    def get(self, request, pk):
        marche = self.get_object(pk)
        if not marche:
            return Response(
                {'error': 'Marché introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = MarcheSerializer(
            marche, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        marche = self.get_object(pk)
        if not marche:
            return Response(
                {'error': 'Marché introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = MarcheSerializer(
            marche, data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        marche = self.get_object(pk)
        if not marche:
            return Response(
                {'error': 'Marché introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        marche.delete()
        return Response(
            {'message': 'Marché supprimé'},
            status=status.HTTP_204_NO_CONTENT
        )


# ════════════════════════════════════════════════════════════
# 5. SOUMISSIONS — Fournisseurs
# ════════════════════════════════════════════════════════════
class SoumissionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        soumissions = Soumission.objects.filter(
            fournisseur=request.user
        ).select_related('marche')
        serializer = SoumissionSerializer(
            soumissions, many=True)
        return Response(serializer.data)

    def post(self, request):
        marche_id = request.data.get('marche')

        try:
            marche = Marche.objects.get(pk=marche_id)
        except Marche.DoesNotExist:
            return Response(
                {'error': 'Marché introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        if marche.statut == 'expire':
            return Response(
                {'error': 'Ce marché est clôturé'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Soumission.objects.filter(
            marche=marche,
            fournisseur=request.user
        ).exists():
            return Response(
                {'error': 'Vous avez déjà soumis une offre'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SoumissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(fournisseur=request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ════════════════════════════════════════════════════════════
# 6. SOUMISSIONS — PRMP voit toutes les soumissions
# ════════════════════════════════════════════════════════════
class SoumissionMarcheView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, marche_pk):
        try:
            marche = Marche.objects.get(pk=marche_pk)
        except Marche.DoesNotExist:
            return Response(
                {'error': 'Marché introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        soumissions = Soumission.objects.filter(
            marche=marche
        ).select_related('fournisseur')
        serializer = SoumissionSerializer(
            soumissions, many=True)
        return Response({
            'marche':      marche.titre,
            'id_marche':   marche.id_marche,
            'total':       soumissions.count(),
            'soumissions': serializer.data,
        })

    def put(self, request, marche_pk):
        soumission_id  = request.data.get('soumission_id')
        nouveau_statut = request.data.get('statut')

        if nouveau_statut not in ['acceptee', 'rejetee']:
            return Response(
                {'error': 'Statut invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            soumission = Soumission.objects.get(
                pk=soumission_id, marche__pk=marche_pk)
        except Soumission.DoesNotExist:
            return Response(
                {'error': 'Soumission introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        soumission.statut = nouveau_statut
        soumission.save()
        return Response({
            'message': f'Soumission {nouveau_statut}',
            'statut':  soumission.statut,
        })


# ════════════════════════════════════════════════════════════
# 7. ÉVALUATEUR — Voir tous les dossiers
# ════════════════════════════════════════════════════════════
class DossierEvaluateurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        statut = request.query_params.get('statut')

        soumissions = Soumission.objects.all()\
            .select_related('marche', 'fournisseur')\
            .prefetch_related('evaluation')\
            .order_by('-soumis_le')

        print(f"=== Total soumissions: {soumissions.count()} ===")

        resultats = []
        for s in soumissions:
            try:
                eval_obj     = s.evaluation
                a_evaluation = True
            except Exception:
                eval_obj     = None
                a_evaluation = False

            statut_eval = 'évalué' if a_evaluation else 'en_attente'

            if statut and statut != 'tous':
                if statut == 'en_attente' and a_evaluation:
                    continue
                if statut == 'évalué' and not a_evaluation:
                    continue

            fournisseur = s.fournisseur
            nom = f"{fournisseur.first_name} {fournisseur.last_name}".strip()
            if not nom:
                nom = fournisseur.username

            fichier_pdf_url = None
            if s.fichier_pdf:
                try:
                    fichier_pdf_url = request.build_absolute_uri(
                        s.fichier_pdf.url)
                except Exception:
                    pass

            eval_data = None
            if a_evaluation:
                eval_data = {
                    'id':              eval_obj.id,
                    'note_technique':  float(eval_obj.note_technique),
                    'note_financiere': float(eval_obj.note_financiere),
                    'note_experience': float(eval_obj.note_experience),
                    'score_moyen':     eval_obj.score_moyen,
                    'commentaire':     eval_obj.commentaire,
                    'decision':        eval_obj.decision,
                    'evalue_le':       eval_obj.evalue_le.isoformat(),
                }

            resultats.append({
                'id':                  s.id,
                'marche':              s.marche.id,
                'marche_titre':        s.marche.titre,
                'marche_id':           s.marche.id_marche,
                'budget_marche':       float(s.marche.budget),
                'montant':             float(s.montant),
                'fournisseur':         fournisseur.id,
                'fournisseur_nom':     nom,
                'fournisseur_email':   fournisseur.email,
                'fournisseur_societe': fournisseur.username,
                'note':                s.note,
                'fichier_pdf':         str(s.fichier_pdf) if s.fichier_pdf else None,
                'fichier_pdf_url':     fichier_pdf_url,
                'statut':              s.statut,
                'statut_evaluation':   statut_eval,
                'soumis_le':           s.soumis_le.isoformat(),
                'evaluation':          eval_data,
            })

        print(f"=== Résultats envoyés: {len(resultats)} ===")
        return Response(resultats)


# ════════════════════════════════════════════════════════════
# 8. ÉVALUATEUR — Créer ou modifier une évaluation
# ════════════════════════════════════════════════════════════
class EvaluationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        soumission_id   = request.data.get('soumission')
        note_technique  = request.data.get('note_technique')
        note_financiere = request.data.get('note_financiere')
        note_experience = request.data.get('note_experience')
        commentaire     = request.data.get('commentaire', '')
        decision        = request.data.get('decision', 'reserve')

        if not soumission_id:
            return Response(
                {'error': 'soumission est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            soumission = Soumission.objects.get(pk=soumission_id)
        except Soumission.DoesNotExist:
            return Response(
                {'error': 'Soumission introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        for note in [note_technique, note_financiere, note_experience]:
            if note is None:
                return Response(
                    {'error': 'Toutes les notes sont requises'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                val = float(note)
                if not (0 <= val <= 20):
                    return Response(
                        {'error': 'Notes entre 0 et 20'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Notes invalides'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if decision not in ['accepte', 'rejete', 'reserve']:
            return Response(
                {'error': 'Décision invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

        evaluation, created = Evaluation.objects.update_or_create(
            soumission=soumission,
            defaults={
                'evaluateur':      request.user,
                'note_technique':  note_technique,
                'note_financiere': note_financiere,
                'note_experience': note_experience,
                'commentaire':     commentaire,
                'decision':        decision,
            }
        )

        soumission.statut = 'acceptee' if decision == 'accepte' \
            else 'rejetee' if decision == 'rejete' \
            else 'en_attente'
        soumission.save()

        return Response({
            'message':    'Évaluation enregistrée',
            'created':    created,
            'evaluation': {
                'id':              evaluation.id,
                'note_technique':  float(evaluation.note_technique),
                'note_financiere': float(evaluation.note_financiere),
                'note_experience': float(evaluation.note_experience),
                'score_moyen':     evaluation.score_moyen,
                'commentaire':     evaluation.commentaire,
                'decision':        evaluation.decision,
            }
        }, status=status.HTTP_201_CREATED if created
           else status.HTTP_200_OK)


# ════════════════════════════════════════════════════════════
# 9. ÉVALUATEUR — Statistiques
# ════════════════════════════════════════════════════════════
class StatsEvaluateurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total    = Soumission.objects.count()
        evalues  = 0
        acceptes = 0
        rejetes  = 0
        reserves = 0

        for s in Soumission.objects.all():
            try:
                eval_obj = s.evaluation
                evalues += 1
                if eval_obj.decision == 'accepte':
                    acceptes += 1
                elif eval_obj.decision == 'rejete':
                    rejetes += 1
                elif eval_obj.decision == 'reserve':
                    reserves += 1
            except Exception:
                pass

        en_attente = total - evalues

        print(f"=== Stats: total={total}, evalues={evalues}, attente={en_attente} ===")

        return Response({
            'total':      total,
            'evalues':    evalues,
            'en_attente': en_attente,
            'acceptes':   acceptes,
            'rejetes':    rejetes,
            'reserves':   reserves,
        })
# ════════════════════════════════════════════════════════════
# ADMIN — Endpoints
# ════════════════════════════════════════════════════════════
class AdminUtilisateursView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.all()
        data = []
        for u in users:
            data.append({
                'id':       u.id,
                'nom':      f'{u.first_name} {u.last_name}'.strip() or u.username,
                'username': u.username,
                'email':    u.email,
                'role':     'Admin' if u.is_superuser else 'Fournisseurs',
            })
        return Response(data)


class AdminChangerEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email requis'}, status=400)
        request.user.email = email
        request.user.save()
        return Response({'message': 'Email mis à jour'})


class AdminChangerMdpView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ancien  = request.data.get('ancien_mdp')
        nouveau = request.data.get('nouveau_mdp')
        if not request.user.check_password(ancien):
            return Response(
                {'error': 'Mot de passe actuel incorrect'},
                status=400)
        request.user.set_password(nouveau)
        request.user.save()
        return Response({'message': 'Mot de passe mis à jour'})


class AdminCreerCompteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        nom      = request.data.get('nom', '')
        email    = request.data.get('email')
        password = request.data.get('password')
        role     = request.data.get('role')

        if not email or not password:
            return Response(
                {'error': 'Email et mot de passe requis'},
                status=400)

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email déjà utilisé'},
                status=400)

        noms = nom.split(' ', 1)
        user = User.objects.create_user(
            username=email.split('@')[0],
            email=email,
            password=password,
            first_name=noms[0] if noms else '',
            last_name=noms[1] if len(noms) > 1 else '',
        )
        return Response({
            'message': f'Compte {role} créé',
            'id':      user.id,
            'email':   user.email,
        }, status=201)