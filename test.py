
class symbol_table(object):
    def __init__(self, id, name):
        self.id = id  # global id    /   key
        self.type = type  # block func struct
        self.table = set()


