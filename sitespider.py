#!/usr/bin/env python

import time
from ete2 import Tree
from urlparse import urlparse
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException
from selenium.webdriver.common.proxy import *
import logging
import EventHandler
from sets import Set
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sitespider")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('out.log')
logger.addHandler(fh)

class UrlCache:
    def __init__(self, depth):
        assert(depth > 0)
        self.depth = depth
        self.visited = Set()

    def _trim_to_depth(self, url):
        tokens = urlparse(url).path.split("/")
        return urlparse(url).netloc + '/'.join([t for t in tokens[0:self.depth]])

    def has_visited(self, url):
        return self._trim_to_depth(url) in self.visited

    def cache(self, url):
        self.visited.add(self._trim_to_depth(url))

    def __str__(self):
        return '\nCACHE BEGIN.\n' + '\n'.join(self.visited) + '\nCACHE END.'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sitespider")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('out.log')
logger.addHandler(fh)
class SiteSpider:

    def __init__(self, driver, target_url, depth=-1, delay=5): 
        self.driver = driver
        self.target_url = target_url
        self.t = Tree()
        self.root = self.t.add_child(name=URL)
        self.root.add_features(path=URL, advance=True)
        self.depth = depth
        self.delay = delay
        self.subscribers = []
        self.url_cache = UrlCache(self.depth)

    def auth(self, handler):
        handler(self.driver, self.target_url)

    def _is_same_domain(self, href):
        curr = urlparse(href)
        base = urlparse(self.target_url)
        #print "%s =? %s" % (curr.netloc, base.netloc)
        return curr.netloc == base.netloc

    def _url_same(self,url1, url2):
        if self.depth < 0:
            return url1 == url2
        else:
            path1 = urlparse(url1).path.split("/")
            path2 = urlparse(url2).path.split("/")
            same = True
            for i in range(min(min(self.depth, len(path1)),len(path2))):
                if path1[i] != path2[i]:
                    same = False
                    break

            #print "Path1 %s Path2 %s Same? %s" % (path1, path2, str(same))
            return same

    def _has_visited(self, url):
        return self.url_cache.has_visited(url)

    def _has_sister(self, node, url):
        for sister in node.children:
            if self._url_same(sister.name,url):
                return True
        return False

    def _get_url_path(self, url):
        '''
        Label in tree to use
        '''
        if not self._is_same_domain(url): 
            return url 
        else: 
            parse = urlparse(url)
            return parse.path

    def _get_link_url(self, a):
        child_url = a.get_attribute("href")
        if not child_url:
            return None

        # If pound then JS must handle this link so follow it to see
        # where it goes
        if child_url.endswith("#"):
            logger.debug("Ignoring dynamic link.")
            return None
            
        return child_url
    
    def crawl(self):
        self._crawl(self.root)

    def _should_advance(self, child, child_url):
        return self._is_same_domain(child_url) and not self._has_visited(child_url)

    def _close_windows(self):
        wins = self.driver.window_handles

    def _call_subscribers(self):
        for s in self.subscribers:
            s.on_page_visited(self.driver)

    def _crawl(self, node):
        # Make request for the page
        self.url_cache.cache(node.name)

        #Hack to tell the proxy we are requesting a new page
        b64 = base64.b64encode(node.name)
        proxy_signal_url = 'http://127.0.0.1:8080/?page=' + b64
        self.driver.get(proxy_signal_url)
        self.driver.get(node.name)
       
        # There is an issue if the link is in the same domain but then
        # it does a redirect to a url outside the domain. We wont know until
        # we visit it. If this happens abort and remove from tree
        if not self._is_same_domain(self.driver.current_url):
            node.detach()
            return

        self._call_subscribers()

        time.sleep(self.delay)
        logger.info(self.driver.current_url)    
        #logger.debug( self.t.get_ascii(show_internal=True, attributes=["path"]))

        # Access by index because if we move to the 
        # next page the context of the page is lost when we come back 
        anchors = self.driver.find_elements_by_tag_name("a")
        # anchor_set = Set(anchors)
        l = len(anchors)
        for i in range(l):
            # new_anchor_set = Set(new_anchors)
            # anchor_diff = new_anchor_set - anchor_set
            # vanished_anchors = anchor_set - new_anchor_set
            # if anchor_diff:
            #     logger.debug('New Anchors: ' + '\n'.join([anchor.text for anchor in anchor_diff]))
            # if vanished_anchors:
            #     logger.debug('Vanished Anchors: ' + '\n'.join([anchor.text for anchor in anchor_diff]))
            
            new_anchors = self.driver.find_elements_by_tag_name("a")
            assert len(new_anchors) == len(anchors)
            a = new_anchors[i]
            child_url = self._get_link_url(a)
            
            #Only add if its not already there
            if not child_url or self._has_visited(child_url):
                continue
            
            child = node.add_child(name=child_url)
            child.add_feature("path", self._get_url_path(child_url))

            # Determine if the link should be advanced forward
            # We never want to start crawling other pages
            if self._should_advance(child, child_url):
                child.add_feature("advance", True)
            else:
                child.add_feature("advance", False)
        
        logger.debug(self.url_cache)

        #Process all the found links
        for child in node.children:
            if child.advance:
                self._crawl(child)

    def get_link_graph(self):
        return self.t

    def add_subscriber(self, subscriber):
        self.subscribers.append(subscriber)

def auth_handler(driver, url):
    username='bbarfoo'
    password='password'
    print url
    driver.get(url)
    login_link = driver.find_element_by_id('sign-in')
    login_link.click()

    driver.find_element_by_id('username-existing').send_keys(username)
    driver.find_element_by_id('password-existing').send_keys(password)
    driver.find_element_by_id('signin-button').click()

if __name__ == "__main__":
    URL = "https://www.etsy.com/"

    myproxy = '127.0.0.1:8080'

    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': myproxy,
        'sslProxy':myproxy,
        'noProxy':''
    })
    d = webdriver.Firefox(proxy=proxy) 
    
    service_args = [
        '--proxy=127.0.0.1:8080',
        '--ignore-ssl-errors=true',
        '--web-security=false',
        '--ssl-protocol=any',
    ]
    #d = webdriver.PhantomJS(executable_path='/home/wil/libs/node_modules/phantomjs/lib/phantom/bin/phantomjs', service_args=service_args)

    spider = SiteSpider(d, URL, depth=2, delay=5)
    #spider.auth(auth_handler)
    
    spider.add_subscriber(EventHandler.ExternalContent(d, URL,path_depth=2 ))
    spider.crawl()
    print spider.get_link_graph().get_ascii(show_internal=True, attributes=["path"])
    
    d.close()


    
