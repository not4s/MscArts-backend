class MockCache:
    def __init__(self):
        self.cache = dict()

    def get(self, username):
        return self.cache.get(username, [])

    def put(self, username, data):
        self.cache[username] = data

    def print_cache(self):
        for k, v in self.cache.items():
            print(k, v)


mock_cache = MockCache()
