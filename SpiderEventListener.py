class SpiderEventListener:
    def __init__(self, driver):
        self.driver = driver

    def on_page_visited(self):
        raise NotImplementedError("Need to implemented the method")
