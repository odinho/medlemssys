#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 expandtab ai

import sys, random

def check_number(digits):
    _sum = 0
    alt = False
    for d in reversed(str(digits)):
        d = int(d)
        assert 0 <= d <= 9
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        _sum += d
        alt = not alt
    return (_sum % 10) == 0

def add_kid_controlbit(kid):
    _sum = 0
    alt = True
    kid_len = len(kid)
    #print kid
    for s in reversed(str(kid)):
        d = int(s)
        assert 0 <= d <= 9
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        _sum += d
        alt = not alt
        #print s, d, _sum

    controlbit = 10 - (_sum % 10)
    if controlbit == 10:
        controlbit = 0

    new_kid = str((int(kid) * 10) + controlbit)
    new_kid = new_kid.zfill(kid_len+1)
    return new_kid


if __name__ == '__main__':
    kid = str(234567)
    for i in range(10):
        nkid = add_kid_controlbit(kid)
        correct = check_number(nkid)

        print "%s\t%s\t(fra %s, nr %3d)" % (nkid, correct, kid, i)

        if (not correct):
            sys.exit()

        kid = str(random.randrange(100000000, 999999999))
