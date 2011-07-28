# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from datetime import date, datetime
from django.db import models
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
#from emencia.django.newsletter.mailer import mailing_started

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
    fylkeslag = models.CharField(_("fylkeslag"), max_length=255)
    distrikt = models.CharField(_("distrikt"), max_length=255)
    andsvar = models.CharField(_("andsvar"), max_length=255)

    class Meta:
        verbose_name_plural = "lokallag"

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

    def __unicode__(self):
        return u"%s (%s)" % (self.namn, self.start.strftime("%Y"))

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
    ("L", "Lagsskiping"),
    ("D", "Direkteverva"),
    ("A", "Anna"),
)

class Medlem(models.Model):
    fornamn = models.CharField(_("fornamn"), max_length=255)
    mellomnamn = models.CharField(_("mellomnamn"), max_length=255,
            blank=True, null=True)
    etternamn = models.CharField(_("etternamn"), max_length=255)
    fodt = models.IntegerField(_(u"født"), max_length=4,
            default=date.today().year - 17, blank=True, null=True)

    # Kontakt
    postnr = models.IntegerField(_("postnr"), default=5000)
    epost = models.CharField(_("epost") ,max_length=255,
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

    # Medlemsskapet
    innmeldt_dato = models.DateField(_("innmeldt"), default=date.today)
    utmeldt_dato = models.DateField(_("utmeldt"), blank=True, null=True,
            default=None)
    status = models.CharField(_("medlstatus"), max_length=1,
            choices=STATUSAR, default="M")
    innmeldingstype = models.CharField(_("innmtype"), max_length=1,
            choices=INNMELDINGSTYPAR, blank=True, null=True)
    innmeldingsdetalj = models.CharField(_("detalj om innmelding"), max_length=255,
        blank=True, null=True, help_text=_("Skriv inn vervemedlem i hakeparantes ([1234])"))

    # Tilkopla felt
    lokallag = models.ForeignKey(Lokallag, blank=True, null=True)
    val = models.ManyToManyField(Val, blank=True, null=True)
    nemnd = models.ManyToManyField(Nemnd, blank=True, null=True)
    tilskiping = models.ManyToManyField(Tilskiping, blank=True, null=True)
    lokallagsrolle = models.ManyToManyField(Lokallag,
        through='Rolle', related_name="rollemedlem", blank=True, null=True)

    class Meta:
        verbose_name_plural = "medlem"
        ordering = ['-id']

    def __unicode__(self):
        return " ".join([self.fornamn, self.mellomnamn, self.etternamn])
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
        return self.fodt < (date.today().year - 20)
    er_teljande.short_description = _("Gamal")
    er_teljande.boolean = True

    def fodt_farga(self):
        if not self.er_teljande():
            return "<span class='ikkje-teljande'>%s</span>" % self.fodt
        elif self.er_gamal():
            return "<span class='er-gamal'>%s</span>" % self.fodt
        return self.fodt
    fodt_farga.short_description = _(u"Født")
    fodt_farga.allow_tags = True
    fodt_farga.admin_order_field = 'fodt'

    def har_betalt(self):
        if (self.giro_set.filter(oppretta__gte=date(date.today().year, 1, 1),
                                 innbetalt__isnull=False)):
            return True
        else:
            return False
    har_betalt.short_description = _("Betalt")
    har_betalt.boolean = True

    def set_val(self, tittel, add=True):
        if add:
            self.val.add(Val.objects.get_or_create(tittel=tittel)[0])
        else:
            self.val.remove(Val.objects.get(tittel=tittel))

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
)
HENSIKTER = (
    ('P', "Medlemspengar"),
    ('G', "Gåve"),
    ('T', "Tilskiping"),
    ('A', "Anna"),
)

class Giro(models.Model):
    medlem = models.ForeignKey(Medlem)
    belop = models.PositiveIntegerField(_(u"Beløp"))
    kid = models.CharField(_("KID-nummer"), max_length=255, blank=True)
    oppretta = models.DateTimeField(_("Giro lagd"), blank=True, default=datetime.now)
    innbetalt = models.DateField(_("Dato betalt"), blank=True, null=True)
    konto = models.CharField(_("Konto"), max_length=1, choices=KONTI, default="M")
    hensikt = models.CharField(_("Hensikt"), max_length=1, choices=HENSIKTER,
            default="P")
    desc = models.TextField(_("Forklaring"), blank=True, default="")

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
        if len(self.kid) < 10:
            self.kid = str(self.medlem_id).zfill(5)
            pk = super(Giro, self).save(*args, **kwargs)
            self.kid = mod10.add_kid_controlbit(self.kid + str(self.pk).zfill(5))
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
        return u"%s, %s, %s (%s)" % (self.medlem, self.lokallag, self.rolletype)

