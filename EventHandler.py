import logging
from sets import Set
from collections import namedtuple
from urlparse import urlparse
from SpiderEventListener import SpiderEventListener
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("external")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('external_resources.csv')
logger.addHandler(fh)

cookie_logger = logging.getLogger("cookies")
cookie_logger.setLevel(logging.DEBUG)
cfh = logging.FileHandler('cookies.csv')
cookie_logger.addHandler(cfh)

mixed_logger = logging.getLogger("mixed")
mixed_logger.setLevel(logging.DEBUG)
mfh = logging.FileHandler('mixed.csv')
mixed_logger.addHandler(mfh)

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

               
                #Finger print all of the pages in the same domain
                # we want to look for other domains that will make this 
                # unique
                #if netloc == self.domain:
                #    short = self._get_short_path(page_path)
                #    if not(short in self.fingerprinted):
                #        self._fingerprint(is_mixed, short, netloc)
                #        self.fingerprinted.append(short)
                
                # keep track of all the possible domains used and which type
                # of references they have embedded
                if not((scheme,netloc,el.tag_name) in self.external):
                    self.external.append((scheme, netloc,el.tag_name))
                    logger.debug(el.tag_name + "," + scheme + "," + netloc + "," + src + "," + page)
    
    #def _fingerprint(self, is_mixed, page, external_domain):
    #    fp_logger.info(str(is_mixed) + "," + page + "," + external_domain)



class CookieHandler(SpiderEventListener):
    def __init__(self, driver, domain):
        self.driver = driver
        self.domain = domain
        self.cookie_names = Set()
        self.threshold = 10

    def on_page_visited(self):
        html = self.driver.page_source
        cookies = self.driver.get_cookies()
        for cookie in [(c['name'], c['value']) for c in cookies]:
            if cookie[0] not in self.cookie_names:
                self.cookie_names.add(cookie[0])
            if len(cookie[1]) > self.threshold:
                if html.find(cookie[1]) > 0:
                    cookie_logger.info('EMBEDDED COOKIE VALUE, ' + str(cookie))
        
        cookie_logger.info('COOKIE NAMES, ' + str(self.cookie_names))

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

        mixed_logger.info('http sites, ' + str(self.http_sites))
        mixed_logger.info('http count, ' + str(self.http_count))
        mixed_logger.info('https count, ' + str(self.https_count))
        mixed_logger.info('total count, ' + str(self.total_count))

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
                    mixed_logger.info("FOUND MIXED CONTENT, " + str(page) + " tag=" + str(el.tag_name) + " src=" + str(src))
                
                if not(netloc in self.external):
                    self.external.add(netloc)
                    
