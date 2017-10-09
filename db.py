class DB:

    def __init__(self, file):
        self.file = file
        with open(file) as f:
            self.cache = defaultdict(dict)
            for (name, patterns) in json.load(f).items():
                for (n, pattern) in patterns.items():
                    self.cache[name][int(n)] = pattern

    def save(self):
        with open(self.file, "w") as f:
            json.dump(self.cache, f)

    def has_name(self, name):
        return name in self.cache

    def delete_name(self, name):
        del self.cache[name]
        self.save()

    def get_patterns(self, name):
        return self.cache[name]

    def has_pattern(self, name, n):
        return n in self.cache[name]

    def get_pattern(self, name, n):
        return self.cache[name][n]

    def delete_pattern(self, name, n):
        del self.cache[name][n]
        self.save()

    def set_pattern(self, name, n, pattern):
        self.cache[name][n] = pattern
        self.save()

    def jsonify(self):
        "Convert whole db into the JSON we send in API responses."
        return [self.jsonify_item(name, patterns)
                for name, patterns in self.cache.items()]

    def jsonify_item(self, name, patterns=None):
        "Convert one item into the JSON we send in API responses."
        ps = patterns or self.get_patterns(name)
        return {
            'name': name,
            'patterns': [{'pattern': p, 'args': n} for n, p in ps.items()]
        }
