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
    def __init__(self, driver, domain):
        self.domain = urlparse(domain).netloc
        self.external = []
        self.driver = driver

    def on_page_visited(self, d):
        
        page = self.driver.current_url
        
        audios = self.driver.find_elements_by_tag_name("audio")
        self._extract_src(audios, "src")
        
        imgs = self.driver.find_elements_by_tag_name("img")
        self._extract_src(imgs, "src")

        scripts = self.driver.find_elements_by_tag_name("script")
        self._extract_src(scripts, "src")

        links = self.driver.find_elements_by_tag_name("link")
        self._extract_src(links, "href")
        
        embeds = self.driver.find_elements_by_tag_name("embed")
        self._extract_src(embeds, "src")

        iframes = self.driver.find_elements_by_tag_name("iframe")
        self._extract_src(embeds, "src")

        objects = self.driver.find_elements_by_tag_name("objects")
        self._extract_src(embeds, "data")
        
        sources = self.driver.find_elements_by_tag_name("source")
        self._extract_src(embeds, "src")


    def _extract_src(self, els, attr):
        for el in els:
            src = el.get_attribute(attr)
            if src:
                page = self.driver.current_url 
                parse = urlparse(src)
                netloc = parse.netloc
                scheme = parse.scheme

                if scheme == 'http':
                    logger.debug("FOUND MIXED CONTENT page=" + page + " tag=" + el.tag_name + " src=" + src)
                
                #logger.debug("src " + src + " netloc " + netloc)
                if not(netloc in self.external):
                    self.external.append(netloc)
                    logger.debug("page=" + page + " tag=" + el.tag_name + " location=" + netloc + " src=" + src)


class MixedContent(SpiderEventListener):


    def __init__(self, driver, domain):
        self.domain = urlparse(domain).netloc
        self.external = []
        self.driver = driver

    def on_page_visited(self, d):
        pass
