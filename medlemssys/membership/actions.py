import logging
from django.utils import timezone
from django.db.models import Count

from medlem.models import Medlem
from .models import Membership

logger = logging.getLogger(__name__)

def add_missing_giros(year=None):
    """Create giros for current memberships without one for given year.
    """
    year = year or timezone.now().year

    memberships = Membership.objects.missing_giros(year)
    for ms in memberships:
        ms.create_giro(year)
    return memberships

def find_invalid_memberships():
    medlems = (Medlem.objects
        .annotate(num_memberships=Count('memberships'))
        .filter(num_memberships__gt=1))
    invalids = {'invalid_end': [], 'flipped': []}
    for m in medlems:
        last_ms = None
        for ms in m.memberships.all().order_by('start'):
            if ms.end and ms.start > ms.end:
                logging.warning(
                    "Start and end for membership seems "
                    "flipped start > end ({m.start} > {m.end})."
                    "".format(m=ms))
                invalids['flipped'].append((ms, None))
            if last_ms and (not last_ms.end or last_ms.end > ms.start):
                if not last_ms.end:
                    logging.warning(
                        "Membership {lm.id} ({lm}) missing "
                        "end, but {m.id} ({m}) is starting at {m.start}. "
                        "".format(m=ms, lm=last_ms))
                else:
                    logging.warning(
                        "Membership {lm.id} ({lm}) has end "
                        "date going past start date of next membership "
                        "{m.id} ({m})."
                        "".format(m=ms, lm=last_ms))
                invalids['invalid_end'].append((last_ms, ms))
            last_ms = ms
    return invalids

def fix_invalid_memberships():
    invalids = find_invalid_memberships()
    fixed = []
    for ms, next_ms in invalids['invalid_end']:
        ms.end = next_ms.start
        ms.save()
        fixed.append(ms)
    return fixed
