"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import datetime
from django.test import TestCase
from django.utils import timezone

from .models import MembershipType, Membership
from medlem.models import Medlem
from medlem.tests import lagMedlem, lagTestMedlemar

def createMemberships():
    yesterday = timezone.now() - datetime.timedelta(days=1)
    tomorrow = timezone.now() + datetime.timedelta(days=1)
    mt = MembershipType(name='test', default_price=13)
    mt.save()

    m = lagMedlem(20, name="20-membership-openended-with-history")
    m.memberships.create(type=mt, start=yesterday, end=None)
    m.memberships.create(type=mt, start=yesterday - datetime.timedelta(days=1), end=yesterday)

    m = lagMedlem(20, name="20-membership-yesterday-till-tomorrow")
    m.memberships.create(type=mt, start=yesterday, end=tomorrow)

    m = lagMedlem(20, name="20-membership-starts-tomorrow")
    m.memberships.create(type=mt, start=tomorrow)

    m = lagMedlem(20, name="20-membership-ended-yesterday")
    m.memberships.create(type=mt, start=yesterday, end=yesterday)

    m = lagMedlem(20, name="20-no-membership")

class MedlemTest(TestCase):

    def setUp(self):
        createMemberships()

    def test_valid_membership(self):
        valid = (Medlem.objects.valid_membership()
                               .values_list('fornamn', flat=True))
        self.assertListEqual([
          '20-membership-yesterday-till-tomorrow',
          '20-membership-openended-with-history',
        ], list(valid))

    def test_invalid_membership(self):
        invalid = (Medlem.objects.invalid_membership()
                                 .values_list('fornamn', flat=True))
        self.assertListEqual([
          '20-no-membership',
          '20-membership-ended-yesterday',
          '20-membership-starts-tomorrow',
        ], list(invalid))

    def test_membership_queryset_current(self):
        ms = Membership.objects.current()
        self.assertListEqual(
            [
             '20-membership-openended-with-history',
             '20-membership-yesterday-till-tomorrow',
            ],
            [unicode(m.member.fornamn) for m in ms])

class MembershipQuerysetTest(TestCase):
    def setUp(self):
        self.medlemar = lagTestMedlemar()
        mt = MembershipType(name='test', default_price=71)
        mt.save()

    def test_missing_giro_with_no_memberships(self):
        self.assertListEqual([], list(Membership.objects.missing_giros()))

    def test_missing_giro_with_one_current_membership(self):
        ms = Membership.objects.create(
                member=self.medlemar['25-betalt'],
                type_id=1)
        g = self.medlemar['25-betalt'].giroar.get()
        g.membership = ms
        g.save()

        ms = Membership.objects.create(
                member=self.medlemar['23-betaltifjor'],
                type_id=1)
        g = self.medlemar['23-betaltifjor'].giroar.get()
        g.membership = ms
        g.save()

        memberships = Membership.objects.missing_giros()
        self.assertListEqual(
            ['23-betaltifjor'],
            [m.member.fornamn for m in memberships])

        last_year = timezone.now().year - 1
        memberships = Membership.objects.missing_giros(last_year)
        self.assertListEqual(
            ['25-betalt'],
            [m.member.fornamn for m in memberships])

    def test_add_missing_giro_with_one_current_membership(self):
        from . import actions

        ms = Membership.objects.create(
                member=self.medlemar['25-betalt'],
                type_id=1)
        g = self.medlemar['25-betalt'].giroar.get()
        ms.giros = [g]

        ms = Membership.objects.create(
                member=self.medlemar['23-betaltifjor'],
                type_id=1)
        g = self.medlemar['23-betaltifjor'].giroar.get()
        ms.giros = [g]

        memberships = Membership.objects.missing_giros()
        self.assertListEqual(
            ['23-betaltifjor'],
            [m.member.fornamn for m in memberships])

        actions.add_missing_giros()

        g = self.medlemar['23-betaltifjor'].giroar.get(
                gjeldande_aar=timezone.now().year)
        self.assertEqual(71, g.belop)
        memberships = Membership.objects.missing_giros()
        self.assertListEqual(
            [],
            [m.member.fornamn for m in memberships])
