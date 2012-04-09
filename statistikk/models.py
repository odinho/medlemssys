# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.db import models
from django.utils.translation import ugettext_lazy as _

from medlem.models import Lokallag

class LokallagStat(models.Model):
    lokallag = models.ForeignKey(Lokallag)
    veke = models.CharField(_("År-veke"), max_length=7)

    n_teljande = models.IntegerField(_("tal på teljande"))
    n_interessante = models.IntegerField(_("tal på interessante"))
    n_ikkje_utmelde = models.IntegerField(_("tal på ikkje utmelde"))
    n_totalt = models.IntegerField(_("tal på medlemar registrert"))

    teljande = models.TextField(_("liste over teljande"))
    interessante = models.TextField(_("liste over interessante"))

    oppretta = models.DateTimeField(_("oppretta"), auto_now_add=True)

    class Meta:
        unique_together = ('lokallag', 'veke')
