class FlowCursor:
    def __init__(self, y: int = 0):
        self.y = y

    def advance(self, amount: int):
        self.y += int(amount)
        return self.y
