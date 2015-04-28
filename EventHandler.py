import logging
from sets import Set
from urlparse import urlparse
from SpiderEventListener import SpiderEventListener

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("external")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('external.log')
logger.addHandler(fh)

class EventHandler(SpiderEventListener):
    def __init__(self, driver):
        self.driver = driver
        
    def on_page_visited(self):
        logger.info('Visiting: ' + self.driver.current_url)
        
class ExternalContent(SpiderEventListener):
    '''
    Look for external calls to other domains
    '''
    def __init__(self, driver, domain):
        self.domain = urlparse(domain).netloc
        self.external = []
        self.driver = driver

    def on_page_visited(self):
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
        self._extract_src(iframes, "src")

        objects = self.driver.find_elements_by_tag_name("objects")
        self._extract_src(objects, "data")
        
        sources = self.driver.find_elements_by_tag_name("source")
        self._extract_src(sources, "src")

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
                
                if not(netloc in self.external):
                    self.external.append(netloc)
                    logger.debug("page=" + page + " tag=" + el.tag_name + " location=" + netloc + " src=" + src)

class EmbededContent(SpiderEventListener):
    def __init__(self, driver, domain):
        self.domain = urlparse(domain).netloc
        self.driver = driver
        self.embedded = Set()

    def on_page_visited(self):
        pass

class MixedContent(SpiderEventListener):
    def __init__(self, driver, domain):
        self.domain = urlparse(domain).netloc
        self.http_sites = []
        self.http_count = 0
        self.https_count = 0
        self.total_count = 0
        self.driver = driver
        self.external = Set()
        
    def on_page_visited(self):
        url = urlparse(self.driver.current_url)
        scheme = url.scheme
        if scheme == 'http':
            self.http_sites.append(self.driver.current_url)
            self.http_count += 1
        elif scheme == 'https':
            self.https_count += 1
        self.total_count += 1

        logger.info('MIXED CONTENT CHECK START.')
        logger.info('http sites: ' + str(self.http_sites))
        logger.info('http count: ' + str(self.http_count))
        logger.info('https count: ' + str(self.https_count))
        logger.info('total count: ' + str(self.total_count))

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
        self._extract_src(iframes, "src")

        objects = self.driver.find_elements_by_tag_name("objects")
        self._extract_src(objects, "data")
        
        sources = self.driver.find_elements_by_tag_name("source")
        self._extract_src(sources, "src")

        logger.info('MIXED CONTENT CHECK END.')
        
    def _extract_src(self, els, attr):
        for el in els:
            src = el.get_attribute(attr)
            if src:
                page = self.driver.current_url 
                parse = urlparse(src)
                netloc = parse.netloc
                scheme = parse.scheme

                if scheme == 'http':
                    logger.info("FOUND MIXED CONTENT: " + str(page) + " tag=" + str(el.tag_name) + " src=" + str(src))
                
                if not(netloc in self.external):
                    self.external.add(netloc)
                    