# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
import random
from datetime import date, datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms import ModelForm
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
#from emencia.django.newsletter.mailer import mailing_started

import mod10


def generate_password(length=7):
    return ''.join(random.choice('abcdefghjkmnpqrstuvwxyz23456789') for x in range(length))

class Val(models.Model):
    tittel = models.CharField(_("kort forklaring"), max_length=100, unique=True)
    forklaring = models.TextField(_("lang forklaring"), blank=True)

    @property
    def namn(self):
        return self.tittel

    class Meta:
        verbose_name_plural = "val"

    def __unicode__(self):
        return self.tittel

class Lokallag(models.Model):
    namn = models.CharField(_("namn"), max_length=255, unique=True)
    slug = models.SlugField(_("nettnamn"), max_length=255, unique=True, blank=True)
    fylkeslag = models.CharField(_("fylkeslag"), max_length=255, blank=True)
    distrikt = models.CharField(_("distrikt"), max_length=255, blank=True)
    andsvar = models.CharField(_("andsvar"), max_length=255, blank=True)
    lokalsats = models.IntegerField(_("lokalsats"), default=0)

    aktivt = models.BooleanField(_("aktivt"), default=True)
    epost = models.EmailField(_("epost"), blank=True,
        help_text=_(u"""Eiga epostliste til styret. Tek prioritet
        over å senda enkeltvis til dei som er registrert som styre."""))

    class Meta:
        verbose_name_plural = "lokallag"
        ordering = ['-aktivt', 'namn']

    def num_medlem(self):
        return self.medlem_set.betalande().count()
    num_medlem.short_description = "medlemstal"

    def listing(self):
        return reverse('lokallag_home', args=(self.slug,))

    def styreepostar(self):
        if self.epost:
            return [self.epost]
        return self.rollemedlem.exclude(epost='').values_list('epost', flat=True)

    def styret(self):
        return self.rolle_set.all()

    def styret_admin(self):
        styret = [u"{} ({})".format(x.medlem.admin_change(), x.rolletype) for x in self.styret()]
        return u', '.join(styret)
    styret_admin.short_description = _("Styret")
    styret_admin.allow_tags = True

    def save(self, *args, **kwargs):
        if not self.slug or self.slug == "":
            self.slug = slugify(self.namn)
        super(Lokallag, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.listing()

    def __unicode__(self):
        return self.namn

class Innmeldingstype(models.Model):
    namn = models.CharField(_("namn"), max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "innmeldingstypar"

    def __unicode__(self):
        return self.namn


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

class MedlemQuerySet(QuerySet):
    def alle(self):
        """Alle oppføringar i registeret"""
        if getattr(self, 'core_filters', None):
            return self.filter(**self.core_filters)

        return self

    def ikkje_utmelde(self, year=date.today().year):
        """Medlem som ikkje er eksplisitt utmelde"""
        return self.alle().filter(
            Q(utmeldt_dato__isnull=True) | Q(utmeldt_dato__gte=date(year+1, 1, 1))
        )

    def utmelde(self, year=date.today().year):
        """Medlem som er utmelde"""
        return self.alle().filter(
            utmeldt_dato__isnull=False, utmeldt_dato__lt=date(year+1, 1, 1)
        )

    def betalande(self, year=date.today().year):
        """Medlem med ein medlemspengeinnbetaling inneverande år"""
        return self.ikkje_utmelde(year) \
            .filter(
                giroar__gjeldande_aar=year,
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
            .exclude(giroar__gjeldande_aar=year,
                giroar__innbetalt__isnull=False)

    def teljande(self, year=date.today().year):
        """Medlem i teljande alder, med postnr i Noreg og med betalte medlemspengar"""
        return self.betalande(year) & self.unge(year).distinct().filter(postnr__gt="0000", postnr__lt="9999")

    def interessante(self, year=date.today().year):
        """Medlem som har betalt i år eller i fjor."""
        return self.ikkje_utmelde(year) \
            .filter(
                Q(innmeldt_dato__year=year) |
                Q(giroar__gjeldande_aar=year,
                  giroar__innbetalt__isnull=False) |
                Q(giroar__gjeldande_aar=year-1,
                  giroar__innbetalt__isnull=False)
            ).distinct()


class MedlemManager(models.Manager):
    def get_query_set(self):
        return MedlemQuerySet(self.model)

    def __getattr__(self, attr, *args):
        if attr.startswith("_"):
            raise AttributeError
        return getattr(self.get_query_set(), attr, *args)


class Medlem(models.Model):
    fornamn = models.CharField(_("fornamn"), max_length=255)
    mellomnamn = models.CharField(_("mellomnamn"), max_length=255,
            blank=True)
    etternamn = models.CharField(_("etternamn"), max_length=255)
    fodt = models.IntegerField(_(u"født"), max_length=4,
            blank=True, null=True)
    # Hadde denne før, men importering gjorde folk so gamle då: default=date.today().year - 17,

    # Kontakt
    postnr = models.CharField(
        _("postnr"), max_length=4,
        help_text="'0000' viss norsk adresse manglar")
    epost = models.CharField(_("epost"), max_length=255,
            blank=True)
    postadr = models.CharField(
        _("postadresse"), max_length=255, blank=True, null=True,
        help_text="Skriv utanlands-/skuleadresse i borte-addresse")
    ekstraadr = models.CharField(_("ekstraadresse"), max_length=255,
            blank=True)
    mobnr = models.CharField(_("mobiltelefon"), max_length=50,
            blank=True)
    heimenr = models.CharField(_("heimetelefon"), max_length=50,
            blank=True)

    bortepostnr = models.CharField(
            _("borte-postnr"), max_length=255, blank=True, null=True,
            help_text="T.d. '0864' eller 'c/o John Smith, 50012 OX-5, Oxford England'")
    borteadr = models.CharField(
            _("borte-adresse"), max_length=255, blank=True, null=True,
            help_text="Dersom borte-adressene er sett, vert post sendt her. For t.d. hybel- og utenlandsadresser.")

    # Om medlemen
    gjer = models.CharField(_("gjer"), max_length=255,
        blank=True)
    kjon = models.CharField(_("kjønn"), max_length=1, choices=(("M", "Mann"),
        ("K", "Kvinne"), ("U", "Udefinert")), default="U")
    merknad = models.TextField(_("merknad"), blank=True, default="")

    # Spesialfelt, denormalisert felt frå Giro
    _siste_medlemspengar = models.PositiveIntegerField(blank=True, null=True,
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
        blank=True, help_text=_("Skriv inn vervemedlem i hakeparantesar ([1234])"))
    verva_av = models.ForeignKey('Medlem', related_name='har_verva', blank=True, null=True)
    betalt_av = models.ForeignKey('Medlem', related_name='betalar_for', blank=True, null=True)

    # Tilkopla felt
    lokallag = models.ForeignKey(Lokallag, blank=True, null=True)
    val = models.ManyToManyField(Val, blank=True, null=True)
    lokallagsrolle = models.ManyToManyField(Lokallag,
        through='Rolle', related_name="rollemedlem", blank=True, null=True)

    user = models.OneToOneField(User, verbose_name=_("innloggingsbrukar"),
                                blank=True, null=True)
    oppretta = models.DateTimeField(_("oppretta"), auto_now_add=True)
    oppdatert = models.DateTimeField(_("oppdatert"), auto_now=True)
    nykel = models.CharField(_("nykel"), max_length=255,
            blank=True, default=generate_password)

    @property
    def stad(self):
        try:
            return PostNummer.objects.get(postnr=self.postnr).poststad
        except PostNummer.DoesNotExist:
            return "?"

    @property
    def bortestad(self):
        try:
            return PostNummer.objects.get(postnr=self.bortepostnr).poststad
        except PostNummer.DoesNotExist:
            return "?"

    # Managers
    objects = MedlemManager()

    class Meta:
        verbose_name_plural = "medlem"
        ordering = ['-id']

    def __unicode__(self):
        return " ".join([ x for x in [self.fornamn, self.mellomnamn, self.etternamn] if x ])
    __unicode__.admin_order_field = 'etternamn'

    def get_absolute_url(self):
        return reverse('medlem_edit', args=(self.pk, self.nykel))

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
    fodt_farga.admin_order_field = 'fodt'
    fodt_farga.allow_tags = True

    def har_betalt(self):
        if (self.giroar.filter(gjeldande_aar=date.today().year,
                                 innbetalt__isnull=False)).exists():
            return True
        else:
            return False
    har_betalt.short_description = _("Betalt")
    har_betalt.boolean = True

    def status_html(self):
        return "<abbr title='%s'>%s</abbr>" % (self.get_status_display(), self.status)
    status_html.short_description = _("Status")
    status_html.admin_order_field = 'status'
    status_html.allow_tags = True

    def full_adresse(self, **kwargs):
        if 'namn' not in kwargs:
            kwargs['namn'] = False
        return self.full_postadresse(heimeadresse=True, **kwargs)

    def full_postadresse(self, namn=True, heimeadresse=False, as_list=False):
        adr = []
        if namn:
            adr.append(unicode(self))
        postnr, adresse, poststad, ekstra = self.postnr, self.postadr, self.stad, self.ekstraadr
        if (self.borteadr or self.bortepostnr) and not heimeadresse:
            postnr, adresse, poststad, ekstra = self.bortepostnr, self.borteadr, self.bortestad, ''
        if adresse:
            adr.append(adresse)
        if "0005" < postnr < "9995":
            if ekstra:
                adr.append(ekstra)
            adr.append(postnr + " " + poststad)
        else:
            # Jækelen er i utlandet
            if ekstra:
                adr.append(ekstra)
            if len(postnr) > 4:
                adr.append(postnr)
        if as_list:
            return adr
        return u"\n".join(adr)

    def full_betalingsadresse(self, **kwargs):
        if self.betalt_av:
            return self.betalt_av.full_betalingsadresse(**kwargs)
        return self.full_postadresse(**kwargs)

    def set_val(self, tittel, add=True):
        if add:
            self.val.add(Val.objects.get_or_create(tittel=tittel)[0])
        else:
            self.val.remove(Val.objects.get(tittel=tittel))

    def val_exists(self, tittel):
        return self.val.filter(tittel=tittel).exists()

    def lokallag_display(self):
        if not self.lokallag_id:
            return u"(ingen)"
        return unicode(self.lokallag)

    def gjeldande_giro(self, year=date.today().year):
        try:
            return self.giroar.filter(gjeldande_aar=year)[0]
        except IndexError:
            return None

    def admin_change(self):
        url = reverse('admin:medlem_medlem_change', args=(self.pk,))
        return u'<a href="{0}">{1}</a>'.format(url, self)
    admin_change.short_description = _("Medlem")
    admin_change.admin_order_field = 'medlem'
    admin_change.allow_tags = True

    def save(self, *args, **kwargs):
        if self.mobnr and ' ' in self.mobnr:
            self.mobnr = ''.join(self.mobnr.split())
        super(Medlem, self).save(*args, **kwargs)

@transaction.commit_on_success
def update_denormalized_fields():
    for date in Giro.objects.values('gjeldande_aar').distinct().order_by('gjeldande_aar'):
        Medlem.objects.filter(giroar__gjeldande_aar=date['gjeldande_aar'], giroar__innbetalt__isnull=False) \
                .update(_siste_medlemspengar=date['gjeldande_aar'])

    Medlem.objects.filter(giroar__isnull=True).update(_siste_medlemspengar=None)


class MedlemForm(ModelForm):
    class Meta:
        model = Medlem

class EndraMedlemForm(ModelForm):
    class Meta:
        model = Medlem
        fields = ('fornamn', 'mellomnamn', 'etternamn',
                  'fodt', 'postadr', 'ekstraadr', 'postnr', 'epost', 'mobnr',
                  'borteadr', 'bortepostnr')

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
    ('V', "Ventar"),
    ('1', "Epost sendt"),
    ('E', "(E) Sendingsfeil"),
    ('M', "Manuelt postlagt"),
    ('F', "Ferdig"),
    ('U', u"Utgått ubetalt"),
)

class Giro(models.Model):
    medlem = models.ForeignKey(Medlem, related_name='giroar')
    belop = models.PositiveIntegerField(_(u"Beløp"))
    innbetalt_belop = models.PositiveIntegerField(_(u"Innbetalt beløp"), default=0)

    # XXX This is not really unique, but unique per oppretta_year and oppretta_year - 1
    kid = models.CharField(_("KID-nummer"), max_length=255, blank=True, unique=True)

    oppretta = models.DateTimeField(_("oppretta"), auto_now_add=True)
    oppdatert = models.DateTimeField(_("oppatert"), auto_now=True)
    innbetalt = models.DateField(_("Dato betalt"), blank=True, null=True)
    konto = models.CharField(_("Konto"), max_length=1, choices=KONTI, default="M")
    hensikt = models.CharField(_("Hensikt"), max_length=1, choices=HENSIKTER, default="P")
    desc = models.TextField(_("Forklaring"), blank=True, default="")

    status = models.CharField(_("Status"), max_length=1, choices=GIRO_STATUSAR, default="V")
    gjeldande_aar = models.PositiveIntegerField(_(u"Gjeldande år"), default=lambda: date.today().year)

    class Meta:
        verbose_name_plural = "giroar"
        ordering = ('-oppdatert', '-innbetalt', '-pk')

    def __unicode__(self):
        betalt = "IKKJE BETALT"
        if self.betalt():
            betalt = "betalt"
        return u"%s, %s (%s)" % (self.medlem, self.gjeldande_aar, betalt)

    def betalt(self):
        if self.innbetalt and self.innbetalt_belop >= self.belop:
            return True
        return False

    def admin_change(self):
        url = reverse('admin:medlem_giro_change', args=(self.pk,))
        belop = str(self.innbetalt_belop)
        if self.belop != self.innbetalt_belop:
            belop = '{0}/{1}'.format(self.innbetalt_belop, self.belop)
        if self.betalt():
            return '<a href="{url}">{img} {belop}</a>'.format(url=url, img='<img src="/static/admin/img/icon-yes.gif" alt="Betalt">', belop=belop)
        return '<a href="{url}">{img} {belop}</a>'.format(url=url, img='<img src="/static/admin/img/icon-no.gif" alt="Ikkje betalt">', belop=belop)
    admin_change.short_description = _("Giro")
    admin_change.admin_order_field = 'giro'
    admin_change.allow_tags = True

    def save(self, *args, **kwargs):
        if not self.pk and self.betalt():
            self.status = 'F'

        if len(self.kid) < 1:
            super(Giro, self).save(*args, **kwargs)
            self.kid = str(int(self.pk) % 100000).zfill(5)
            self.kid = mod10.kid_add_controlbit(self.kid)

        # Fiks det denormaliserte feltet til medlemen, som fortel um siste
        # medlemspengebetaling.
        if self.hensikt == 'P' \
                and self.innbetalt is not None \
                and (self.medlem._siste_medlemspengar is None \
                    or self.medlem._siste_medlemspengar < self.gjeldande_aar):
            self.medlem._siste_medlemspengar = self.gjeldande_aar
            self.medlem.save()

        super(Giro, self).save(*args, **kwargs)

class Rolletype(models.Model):
    namn = models.CharField(_("rollenamn"), max_length=64)

    def __unicode__(self):
        return self.namn

    class Meta:
        verbose_name_plural = "rolle i lokallag"
        ordering = ['namn']

class Rolle(models.Model):
    medlem = models.ForeignKey(Medlem)
    lokallag = models.ForeignKey(Lokallag)
    rolletype = models.ForeignKey(Rolletype, blank=True, null=True)

    class Meta:
        verbose_name_plural = "rolle i lokallag"
        ordering = ['rolletype', 'medlem']

    def __unicode__(self):
        return u"%s, %s (%s)" % (self.medlem, self.lokallag, self.rolletype)


class LokallagOvervaking(models.Model):
    medlem = models.ForeignKey(Medlem, blank=True, null=True)
    epost = models.CharField(_("epost"), max_length=255, blank=True,
            help_text="""Vert brukt dersom medlem ikkje er satt""")
    lokallag = models.ForeignKey(Lokallag)
    deaktivert = models.DateTimeField(blank=True, null=True)
    sist_oppdatert = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "overvaking av lokallag"

    def epostar(self):
        if self.medlem:
            return [self.medlem.epost]
        elif self.epost:
            return [self.epost]
        else:
            return self.lokallag.styreepostar()

    def epostar_admin(self):
        return ', '.join(self.epostar())
    epostar_admin.short_description = "Brukt epost"


    def __unicode__(self):
        ekstra = ""
        if self.deaktivert and self.deaktivert < datetime.now():
            ekstra = " (deaktivert)"

        if self.medlem:
            return u"%s overvakar %s%s" % (self.medlem, self.lokallag, ekstra)
        elif self.epost:
            return u"%s overvakar %s%s" % (self.epost, self.lokallag, ekstra)
        else:
            return u"Overvaking %s%s" % (self.lokallag, ekstra)

class PostNummer(models.Model):
    postnr = models.CharField(max_length=6)
    poststad = models.CharField(max_length=50)
    bruksomrade = models.CharField(max_length=50)
    folketal = models.SmallIntegerField(null=True, blank=True)
    bydel = models.CharField(max_length=50)
    kommnr = models.CharField(max_length=50)
    kommune = models.CharField(max_length=50)
    fylke = models.CharField(max_length=50)
    lat = models.FloatField()
    lon = models.FloatField()
    datakvalitet = models.SmallIntegerField()
    sist_oppdatert = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "postnummer"

    def __unicode__(self):
        return u"{0} {1}".format(self.postnr, self.poststad)
