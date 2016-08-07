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

from medlemssys.medlem.behaviours import MedlemQuerySet
from medlemssys.medlem.behaviours import MEDLEM_LOOKUPS
from medlemssys.medlem.behaviours import GIRO_LOOKUPS


class BaseBehaviour(object):
    queryset_class = MedlemQuerySet
    medlem_ui_filters = MEDLEM_LOOKUPS
    giro_ui_filters = GIRO_LOOKUPS


class Behaviour(BaseBehaviour):
    pass
