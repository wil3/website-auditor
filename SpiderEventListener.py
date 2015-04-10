class SpiderEventListener:
    def __init__(self):
        pass

    def on_page_visited(self, driver):
        raise NotImplementedError("Need to implemented the method")
