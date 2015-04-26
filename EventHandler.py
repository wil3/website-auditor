from SpiderEventListener import SpiderEventListener
class EventHandler(SpiderEventListener):

    def __init__(self):
        pass

    def on_page_visited(self, driver):
        print "On page visited handler " , driver.current_url
        pass

