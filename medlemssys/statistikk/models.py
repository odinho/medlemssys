# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

# Copyright 2009-2014 Odin Hørthe Omdal

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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from medlemssys.medlem.models import Lokallag


class LokallagStat(models.Model):
    lokallag = models.ForeignKey(Lokallag, null=True, on_delete=models.SET_NULL)
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

    def __unicode__(self):
        return "{0} {1}".format(self.lokallag, self.veke)
