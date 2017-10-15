from collections import defaultdict
from fcntl import LOCK_EX, LOCK_SH, LOCK_UN, flock
from functools import wraps
from math import floor
from os import fsync, SEEK_SET, SEEK_END
from time import time
import json

def accessor(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        args[0]._refresh()
        return f(*args, **kwargs)
    return wrapper

def mutator(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        args[0]._log(f(*args, **kwargs))
    return wrapper

class DB:

    """\
A database implementation that sits on top of a write-ahead log and an
in-memory cache. Mutations to the database are written to the log and
all reads first replay any new log entries to make sure the cache is
up to date with any changes made by this or other processes. We also
write out the cache to disk to avoid having to replay the whole log at
startup.
    """

    def __init__(self, name):
        self.file = name + '.data'
        self.log = Log(name + '.log')
        try:
            self._load()
        except:
            self.low_water_mark = 0
            self.cache = self.empty_cache()

    def empty_cache(self):
        "Return an empty cache for a new database."
        pass

    def fill_cache(self, data):
        "Return a in-memory cache representing thet data loaded from disk."
        pass

    def cache_to_json(self):
        "Convert the cache to the form we want to serialize as JSON to disk."
        return self.cache

    def _replay(self, entry):
        "Replay a log entry to reflect it in our in-memory cache."
        pass

    def _log(self, entry):
        "Log data to our transaction log."
        self.log.write('\t'.join([str(x) for x in entry]))

    def _refresh(self):
        "Replay any new log entries against our in-memory cache."
        new_lwm = self.low_water_mark
        for (entry, lsn) in self.log.read(self.low_water_mark):
            self._replay(entry)
            new_lwm = lsn

        if self.low_water_mark < new_lwm:
            self.low_water_mark = new_lwm
            self._save()

    def _load(self):
        "Load cached data from disk so we don't have to replay the whole log."
        with open(self.file) as f:
            flock(f, LOCK_EX)
            data = json.load(f)
            self.cache = self.fill_cache(data['cache'])
            self.low_water_mark = data['low_water_mark']
            flock(f, LOCK_UN)

    def _save(self):
        # We could check that our low water mark is greater than the
        # one already on disk before we write since it's possible that
        # someone else has read farther in the log than us and gotten
        # in and written out their cache to disk. But it doesn't
        # really matter since we never actually read from the on-disk
        # cache except at startup. Rolling the cache back in time will,
        # at worst, make some processes have to replay a few more log
        # records than they might have otherwise.
        with open(self.file, 'w') as f:
            flock(f, LOCK_EX)
            json.dump({
                'cache': self.cache_to_json(),
                'low_water_mark': self.low_water_mark
            }, f, sort_keys=True, indent=2)
            flock(f, LOCK_UN)


class LinkDB (DB):

    "Database of link shortcuts."

    def empty_cache(self):
        return defaultdict(list)

    def fill_cache(self, data):
        return defaultdict(list, data)

    def _replay(self, entry):
        "Replay a log entry to reflect it in our in-memory cache."
        verb, name, n, pattern = entry.split('\t')
        if verb == 'SET':
            n = int(n)
            expand(self.cache[name], n)
            self.cache[name][n] = pattern
        elif verb == 'DELETE':
            n = int(n)
            expand(self.cache[name], n)
            self.cache[name][n] = None
            shrink(self.cache[name])
        elif verb == 'DELETE_NAME':
            del self.cache[name]
        else:
            raise Error('Bad log entry: {}'.format(entry))


    # Accessors -- must check for new entries in log.

    @accessor
    def has_name(self, name):
        return name in self.cache

    @accessor
    def get_patterns(self, name):
        return [(n, p) for n, p in enumerate(self.cache[name]) if p is not None]

    @accessor
    def has_pattern(self, name, n):
        return n < len(self.cache[name]) and self.cache[name][n] is not None

    @accessor
    def get_pattern(self, name, n):
        return self.cache[name][n]

    @accessor
    def names(self):
        return self.cache.keys()

    # Mutators -- write entries to log.

    @mutator
    def delete_name(self, name):
        return ('DELETE_NAME', name, '*', '*')

    @mutator
    def delete_pattern(self, name, n):
        return ('DELETE', name, n, self.cache[name][n])

    @mutator
    def set_pattern(self, name, n, pattern):
        return ('SET', name, n, pattern)

class NonceDB (DB):

    "Database of nonces we've seen."

    def empty_cache(self):
        return defaultdict(set)

    def fill_cache(self, data):
        return defaultdict(set, { k:set(v) for k, v in data.items() })

    def cache_to_json(self):
        return { k:list(v) for k, v in self.cache.items() }

    def timekey(self, t):
        return str(300 + ((floor(t) // 300) * 300))


    # Accessors

    @accessor
    def used(self, t, nonce):
        # Time recorded in nonce goes to a particular bucket. If the
        # bucket is the current bucket but it doesn't contain the
        # nonce, then we haven't seen it. If it's any other bucket
        # then we consider it to have been seen.

        current = self.timekey(time())
        expired = self.timekey(t) != current
        seen = expired or nonce in self.cache[current]

        if not seen: self.add_nonce(t, nonce)

        # While we're here, expire old nonces.
        for k in self.cache.keys():
            if k != current:
                self.delete_chunk(k)

        print('checking nonce: {}; t: {}; current: {}; timekey: {}; expired: {}; seen: {}'.format(
            nonce, t, current, self.timekey(t), expired, seen))
        return seen


    # Mutators

    @mutator
    def add_nonce(self, t, nonce):
        return ['ADD_NONCE', t, nonce]

    @mutator
    def delete_chunk(self, chunk):
        return ['DELETE_CHUNK', chunk]

    def _replay(self, entry):
        verb, rest = entry.split('\t', maxsplit=1)
        if verb == 'ADD_NONCE':
            time, nonce = rest.split('\t')
            self.cache[self.timekey(int(time))].add(nonce)
        elif verb == 'DELETE_CHUNK':
            del self.cache[rest]
        else:
            raise Error('Bad log entry: {}'.format(entry))


class Log:

    "Simple write-ahead log. Records each record as a line."

    def __init__(self, file):
        self.file = file

    def write(self, data):
        with open(self.file, mode='a') as f:
            flock(f, LOCK_EX)
            f.seek(0, SEEK_END)
            print(data, file=f)
            f.flush()
            fsync(f.fileno())
            flock(f, LOCK_UN)
            return f.tell()

    def read(self, low_water_mark):
        with open(self.file, mode='r') as f:
            flock(f, LOCK_SH)
            f.seek(low_water_mark, SEEK_SET)
            while True:
                line = f.readline()
                pos = f.tell()
                if line == '':
                    break
                yield line[:-1], pos
            flock(f, LOCK_UN)


#
# Utilities
#

def expand(list, size):
    list += [None] * (1 + (size - len(list)))


def shrink(list):
    while list and list[-1] is None: list.pop()
