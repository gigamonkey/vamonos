from collections import defaultdict
from fcntl import LOCK_EX, LOCK_SH, LOCK_UN, flock
from os import fsync, SEEK_SET, SEEK_END
from time import sleep
import json


class DB:

    def has_name(self, name): pass

    def delete_name(self, name): pass

    def get_patterns(self, name): pass

    def has_pattern(self, name, n): pass

    def get_pattern(self, name, n): pass

    def delete_pattern(self, name, n): pass

    def set_pattern(self, name, n, pattern): pass

    def names(self): pass

    def jsonify(self):
        "Convert whole db into the JSON we send in API responses."
        return [self.jsonify_item(name) for name in self.names()]

    def jsonify_item(self, name):
        "Convert one item into the JSON we send in API responses."
        patterns = [{'pattern': p, 'args': n}
                    for n, p in self.get_patterns(name).items()]
        return {'name': name, 'patterns': patterns}


class SimpleDB (DB):

    def __init__(self, file):
        self.file = file
        with open(file) as f:
            self.cache = defaultdict(dict)
            for (name, patterns) in json.load(f).items():
                for (n, pattern) in patterns.items():
                    self.cache[name][int(n)] = pattern

    def _save(self):
        with open(self.file, "w") as f:
            json.dump(self.cache, f)

    def has_name(self, name):
        return name in self.cache

    def delete_name(self, name):
        del self.cache[name]
        self._save()

    def get_patterns(self, name):
        return self.cache[name]

    def has_pattern(self, name, n):
        return n in self.cache[name]

    def get_pattern(self, name, n):
        return self.cache[name][n]

    def delete_pattern(self, name, n):
        del self.cache[name][n]
        self._save()

    def set_pattern(self, name, n, pattern):
        self.cache[name][n] = pattern
        self._save()

    def names(self):
        return self.cache.keys()


class LoggedDB (DB):

    def __init__(self, name):
        self.file = name + '.data'
        self.log = Log(name + '.log')
        try:
            self._load()
        except:
            self.low_water_mark = 0
            self.cache = defaultdict(dict)

    def _log(self, *entry):
        "Log data to our transaction log."
        self.log.write('\t'.join([str(x) for x in entry]))

    def _replay(self, entry):
        "Replay a log entry to reflect it in our in-memory cache."
        verb, name, n, pattern = entry.split('\t')
        n = int(n)
        if verb == 'SET':
            self.cache[name][n] = pattern
        elif verb == 'DELETE':
            del self.cache[name][n]
        elif verb == 'DELETE_NAME':
            del self.cache[name]
        else:
            raise Error('Bad log entry: {}'.format(entry))

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
            self.cache = defaultdict(dict)
            data = json.load(f)
            self.low_water_mark = data['low_water_mark']
            for (name, patterns) in data['cache'].items():
                for (n, pattern) in patterns.items():
                    self.cache[name][int(n)] = pattern
            flock(f, LOCK_UN)

    def _save(self):
        # We could check that our low water mark is greater than the
        # one already on disk before we write since it's possible that
        # someone else has read farther in the log than us and gotten
        # in and written out their cache to disk. But it doesn't
        # really matter since we never actually read from the on-disk
        # cache at startup. Rolling the cache back in time will, at
        # worst, make some processes have to reply a few more log
        # records than they might have otherwise.
        with open(self.file, 'w') as f:
            flock(f, LOCK_EX)
            json.dump({
                'low_water_mark': self.low_water_mark,
                'cache': self.cache
            }, f)
            flock(f, LOCK_UN)

    # Accessors -- must check for new entries in log.

    def has_name(self, name):
        self._refresh()
        return name in self.cache

    def get_patterns(self, name):
        self._refresh()
        return self.cache[name]

    def has_pattern(self, name, n):
        self._refresh()
        return n in self.cache[name]

    def get_pattern(self, name, n):
        self._refresh()
        return self.cache[name][n]

    def names(self):
        self._refresh()
        return self.cache.keys()

    # Mutators -- write entries to log.

    def delete_name(self, name):
        self._log('DELETE_NAME', name, '*', '*')

    def delete_pattern(self, name, n):
        self._log('DELETE', name, n, self.cache[name][n])

    def set_pattern(self, name, n, pattern):
        self._log('SET', name, n, pattern)


class Log:

    "Simple write ahead log. Records each record as a line."

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
