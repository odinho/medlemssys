# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai
from django.db import models
from django.utils.timezone import now
from django.db.models.query import QuerySet, Q
from model_utils.managers import PassThroughManager

from medlem.models import Medlem, Giro

class MembershipType(models.Model):
    name = models.CharField(max_length=200)
    default_price = models.IntegerField()

    def num_memberships(self):
        return self.membership_set.count()

    def __unicode__(self):
        return self.name

class MembershipQuerySet(QuerySet):
    def current(self, datetime=None):
        datetime = datetime or now()
        return self.filter(
            Q(start__lt=datetime),
            Q(end__isnull=True) | Q(end__gt=datetime))

    def missing_giros(self, year=None):
        year = year or now().year
        return self.filter(
            Q(giros__isnull=True) | ~Q(giros__gjeldande_aar=year))

class Membership(models.Model):
    member = models.ForeignKey(Medlem, related_name='memberships')
    type = models.ForeignKey(MembershipType)

    start = models.DateTimeField(blank=True, default=now)
    end = models.DateTimeField(blank=True, null=True)

    objects = PassThroughManager.for_queryset_class(MembershipQuerySet)()

    class Meta:
        ordering = ('-start', 'end', 'pk')

    def __unicode__(self):
        end = '-{}'.format(self.end.year) if self.end else ''
        return '{s.member} {s.type} ({s.start.year}{end})'.format(s=self, end=end)

    def price(self):
        return self.type.default_price

    def create_giro(self, year=None):
        year = year or now().year
        g = Giro(
            medlem=self.member,
            belop=self.price(),
            innbetalt_belop=0,
            gjeldande_aar=year
        )
        g.save()
        self.giros.add(g)
        return g
