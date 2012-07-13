# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from datetime import date, datetime
from django.db import models, transaction
from django.db.models import Q
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
#from emencia.django.newsletter.mailer import mailing_started

from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from medlemssys import mod10


class Val(models.Model):
    tittel = models.CharField(_("kort forklaring"), max_length=100, unique=True)
    forklaring = models.TextField(_("lang forklaring"), blank=True)

    class Meta:
        verbose_name_plural = "val"

    def __unicode__(self):
        return self.tittel

class Lokallag(models.Model):
    namn = models.CharField(_("namn"), max_length=255, unique=True)
    slug = models.SlugField(_("nettnamn"), max_length=255, unique=True, blank=True)
    fylkeslag = models.CharField(_("fylkeslag"), max_length=255)
    distrikt = models.CharField(_("distrikt"), max_length=255)
    andsvar = models.CharField(_("andsvar"), max_length=255)
    lokalsats = models.IntegerField(_("lokalsats"), default=0)

    aktivt = models.BooleanField(_("aktivt"), default=True)

    class Meta:
        verbose_name_plural = "lokallag"
        ordering = ['-aktivt', 'namn']

    def num_medlem(self):
        return self.medlem_set.betalande().count()
    num_medlem.short_description = "medlemstal"

    def save(self, *args, **kwargs):
        if not self.slug or self.slug == "":
            self.slug = slugify(self.namn)
        super(Lokallag, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.namn

class Innmeldingstype(models.Model):
    namn = models.CharField(_("namn"), max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "innmeldingstypar"

    def __unicode__(self):
        return self.namn

class Nemnd(models.Model):
    namn = models.CharField(_("namn"), max_length=64)
    start = models.DateField(_("start"), default=date.today)
    stopp = models.DateField(_("stopp"))

    class Meta:
        verbose_name_plural = "nemnder"

    def __unicode__(self):
        return u"%s (%s–%s)" % (self.namn, self.start.strftime("%y"),
                                self.stopp.strftime("%y"))

class Tilskiping(models.Model):
    namn = models.CharField(_("namn"), max_length=64)
    slug = models.SlugField(_("kortnamn"), max_length=64)
    start = models.DateField(_("start"), default=date.today)
    stopp = models.DateField(_("stopp"))

    class Meta:
        verbose_name_plural = "tilskipingar"

    def num_deltakarar(self):
        return self.medlem_set.count()
    num_deltakarar.short_description = _("deltakarar")

    def __unicode__(self):
        return u"%s (%s)" % (self.namn, self.start.strftime("%Y"))
    __unicode__.admin_order_field = 'namn'

STATUSAR = (
    ("M", "Vanleg medlem"),
    ("I", "Infoperson"),
    ("L", "Livstidsmedlem"),
)

INNMELDINGSTYPAR = (
    ("H", "Heimesida"),
    ("M", "Målferd"),
    ("V", "Vervekampanje"),
    ("F", "Flygeblad"),
    ("L", "Lagsskiping/årsmøte"),
    ("D", "Direkteverva"),
    ("S", "SMS"),
    ("O", "Vitjing"),
    ("A", "Anna"),
    ("U", "--"),
)

class MedlemManager(models.Manager):
    def alle(self):
        """Alle oppføringar i registeret"""
        if getattr(self, 'core_filters', None):
            qs = super(MedlemManager, self).get_query_set().filter(**self.core_filters)
        else:
            qs = super(MedlemManager, self).get_query_set()

        return qs

    def ikkje_utmelde(self, year=date.today().year):
        """Medlem som ikkje er eksplisitt utmelde"""
        return self.alle().filter(
            Q(utmeldt_dato__isnull=True) | Q(utmeldt_dato__gt=date(year+1, 1, 1))
        )

    def betalande(self, year=date.today().year):
        """Medlem med ein medlemspengeinnbetaling inneverande år"""
        return self.ikkje_utmelde(year) \
            .filter(
                giroar__oppretta__gte=date(year, 1, 1),
                giroar__oppretta__lt=date(year+1, 1, 1),
                giroar__innbetalt__isnull=False
            ).distinct()

    def unge(self, year=date.today().year):
        """Medlem under 26 (altso i teljande alder)"""
        return self.ikkje_utmelde(year) \
            .filter(
                fodt__gte = year - 25
            )

    def potensielt_teljande(self, year=date.today().year):
        return self.unge(year).filter(postnr__gt="0000", postnr__lt="9999") \
            .exclude(giroar__oppretta__gte=date(year, 1, 1),
                giroar__oppretta__lt=date(year+1, 1, 1),
                giroar__innbetalt__isnull=False)

    def teljande(self, year=date.today().year):
        """Medlem i teljande alder, med postnr i Noreg og med betalte medlemspengar"""
        return self.betalande(year) & self.unge(year).distinct().filter(postnr__gt="0000", postnr__lt="9999")

    def interessante(self, year=date.today().year):
        """Medlem som har betalt i år eller i fjor."""
        return self.ikkje_utmelde(year) \
            .filter(
                Q(innmeldt_dato__year=year) |
                Q(giroar__oppretta__gte=date(year-1, 1, 1),
                  giroar__oppretta__lt=date(year+1, 1, 1),
                  giroar__innbetalt__isnull=False)
            ).distinct()

    def get_query_set(self):
        return self.alle()


class Medlem(models.Model):
    fornamn = models.CharField(_("fornamn"), max_length=255)
    mellomnamn = models.CharField(_("mellomnamn"), max_length=255,
            blank=True, null=True)
    etternamn = models.CharField(_("etternamn"), max_length=255)
    fodt = models.IntegerField(_(u"født"), max_length=4,
            blank=True, null=True)
    # Hadde denne før, men importering gjorde folk so gamle då: default=date.today().year - 17,

    # Kontakt
    postnr = models.CharField(_("postnr"), max_length=4)
    epost = models.CharField(_("epost"), max_length=255,
            blank=True, null=True)
    postadr = models.CharField(_("postadresse"), max_length=255,
            blank=True, null=True)
    ekstraadr = models.CharField(_("ekstraadresse"), max_length=255,
            blank=True, null=True)
    mobnr = models.CharField(_("mobiltelefon"), max_length=50,
            blank=True, null=True)
    heimenr = models.CharField(_("heimetelefon"), max_length=50,
            blank=True, null=True)

    # Om medlemen
    gjer = models.CharField(_("gjer"), max_length=255,
        blank=True, null=True)
    kjon = models.CharField(_("kjønn"), max_length=1, choices=(("M", "Mann"),
        ("K", "Kvinne"), ("U", "Udefinert")), default="U")
    merknad = models.TextField(_("merknad"), blank=True, default="")

    # Spesialfelt, denormalisert felt frå Giro
    _siste_medlemspengar = models.DateField(blank=True, null=True,
            editable=False, default=None)

    # Medlemsskapet
    innmeldt_dato = models.DateField(_("innmeldt"), default=date.today)
    utmeldt_dato = models.DateField(_("utmeldt"), blank=True, null=True,
            default=None)
    status = models.CharField(_("medlstatus"), max_length=1,
            choices=STATUSAR, default="M")
    innmeldingstype = models.CharField(_("innmtype"), max_length=1,
            choices=INNMELDINGSTYPAR, default='U')
    innmeldingsdetalj = models.CharField(_("detalj om innmelding"), max_length=255,
        blank=True, null=True, help_text=_("Skriv inn vervemedlem i hakeparantesar ([1234])"))
    verva_av = models.ForeignKey('Medlem', related_name='har_verva', blank=True, null=True)

    # Tilkopla felt
    lokallag = models.ForeignKey(Lokallag, blank=True, null=True)
    val = models.ManyToManyField(Val, blank=True, null=True)
    nemnd = models.ManyToManyField(Nemnd, blank=True, null=True)
    tilskiping = models.ManyToManyField(Tilskiping, blank=True, null=True)
    lokallagsrolle = models.ManyToManyField(Lokallag,
        through='Rolle', related_name="rollemedlem", blank=True, null=True)

    user = models.OneToOneField(User, verbose_name=_("innloggingsbrukar"),
                                blank=True, null=True)
    oppretta = models.DateTimeField(_("oppretta"), auto_now_add=True)
    oppdatert = models.DateTimeField(_("oppdatert"), auto_now=True)

    # Managers
    objects = MedlemManager()

    class Meta:
        verbose_name_plural = "medlem"
        ordering = ['-id']

    def __unicode__(self):
        return " ".join([ x for x in [self.fornamn, self.mellomnamn, self.etternamn] if x ])
    __unicode__.admin_order_field = 'etternamn'

    def er_innmeldt(self):
        if (self.utmeldt_dato):
            return self.utmeldt_dato > date.today()
        return True
    er_innmeldt.short_description = _("Innmeld")
    er_innmeldt.boolean = True

    def er_teljande(self):
        return self.fodt > (date.today().year - 26)
    er_teljande.short_description = _("Teljande")
    er_teljande.boolean = True

    def er_gamal(self):
        return self.fodt < (date.today().year - 23)
    er_teljande.short_description = _("Gamal")
    er_teljande.boolean = True

    def alder(self):
        if not self.fodt:
            return None
        alder = date.today().year - self.fodt
        if alder >= 0 and alder < 120:
            return alder
        return None

    def pronomen(self):
        if self.kjon == 'M':
            return "han"
        elif self.kjon == 'K':
            return "ho"
        return "ho/han"

    def fodt_farga(self):
        if self.alder() == None:
            return "?"
        if not self.er_teljande():
            return "<span class='ikkje-teljande' title='Medlemen er ikkje " + \
               "teljande (%d år)'>%s</span>" % (self.alder(), self.fodt)
        elif self.er_gamal():
            return "<span class='er-gamal' title='Medlemen er gamal, men " + \
        "framleis teljande (%d år)'>%s</span>" % (self.alder(), self.fodt)
        return "<span title='%d år'>%d</span>" % (self.alder(), self.fodt)
    fodt_farga.short_description = _(u"Født")
    fodt_farga.allow_tags = True
    fodt_farga.admin_order_field = 'fodt'

    def har_betalt(self):
        if (self.giroar.filter(oppretta__gte=date(date.today().year, 1, 1),
                                 innbetalt__isnull=False)).exists():
            return True
        else:
            return False
    har_betalt.short_description = _("Betalt")
    har_betalt.boolean = True

    def status_html(self):
        return "<abbr title='%s'>%s</abbr>" % (self.get_status_display(), self.status)
    status_html.short_description = _("Status")
    status_html.allow_tags = True
    status_html.admin_order_field = 'status'

    def set_val(self, tittel, add=True):
        if add:
            self.val.add(Val.objects.get_or_create(tittel=tittel)[0])
        else:
            self.val.remove(Val.objects.get(tittel=tittel))

@transaction.commit_on_success
def update_denormalized_fields():
    for date in Giro.objects.values('oppretta').distinct():
        Medlem.objects.filter(giroar__innbetalt__gt=date['oppretta']) \
                .exclude(giroar__oppretta__gt=date['oppretta']) \
                .update(_siste_medlemspengar=date['oppretta'])

    Medlem.objects.filter(giroar__isnull=True).update(_siste_medlemspengar=None)


class MedlemForm(ModelForm):
    class Meta:
        model = Medlem

class InnmeldingMedlemForm(ModelForm):
    class Meta:
        model = Medlem
        fields = ('fornamn', 'etternamn', 'postnr', 'epost', 'mobnr',)

    def __init__(self, *args, **kwargs):
        super(InnmeldingMedlemForm, self).__init__(*args, **kwargs)
        #self.fields["lokallag"].initial = MyModel.objects.get(id=1)
        print "i: " + str(dir(self))

    def save(self, commit=True, *args, **kwargs):
        m = super(InnmeldingMedlemForm, self).save(commit=False)
        m.lokallag = Lokallag.objects.get(pk=1)
        if commit:
            m.save()
        return m


#def add_medlem_to_newsletters(sender, **kwargs):
#    from emencia.django.newsletter.models import Contact, MailingList
#
#    medlemar = Medlem.objects.all()
#
#    subscribers = []
#    for profile in medlemar:
#        contact, created = Contact.objects.get_or_create(email=profile.epost,
#                                                       defaults={'first_name': profile.fornamn,
#                                                                 'last_name': profile.etternamn,
#                                                                 'content_object': profile})
#        subscribers.append(contact)
#
#    new_mailing, created = MailingList.objects.get_or_create(name='Alle medlem')
#    if created:
#        new_mailing.save()
#    new_mailing.subscribers.add(*subscribers)
#    new_mailing.save()
#mailing_started.connect(add_medlem_to_newsletters)

KONTI = (
    ('M', "Medlemskonto"),
    ('K', "Kassa"),
    ('B', "Brukskonto"),
    ('S', "SMS"),
)
HENSIKTER = (
    ('P', "Medlemspengar"),
    ('G', "Gåve"),
    ('T', "Tilskiping"),
    ('A', "Anna"),
)
GIRO_STATUSAR = (
    ('V', "Ventar på sending"),
    ('1', "Fyrste sendt"),
    ('F', "Ferdig"),
)

class Giro(models.Model):
    medlem = models.ForeignKey(Medlem, related_name='giroar')
    belop = models.PositiveIntegerField(_(u"Beløp"))
    innbetalt_belop = models.PositiveIntegerField(_(u"Innbetalt beløp"), default=0)

    # XXX This is not really unique, but unique per oppretta_year and oppretta_year - 1
    kid = models.CharField(_("KID-nummer"), max_length=255, blank=True, unique=True)

    oppretta = models.DateTimeField(_("Giro lagd"), blank=True, default=datetime.now)
    oppdatert = models.DateTimeField(_("Giro oppatert"), auto_now=True)
    innbetalt = models.DateField(_("Dato betalt"), blank=True, null=True)
    konto = models.CharField(_("Konto"), max_length=1, choices=KONTI, default="M")
    hensikt = models.CharField(_("Hensikt"), max_length=1, choices=HENSIKTER, default="P")
    desc = models.TextField(_("Forklaring"), blank=True, default="")

    status = models.CharField(_("Status"), max_length=1, choices=GIRO_STATUSAR, default="V")

    class Meta:
        verbose_name_plural = "giroar"
        ordering = ('-oppretta',)

    def __unicode__(self):
        if self.innbetalt:
            betalt = "betalt"
        else:
            betalt = "IKKJE BETALT"

        return u"%s, %s (%s)" % (self.medlem, self.oppretta.year, betalt)

    def save(self, *args, **kwargs):
        if len(self.kid) < 1:
            super(Giro, self).save(*args, **kwargs)
            self.kid = str(int(self.pk) % 100000).zfill(5)
            self.kid = mod10.add_kid_controlbit(self.kid)

        # Fiks det denormaliserte feltet til medlemen, som fortel um siste
        # medlemspengebetaling.
        if self.hensikt == 'P' \
                and self.innbetalt is not None \
                and (self.medlem._siste_medlemspengar is None \
                    or self.medlem._siste_medlemspengar < self.oppretta.date()):
            self.medlem._siste_medlemspengar = self.oppretta
            self.medlem.save()

        super(Giro, self).save(*args, **kwargs)

class Rolletype(models.Model):
    namn = models.CharField(_("rollenamn"), max_length=64)

    def __unicode__(self):
        return self.namn

class Rolle(models.Model):
    medlem = models.ForeignKey(Medlem)
    lokallag = models.ForeignKey(Lokallag)
    rolletype = models.ForeignKey(Rolletype, blank=True, null=True)

    class Meta:
        verbose_name_plural = "rolle i lokallag"

    def __unicode__(self):
        return u"%s, %s (%s)" % (self.medlem, self.lokallag, self.rolletype)


class LokallagOvervaking(models.Model):
    medlem = models.ForeignKey(Medlem, blank=True, null=True)
    epost = models.CharField(_("epost"), max_length=255,
            blank=True, null=True, help_text="""Vert brukt dersom medlem ikkje er satt""")

    lokallag = models.ForeignKey(Lokallag)
    deaktivert = models.DateTimeField(blank=True, null=True)
    sist_oppdatert = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "overvaking av lokallag"

    def __unicode__(self):
        ekstra = ""
        if self.deaktivert and self.deaktivert < datetime.now():
            ekstra = " (deaktivert)"

        if self.medlem:
            return u"%s overvakar %s%s" % (self.medlem, self.lokallag, ekstra)
        else:
            return u"%s overvakar %s%s" % (self.epost, self.lokallag, ekstra)
