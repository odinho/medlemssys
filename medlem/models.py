# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import date, datetime
import mod10

# Create your models her

class Val(models.Model):
    tittel = models.CharField(_("kort forklaring"), max_length=100, unique=True)
    forklaring = models.TextField(_("lang forklaring"), blank=True)

    class Meta:
        verbose_name_plural = "val"

    def __unicode__(self):
        return self.tittel

class Lokallag(models.Model):
    namn = models.CharField(_("namn"), max_length=256, unique=True)

    class Meta:
        verbose_name_plural = "lokallag"

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
    start = models.DateField(_("start"), default=date.today)
    stopp = models.DateField(_("stopp"))

    class Meta:
        verbose_name_plural = "tilskipingar"

    def __unicode__(self):
        return u"%s (%s)" % (self.namn, self.start.strftime("%Y"))


class AktivManager(models.Manager):
    def get_query_set(self):
        return super(AktivManager, self).get_query_set().filter(    \
            utmeldt_dato__isnull=True).filter(                      \
            lokallagsmedlemskap__stopp__isnull=True)

class Medlem(models.Model):
    fornamn = models.CharField(_("fornamn"), max_length=256)
    etternamn = models.CharField(_("etternamn"), max_length=256)
    fodt = models.IntegerField(_(u"født"), max_length=4, default=date.today().year - 17)

    # Kontakt
    postadr = models.CharField(_("postadresse"), max_length=256)
    postnr = models.IntegerField(_("postnr"))
    mobnr = models.CharField(_("mobiltelefon"), max_length=50)
    heimenr = models.CharField(_("heimetelefon"), max_length=50,
                               blank=True, default="")
    epost = models.CharField(_("epost") ,max_length=256, unique=True)

    # Medlemsskapet
    innmeldt_dato = models.DateField(_("innmeldt"), default=date.today)
    utmeldt_dato = models.DateField(_("utmeldt"), blank=True, null=True)

    # Tilkopla felt
    lokallag = models.ManyToManyField(Lokallag, through='Lokallagsmedlemskap')
    val = models.ManyToManyField(Val, blank=True, null=True)
    nemnd = models.ManyToManyField(Nemnd, blank=True, null=True)
    tilskiping = models.ManyToManyField(Tilskiping, blank=True, null=True)
    lokallagsrolle = models.ManyToManyField(Lokallag,
        through='Rolle', related_name="rollemedlem", blank=True, null=True)

    # Denormaliserte felt
    lokallag_denorm = models.ForeignKey(Lokallag,
        related_name="aktive_medlem", verbose_name="aktivt lokallag",
        null=True, editable=False,)

    aktiv = AktivManager()
    objects = models.Manager()

    class Meta:
        verbose_name_plural = "medlem"
        ordering = ['-id']

    def __unicode__(self):
        return "%s %s" % (self.fornamn, self.etternamn)
    __unicode__.admin_order_field = 'etternamn'

    def get_lokallag(self):
        return self.lokallag.get(medlemsmedlemskap__stopp__isnull=True)
    get_lokallag.short_description = _("Lokallag")

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
        if (self.giro_set.filter(oppretta__gt=date(date.today().year, 1, 1),
                                 innbetalt__isnull=False)):
            return True
        else:
            return False
    har_betalt.short_description = _("Betalt")
    har_betalt.boolean = True

class Giro(models.Model):
    medlem = models.ForeignKey(Medlem)
    belop = models.PositiveIntegerField(_(u"Beløp"))
    kid = models.CharField(_("KID-nummer"), max_length=256, blank=True)
    oppretta = models.DateTimeField(_("Giro lagd"), blank=True, default=datetime.now)
    innbetalt = models.DateField(_("Dato betalt"), blank=True, null=True)
    desc = models.TextField(_("Forklaring"), max_length=256, blank=True, default="")

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
    start = models.DateField(_("Rollestart"), default=date.today)
    stopp = models.DateField(_("Rollestopp"), blank=True, null=True)

    class Meta:
        ordering = ('-start',)
        verbose_name_plural = "rolle i lokallag"

    def __unicode__(self):
        if self.stopp:
            aktiv = "Inaktiv"
        else:
            aktiv = "Aktiv"

        return u"%s, %s, %s (%s)" % (self.medlem, self.lokallag, self.rolletype, aktiv)

class Lokallagsmedlemskap(models.Model):
    medlem = models.ForeignKey(Medlem, related_name="lokallagsmedlemskap")
    lokallag = models.ForeignKey(Lokallag, related_name="medlemsmedlemskap")
    start = models.DateField(_("start av medlemskap"), default=date.today)
    stopp = models.DateField(_("medlemskap slutt"), blank=True, null=True)

    class Meta:
        ordering = ('-start',)
        verbose_name_plural = "medlemskap i lokallag"

    def __unicode__(self):
        if self.stopp:
            aktiv = "Inaktiv"
        else:
            aktiv = "Aktiv"

        return u"%s, %s (%s)" % (self.medlem, self.lokallag, aktiv)

    def save(self, *args, **kwargs):
        print self.stopp, self.lokallag, self.medlem
        if not self.stopp:
            self.medlem.lokallag_denorm = self.lokallag
            self.medlem.save()
        super(Lokallagsmedlemskap, self).save(*args, **kwargs)

