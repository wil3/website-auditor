#!/usr/bin/env python

import time
from ete2 import Tree
from urlparse import urlparse
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException
import logging
import EventHandler

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

    def _has_visited(self, node, url):
        '''
        Look at the curent nodes ancestors and those nodes sisters/brothers
        to see if the link has ever been visited
        '''
        for ancestor in node.iter_ancestors():
            if self._url_same(ancestor.name,url):
                return True
            else:
                for sister in ancestor.get_sisters():
                    if self._url_same(sister.name,url):
                        return True
                
        return False

    def _has_sister(self, node,url):
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
            try:
                window_handle = self.driver.current_window_handle
                a.click()
                child_url = self.driver.current_url
                handles = self.driver.window_handles
                if len(handles) == 1:
                    self.driver.back()
                else:
                    for handle in self.driver.window_handles:
                        if handle != window_handle:
                            self.driver.switch_to_window(handle)
                            self.driver.close()
                    self.driver.switch_to_window(window_handle)
            except ElementNotVisibleException as e:
                return None
        return child_url
    
    def crawl(self):
        self._crawl(self.root)

    def _should_advance(self, child, child_url):
        return self._is_same_domain(child_url) and not self._has_visited(child, child_url)
    def _close_windows(self):
        wins = self.driver.window_handles

    def _call_subscribers(self):
        for s in self.subscribers:
            s.on_page_visited(self.driver)

    def _crawl(self, node):
        # Make request for the page
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
        l = len(anchors)
        for i in range(l):
            a = self.driver.find_elements_by_tag_name("a")[i]
            
            child_url = self._get_link_url(a)        
            
            #Only add if its not already there
            if child_url == None or self._has_sister(node, child_url):
                continue
            
            child = node.add_child(name=child_url)
            child.add_feature("path", self._get_url_path(child_url))

            # Determine if the link should be advanced forward
            # We never want to start crawling other pages
            if self._should_advance(child, child_url):
                child.add_feature("advance", True)
            else:
                child.add_feature("advance", False)
        

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
    #d = webdriver.Firefox() 
    d = webdriver.PhantomJS(executable_path='/home/wil/libs/node_modules/phantomjs/lib/phantom/bin/phantomjs')

    spider = SiteSpider(d, URL, depth=2, delay=5)
    #spider.auth(auth_handler)
    
    spider.add_subscriber(EventHandler.EventHandler())
    spider.add_subscriber(EventHandler.ExternalContent(d, URL))
    spider.crawl()
    print spider.get_link_graph().get_ascii(show_internal=True, attributes=["path"])
    
    driver.close()


    
