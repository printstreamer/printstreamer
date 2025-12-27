
class AFP_FOCA_Triplet:

    def __init__(self):
        self.length = None
        self.triplet_id = None
        self.data = None

    def parse(self, data):
        self.length = data[0]
        self.triplet_id = data[1]
        self.data = data[2:self.length]

    def __repr__(self):
        return f"<Triplet id=0x{self.triplet_id:02X} len={self.length}>"
