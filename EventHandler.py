from SpiderEventListener import SpiderEventListener
class EventHandler(SpiderEventListener):

    def __init__(self):
        pass

    def on_page_visited(self, driver):
        print "HERE! " , driver.current_url
        pass

