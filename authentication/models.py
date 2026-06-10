from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Marche(models.Model):
    STATUT_CHOICES = [
        ('actif',   'Actif'),
        ('bientot', 'Bientôt expiré'),
        ('expire',  'Expiré'),
    ]
    CATEGORIE_CHOICES = [
        ('Travaux',     'Travaux'),
        ('Fournitures', 'Fournitures'),
        ('Services',    'Services'),
        ('Études',      'Études'),
    ]

    id_marche   = models.CharField(max_length=20, unique=True, blank=True)
    titre       = models.CharField(max_length=200)
    detail      = models.TextField()
    categorie   = models.CharField(max_length=50, choices=CATEGORIE_CHOICES)
    budget      = models.DecimalField(max_digits=15, decimal_places=2)
    date_fin    = models.DateTimeField()
    statut      = models.CharField(max_length=20, choices=STATUT_CHOICES,
                                   default='actif')
    fichier_pdf = models.FileField(upload_to='marches/pdf/',
                                   null=True, blank=True)
    cree_par    = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, related_name='marches')
    cree_le     = models.DateTimeField(auto_now_add=True)
    modifie_le  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.id_marche} - {self.titre}"

    def save(self, *args, **kwargs):
        if not self.id_marche:
            from django.utils import timezone
            annee = timezone.now().year
            count = Marche.objects.filter(
                cree_le__year=annee).count() + 1
            self.id_marche = f"M-{annee}-{str(count).zfill(3)}"
        # Auto-mettre à jour le statut
        from django.utils import timezone
        if self.date_fin < timezone.now():
            self.statut = 'expire'
        elif (self.date_fin - timezone.now()).days <= 5:
            self.statut = 'bientot'
        else:
            self.statut = 'actif'
        super().save(*args, **kwargs)


class Soumission(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('acceptee',   'Acceptée'),
        ('rejetee',    'Rejetée'),
    ]

    marche      = models.ForeignKey(Marche, on_delete=models.CASCADE,
                                    related_name='soumissions')
    fournisseur = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='soumissions')
    montant     = models.DecimalField(max_digits=15, decimal_places=2)
    note        = models.TextField(blank=True)
    fichier_pdf = models.FileField(upload_to='soumissions/pdf/',
                                   null=True, blank=True)
    statut      = models.CharField(max_length=20, choices=STATUT_CHOICES,
                                   default='en_attente')
    soumis_le   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-soumis_le']
        unique_together = ['marche', 'fournisseur']

    def __str__(self):
        return f"Soumission {self.fournisseur.email} →gd {self.marche.id_marche}"
class Evaluation(models.Model):
    DECISION_CHOICES = [
        ('accepte', 'Accepté'),
        ('rejete',  'Rejeté'),
        ('reserve', 'Réservé'),
    ]

    soumission      = models.OneToOneField(
        Soumission, on_delete=models.CASCADE,
        related_name='evaluation'
    )
    evaluateur      = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='evaluations'
    )
    note_technique  = models.DecimalField(
        max_digits=4, decimal_places=1,
        default=0
    )
    note_financiere = models.DecimalField(
        max_digits=4, decimal_places=1,
        default=0
    )
    note_experience = models.DecimalField(
        max_digits=4, decimal_places=1,
        default=0
    )
    commentaire     = models.TextField(blank=True)
    decision        = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        default='reserve'
    )
    evalue_le       = models.DateTimeField(auto_now_add=True)
    modifie_le      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-evalue_le']

    @property
    def score_moyen(self):
        return (float(self.note_technique) +
                float(self.note_financiere) +
                float(self.note_experience)) / 3

    def __str__(self):
        return f"Eval {self.soumission} → {self.decision}"