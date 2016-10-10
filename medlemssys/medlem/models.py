# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

# Copyright 2009-2016 Odin Hørthe Omdal

# This file is part of Medlemssys.

# Medlemssys is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Medlemssys is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Medlemssys.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import random
import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.forms import ModelForm
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from medlemssys.behaviour import get_behaviour
from medlemssys.innhenting import mod10


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

    def num_medlem(self):
        return self.medlem_set.count()
    num_medlem.short_description = "medlemstal"


class Lokallag(models.Model):
    namn = models.CharField(_("namn"), max_length=255, unique=True)
    slug = models.SlugField(_("nettnamn"), max_length=255, unique=True, blank=True)
    kommunes = models.CharField(_("kommunar"), max_length=255, blank=True,
                   help_text="""Kommaseparert med stor forbokstav, t.d. "Stavanger, Sandnes".""")
    fylke = models.CharField(_("fylke"), max_length=255, blank=True,
                   help_text="""Berre eitt fylke, stor forbokstav. Overstyrer kommuner visst denne finst.""")
    andsvar = models.CharField(_("andsvar"), max_length=255, blank=True)
    lokalsats = models.IntegerField(_("lokalsats"), default=0)

    aktivt = models.BooleanField(_("aktivt"), default=True)
    epost = models.EmailField(_("epost"), blank=True,
        help_text=_("""Eiga epostliste til styret. Tek prioritet
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
        return self.rollemedlem.exclude(epost='').values_list('epost',
                                                              flat=True)

    def styret(self):
        return self.rolle_set.all()

    def styret_admin(self):
        styret = ["{} ({})".format(x.medlem.admin_change(), x.rolletype)
                  for x in self.styret()]
        return ', '.join(styret)
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


class MedlemManager(models.Manager):
    def get_queryset(self):
        return get_behaviour().queryset_class(self.model)

    def __getattr__(self, attr, *args):
        if attr.startswith("_"):
            raise AttributeError
        return getattr(self.get_queryset(), attr, *args)


class Medlem(models.Model):
    fornamn = models.CharField(_("fornamn"), max_length=255)
    mellomnamn = models.CharField(_("mellomnamn"), max_length=255,
            blank=True)
    etternamn = models.CharField(_("etternamn"), max_length=255)
    fodt = models.IntegerField(_("født"), blank=True, null=True)
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
    _siste_medlemspengar = models.PositiveIntegerField(
        blank=True, null=True, editable=False, default=None)

    # Medlemsskapet
    innmeldt_dato = models.DateField(
        _("innmeldt"), default=datetime.date.today)
    utmeldt_dato = models.DateField(
        _("utmeldt"), blank=True, null=True, default=None)
    status = models.CharField(_("medlstatus"), max_length=1,
            choices=STATUSAR, default="M")
    innmeldingstype = models.CharField(_("innmtype"), max_length=1,
            choices=INNMELDINGSTYPAR, default='U')
    innmeldingsdetalj = models.CharField(_("detalj om innmelding"), max_length=255,
        blank=True, help_text=_("Skriv inn vervemedlem i hakeparantesar ([1234])"))
    verva_av = models.ForeignKey('Medlem', related_name='har_verva', blank=True, null=True)
    betalt_av = models.ForeignKey('Medlem', related_name='betalar_for', blank=True, null=True)

    # Tilkopla felt
    lokallag = models.ForeignKey(Lokallag,
        blank=True, null=True, on_delete=models.SET_NULL)
    val = models.ManyToManyField(Val, blank=True)
    lokallagsrolle = models.ManyToManyField(Lokallag,
        through='Rolle', related_name='rollemedlem', blank=True)

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

    @property
    def bukommune(self):
        postnr = self.bortepostnr or self.postnr
        try:
            return PostNummer.objects.get(postnr=postnr).kommune
        except PostNummer.DoesNotExist:
            return "?"

    @property
    def bufylke(self):
        postnr = self.bortepostnr or self.postnr
        try:
            return PostNummer.objects.get(postnr=postnr).fylke
        except PostNummer.DoesNotExist:
            return "?"

    # Managers
    objects = MedlemManager()

    class Meta:
        verbose_name_plural = "medlem"
        ordering = ['-id']

    def __unicode__(self):
        return ' '.join(
            [ x for x in [self.fornamn,
                          self.mellomnamn,
                          self.etternamn] if x ])
    __unicode__.admin_order_field = 'etternamn'

    def get_absolute_url(self):
        return reverse('medlem_edit', args=(self.pk, self.nykel))

    def er_innmeldt(self):
        if (self.utmeldt_dato):
            return self.utmeldt_dato > datetime.date.today()
        return True
    er_innmeldt.short_description = _("Innmeld")
    er_innmeldt.boolean = True

    def er_teljande(self):
        return self.fodt > (datetime.date.today().year - 26)
    er_teljande.short_description = _("Teljande")
    er_teljande.boolean = True

    def er_gamal(self):
        return self.fodt < (datetime.date.today().year - 23)
    er_teljande.short_description = _("Gamal")
    er_teljande.boolean = True

    def alder(self):
        if not self.fodt:
            return None
        alder = datetime.date.today().year - self.fodt
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
    fodt_farga.short_description = _("Født")
    fodt_farga.admin_order_field = 'fodt'
    fodt_farga.allow_tags = True

    def har_betalt(self):
        if (self.giroar.filter(gjeldande_aar=datetime.date.today().year,
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
        return "\n".join(adr)

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
            return "(ingen)"
        return unicode(self.lokallag)

    def proposed_lokallag(self):
        """
        Lokallag that the system would choose itself if it had
        to go only on the postnr (or bortepostnr) of the member.
        """
        alder = self.alder()
        lags = set(Lokallag.objects.filter(
            models.Q(fylke=self.bufylke)
            | models.Q(kommunes__icontains=self.bukommune)))
        ordered = []
        if self.lokallag in lags:
            lags.remove(self.lokallag)
            ordered = [self.lokallag]
        last = None
        for lag in lags:
            if 'student' in lag.namn.lower():
                if alder > 18:
                    ordered.insert(0, lag)
                else:
                    last = lag
                continue
            ordered.append(lag)
        if last:
            ordered.append(last)
        return ordered

    def gjeldande_giro(self, year=datetime.date.today().year):
        try:
            return self.giroar.filter(gjeldande_aar=year)[0]
        except IndexError:
            return None

    def admin_url(self):
        return reverse('admin:medlem_medlem_change', args=(self.pk,))

    def admin_change(self):
        return '<a href="{0}">{1}</a>'.format(self.admin_url(), self)
    admin_change.short_description = _("Medlem")
    admin_change.admin_order_field = 'medlem'
    admin_change.allow_tags = True

    def save(self, *args, **kwargs):
        if self.mobnr and ' ' in self.mobnr:
            self.mobnr = ''.join(self.mobnr.split())
        super(Medlem, self).save(*args, **kwargs)


@transaction.atomic
def update_denormalized_fields():
    for date in (Giro.objects.values('gjeldande_aar')
                 .distinct().order_by('gjeldande_aar')):
        (Medlem.objects.filter(
              giroar__gjeldande_aar=date['gjeldande_aar'],
              giroar__innbetalt__isnull=False)
           .update(_siste_medlemspengar=date['gjeldande_aar']))

    (Medlem.objects.filter(giroar__isnull=True)
       .update(_siste_medlemspengar=None))
    (Giro.objects.filter(
          innbetalt__isnull=True,
          medlem__utmeldt_dato__gte=datetime.date.today())
       .delete())


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

    def save(self, commit=True, *args, **kwargs):
        m = super(InnmeldingMedlemForm, self).save(commit=False)
        m.lokallag = Lokallag.objects.get(pk=1)
        if commit:
            m.save()
        return m



KONTI = (
    ('A', "Medlemskonto (KID)"),
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
    ('U', "Utgått ubetalt"),
)


def this_year():
    return datetime.date.today().year

class Giro(models.Model):
    medlem = models.ForeignKey(Medlem, related_name='giroar')
    belop = models.PositiveIntegerField(_("Beløp"))
    innbetalt_belop = models.PositiveIntegerField(_("Innbetalt beløp"), default=0)

    # XXX This is not really unique, but unique per oppretta_year and oppretta_year - 1
    kid = models.CharField(_("KID-nummer"), max_length=255, blank=True, unique=True)

    oppretta = models.DateTimeField(_("oppretta"), auto_now_add=True)
    oppdatert = models.DateTimeField(_("oppatert"), auto_now=True)
    innbetalt = models.DateField(_("Dato betalt"), blank=True, null=True)
    konto = models.CharField(_("Konto"), max_length=1, choices=KONTI, default="M")
    hensikt = models.CharField(_("Hensikt"), max_length=1, choices=HENSIKTER, default="P")
    desc = models.TextField(_("Forklaring"), blank=True, default="")

    status = models.CharField(_("Status"), max_length=1, choices=GIRO_STATUSAR, default="V")
    gjeldande_aar = models.PositiveIntegerField(
        _("Gjeldande år"), default=this_year)

    class Meta:
        verbose_name_plural = "giroar"
        ordering = ('-oppdatert', '-innbetalt', '-pk')

    def __unicode__(self):
        betalt = "IKKJE BETALT"
        if self.betalt():
            betalt = "betalt"
        return "%s, %s (%s)" % (self.medlem, self.gjeldande_aar, betalt)

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
            return '<a href="{url}">{img} {belop}</a>'.format(
                url=url,
                img='<img src="/static/admin/img/icon-yes.svg" alt="Betalt">',
                belop=belop)
        return '<a href="{url}">{img} {belop}</a>'.format(
            url=url,
            img='<img src="/static/admin/img/icon-no.svg" alt="Ikkje betalt">',
            belop=belop)
    admin_change.short_description = _("Giro")
    admin_change.admin_order_field = 'giro'
    admin_change.allow_tags = True

    def save(self, *args, **kwargs):
        if not self.medlem.er_innmeldt() and self.innbetalt is None:
            if self.pk:
                self.delete()
            return

        if self.betalt():
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
        verbose_name_plural = "rolletyper"
        ordering = ['namn']

    def rolle_num(self):
        return self.rolle_set.count()
    rolle_num.short_description = "Folk med rolle"


class Rolle(models.Model):
    medlem = models.ForeignKey(Medlem)
    lokallag = models.ForeignKey(Lokallag, related_name='rolle_set')
    rolletype = models.ForeignKey(Rolletype, blank=True, null=True)

    class Meta:
        verbose_name_plural = "roller"
        ordering = ['rolletype', 'medlem']

    def __unicode__(self):
        return "%s, %s (%s)" % (self.medlem, self.lokallag, self.rolletype)


class LokallagOvervaking(models.Model):
    medlem = models.ForeignKey(Medlem, blank=True, null=True)
    epost = models.CharField(_("epost"), max_length=255, blank=True,
            help_text="""Vert brukt dersom medlem ikkje er satt""")
    lokallag = models.ForeignKey(
        Lokallag, related_name='lokallag_overvaking_set')
    deaktivert = models.DateTimeField(blank=True, null=True)
    sist_oppdatert = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "lokallagovervakingar"

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
        if self.deaktivert and self.deaktivert < timezone.now():
            ekstra += " (deaktivert)"
        if not len(self.epostar()):
            ekstra += " (tom)"

        if self.medlem:
            return "%s overvakar %s%s" % (self.medlem, self.lokallag, ekstra)
        elif self.epost:
            return "%s overvakar %s%s" % (self.epost, self.lokallag, ekstra)
        elif self.lokallag.styreepostar():
            return "Styret overvakar %s%s" % (self.lokallag, ekstra)
        else:
            return "Overvaking %s%s" % (self.lokallag, ekstra)

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
        return "{0} {1}".format(self.postnr, self.poststad)

    def num_medlem(self):
        return Medlem.objects.filter(postnr=self.postnr).count()
    num_medlem.short_description = "medlemstal"

    def num_teljande_medlem(self):
        return Medlem.objects.filter(postnr=self.postnr).teljande().count()
    num_teljande_medlem.short_description = "teljande"
