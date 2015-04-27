import logging
from urlparse import urlparse
from SpiderEventListener import SpiderEventListener
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("external")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('external.log')
logger.addHandler(fh)
class EventHandler(SpiderEventListener):

    def __init__(self):
        pass

    def on_page_visited(self, driver):
        print "On page visited handler " , driver.current_url
        pass

class ExternalContent(SpiderEventListener):
    '''
    Look for external calls to other domains
    '''
    def __init__(self, domain):
        self.domain = urlparse(domain).netloc

    def on_page_visited(self, driver):
        
        page = driver.current_url
        
    def _images(self):
        imgs = driver.find_elements_by_tag_name("img")
        for img in imgs:
            src = img.get_attribute("src")
            if src:
                netloc = urlparse(src).netloc
                logger.debug("src " + src + " netloc " + netloc)
