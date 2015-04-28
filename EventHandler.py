import logging
from urlparse import urlparse
from SpiderEventListener import SpiderEventListener
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("external")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('external.log')
logger.addHandler(fh)

fp_logger = logging.getLogger("fp")
fp_fh = logging.FileHandler('fingerprints.csv')
fp_logger.addHandler(fp_fh)

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
    def __init__(self, driver, domain, path_depth=-1):
        self.domain = urlparse(domain).netloc
        self.external = []
        self.fingerprinted = []
        self.driver = driver
        self.path_depth = path_depth

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
    
    def _get_short_path(self, path):
        if self.path_depth < 0:
            return path
        paths= path.split("/")
        short_path = paths [:min(self.path_depth, len(paths))]
        return "/".join(short_path)

    def _extract_src(self, els, attr):
        page = self.driver.current_url 
        page_path = urlparse(page).path
        for el in els:
            src = el.get_attribute(attr)
            if src:
                parse = urlparse(src)
                netloc = parse.netloc
                scheme = parse.scheme

                is_mixed = False
                if scheme == 'http':
                    #logger.debug("FOUND MIXED CONTENT page=" + page + " tag=" + el.tag_name + " src=" + src)
                    is_mixed = True
               
                #Finger print all of the pages in the same domain
                # we want to look for other domains that will make this 
                # unique
                if netloc == self.domain:
                    short = self._get_short_path(page_path)
                    if not(short in self.fingerprinted):
                        self._fingerprint(is_mixed, short, netloc)
                        self.fingerprinted.append(short)
                
                #logger.debug("src " + src + " netloc " + netloc)
                # keep track of all the possible domains used
                if not(netloc in self.external):
                    self.external.append(netloc)
                    logger.debug(el.tag_name + "," + netloc + "," + src + "," + page)
    
    def _fingerprint(self, is_mixed, page, external_domain):
        fp_logger.info(str(is_mixed) + "," + page + "," + external_domain)


class MixedContent(SpiderEventListener):


    def __init__(self, driver, domain):
        self.domain = urlparse(domain).netloc
        self.external = []
        self.driver = driver

    def on_page_visited(self, d):
        pass
