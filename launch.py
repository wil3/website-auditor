#!/usr/bin/env python

import time
from ete2 import Tree
from urlparse import urlparse
from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException
URL = "https://www.etsy.com/"
#URL = "https://danielkummer.github.io/git-flow-cheatsheet/"

#URL = "http://okengineer.com/"
t = Tree()
root = t.add_child(name=URL)
root.add_features(path="[root]", advance=True)

def is_same_domain(href):
    curr = urlparse(href)
    base = urlparse(URL)
    #print "%s =? %s" % (curr.netloc, base.netloc)
    return curr.netloc == base.netloc

'''
If links use JS wont know url until it is clicked

visit then go back
'''



def scrape_links(base):
    links = []
    anchors = driver.find_elements_by_tag_name("a")
    l = len(anchors)
    for i in range(l):
        a = driver.find_elements_by_tag_name("a")[i]
        href = a.get_attribute("href")
        print href
        a.click()
        links.append(driver.current_url)
        driver.back()

    return links


def crawl(node):

    driver.get(node.name)
    links = scrape_links(node.name)
    
    for link in links:
        node.add_child(name=link)

def has_visited(node, url):
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

def has_sister(node,url):
    for sister in node.children:
        if sister.name == url:
            return True
    return False

def get_url_path(url):
    parse = urlparse(url)
    return parse.path

def crawl2(node):
    time.sleep(1)
    #print "Finding links for ", node.name
    print t.get_ascii(show_internal=True, attributes=["path"])
    anchors = driver.find_elements_by_tag_name("a")
    l = len(anchors)
    for i in range(l):
        a = driver.find_elements_by_tag_name("a")[i]
        href = a.get_attribute("href")
        if href == None:
            continue
        # Uses javascript so need to follow to see wher eit goes
        # a.click()
        #child_url = driver.current_url
        
        if href.endswith("#"):
            try:
                a.click()
                child_url = driver.current_url
                driver.back()
            except ElementNotVisibleException as e:
                print "Couldnt click element possibly hidden"
                continue
        else:
            child_url = href
        
        #Only add if its not already there
        if has_sister(node, child_url):
            continue
        
        child = node.add_child(name=child_url)
        child.add_feature("path", get_url_path(child_url))

        if is_same_domain(child_url) and not has_visited(child, child_url):
            #only follow if we havnt alread hit it coming to this nodej
            #Follow
           # if advance:
#            crawl2(child) 
            child.add_feature("advance", True)

        else:
            child.add_feature("advance", False)
            
        #driver.back()

    for child in node.children:
        if child.advance:
            crawl2(child)

    
def init_page(node):
    pass


def visit(base):
    anchors = driver.find_elements_by_tag_name("a")

    for a in anchors:
        href = a.get_attribute("href")
        print href
        #Only follow link if within the same domain

        if is_same_domain(href):
            print "following ", href
            a.click()
            visit()

driver = webdriver.Firefox() 
#driver = webdriver.PhantomJS(executable_path='/home/wil/libs/node_modules/phantomjs/lib/phantom/bin/phantomjs')

driver.get(root.name)
crawl2(root)
print t.get_ascii(show_internal=True, attributes=["path", "advance"])
#links = scrape_links(URL)
driver.close()
