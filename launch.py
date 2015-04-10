#!/usr/bin/env python

import time
from ete2 import Tree
from urlparse import urlparse
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException

import EventHandler

class SiteSpider:

    def __init__(self, driver, target_url): 
        self.driver = driver
        self.target_url = target_url
        self.t = Tree()
        self.root = self.t.add_child(name=URL)
        self.root.add_features(path=URL, advance=True)

    def _is_same_domain(self, href):
        curr = urlparse(href)
        base = urlparse(URL)
        #print "%s =? %s" % (curr.netloc, base.netloc)
        return curr.netloc == base.netloc

    def _has_visited(self, node, url):
        '''
        TODO: Probably a better way to do this
        '''
        for ancestor in node.iter_ancestors():
            if ancestor.name == url:
                return True
            else:
                for sister in ancestor.get_sisters():
                    if sister.name == url:
                        return True
                
        return False

    def _has_sister(self, node,url):
        for sister in node.children:
            if sister.name == url:
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
       
        href = a.get_attribute("href")
        if href == None:
           return None 
        # If pound then JS must handle this link so follow it to see
        # where it goes
        if href.endswith("#"):
            try:
                a.click()
                child_url = driver.current_url
                driver.back()
            except ElementNotVisibleException as e:
                print "Couldnt click element possibly hidden"
                return None
        else:
            child_url = href

        return child_url
    
    def crawl(self):
        self._crawl(self.root)

    def _crawl(self, node):
        # Make request for the page
        self.driver.get(node.name)

        if self.callback:
            self.callback.on_page_visited(self.driver)

        time.sleep(1)
        print self.driver.current_url    
        print self.t.get_ascii(show_internal=True, attributes=["path"])

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
            if self._is_same_domain(child_url) and not self._has_visited(child, child_url):
                child.add_feature("advance", True)
            else:
                child.add_feature("advance", False)
        

        #Process all the found links
        for child in node.children:
            if child.advance:
                self._crawl(child)

    def get_link_graph(self):
        return self.t

    def subscribe(self, callback):
        self.callback = callback



if __name__ == "__main__":
    #URL = "https://www.etsy.com/"
#URL = "https://danielkummer.github.io/git-flow-cheatsheet/"
    URL = "http://okengineer.com/"
    driver = webdriver.Firefox() 
#driver = webdriver.PhantomJS(executable_path='/home/wil/libs/node_modules/phantomjs/lib/phantom/bin/phantomjs')

    spider = SiteSpider(driver, URL)
    spider.subscribe(EventHandler.EventHandler())
    spider.crawl()
    print spider.get_link_graph().get_ascii(show_internal=True, attributes=["path"])
    driver.close()


    
