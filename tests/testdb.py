#!/usr/bin/env python3

from logdb import LoggedDB
from sys import argv
from time import sleep

if __name__ == '__main__':

    db = LoggedDB('testdb')

    if argv[1] == 'reader':
        while True:
            print(db.get_pattern('foo', 0))
            sleep(2.0)

    elif argv[1] == 'writer':
        db.set_pattern('foo', 0, argv[2])

    elif argv[1] == 'dump':
        for (e, s) in db.log.read(0):
            print('{}\t{}'.format(e, s))
