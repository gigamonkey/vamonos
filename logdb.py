from collections import defaultdict
from fcntl import LOCK_EX, LOCK_SH, LOCK_UN, flock
from os import fsync
from time import sleep

START   = 0
CURRENT = 1
END     = 2

class Log:

    def __init__(self, file):
        self.file = file

    def write(self, data):
        with open(self.file, mode='a') as f:
            flock(f, LOCK_EX)
            f.seek(0, END)
            print(data, file=f)
            f.flush()
            fsync(f.fileno())
            flock(f, LOCK_UN)
            return f.tell()

    def read(self, low_water_mark):
        with open(self.file, mode='r') as f:
            flock(f, LOCK_SH)
            f.seek(low_water_mark, START)
            while True:
                line = f.readline()
                pos = f.tell()
                if line == '': break
                yield (line[:-1], pos)
            flock(f, LOCK_UN)


class LoggedDB:

    def __init__(self, file, log):
        self.file = file
        self.log = log
        self.lwm = 0
        self.cache = defaultdict(dict)

    def _log(self, *entry):
        self.log.write('\t'.join([str(x) for x in entry]))

    def _replay(self, entry):
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
        for (entry, lsn) in self.log.read(self.lwm):
            print('** REPLAYING {}'.format(entry))
            self._replay(entry)
            self.lwm = lsn

    def _load(self):
        with open(self.file) as f:
            self.cache = defaultdict(dict)
            for (name, patterns) in json.load(f).items():
                for (n, pattern) in patterns.items():
                    self.cache[name][int(n)] = pattern

    def _save(self):
        with open(self.file, 'w') as f:
            json.dump({'lwm': self.lwm, 'data': self.cache}, f)

    # Public methods

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

    def delete_name(self, name):
        self._log('DELETE_NAME', name, '*', '*')

    def delete_pattern(self, name, n):
        self._log('DELETE', name, n, self.cache[name][n])

    def set_pattern(self, name, n, pattern):
        self._log('SET', name, n, pattern)


if __name__ == '__main__':


    if False:
        print('Opening log')
        log = Log('test2.log')
        lsns = [ log.write(x) for x in ['a', 'b', 'c', 'def', 'ghij', 'kl', 'mnopqst'] ]
        print(lsns)
        for (record, lsn) in log.read(lsns[2]):
            print('{}: {}'.format(lsn, record))

    from sys import argv

    db = LoggedDB("testdb.data", Log("testdb.log"))

    if argv[1] == 'reader':
        while True:
            print(db.get_pattern('foo', 0))
            sleep(2.0)
    elif argv[1] == 'writer':
        db.set_pattern('foo', 0, argv[2])
