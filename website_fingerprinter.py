import csv
import pprint
import socket
import argparse
import urlparse
import logging

logger = logging.getLogger("fingerprint")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('website_fingerprint.log')
logger.addHandler(fh)

class SitePage():
    def __init__(self, url):
        self.url = url
        self.transactions = []

    def add_transaction(self, t):
        self.transactions.append(t)

    def __repr__(self):
        return self._to_str()
    
    def __str__(self):
        return self._to_str()

    def _to_str(self):
        a = [ "\t" + str(t) + "\n" for t in self.transactions]
        b = "".join(a)
        return self.url + "\n" + b #pprint.pformat(self.transactions)

class Transaction():

    def __init__(self, dir, origin, resource_domain, resource_path, len):
        self.dir = dir
        self.origin = origin
        self.resource_domain = resource_domain
        self.resource_path = resource_path
        self.len = len
    def __repr__(self):
        return self._to_str()
    def __str__(self):
        return self._to_str()

    def _to_str(self):
        d = '<'
        if self.dir == 'REQUEST':
            d = '>'
        return d + " " + self.resource_domain + " "  + self.resource_path + " " + str(self.len)

class PageFingerprintProcessor():

    def __init__(self):
        pass


    def get_fingerprints(self, filepath):
# Load balancing is messing up resulst because we are getting multiple IPs
# assume single ip for domain
        pages = {}
        requests = {} 
        response = {} 
        with open(filepath, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                print row
                dir = row[1]
                
                page_url = row[2]
                #Referer, can be none
                # If None then it is the page request by the user
                referer = row[3]
                if referer == 'None':
                    referer = None
                else:
                    referer = urlparse.urlparse(referer).path

                resource_domain = row[4]
                if resource_domain == '127.0.0.1:8080':
                    continue
                
                resource_path = urlparse.urlparse(row[5]).path
                resource_len = int(row[6])
                #ip = socket.gethostbyname(domain)
                t = Transaction(dir, referer, resource_domain, resource_path, resource_len)
                print t
                if not (page_url in pages):
                    pages[page_url] = SitePage(page_url)

                
                pages[page_url].add_transaction(t)

                #if not(domain in pages[url]):
                #    pages[url].append(domain)
                
                #if dir == 'REQUEST':
                #    if and not(resource_path in requests):
                #        requests[resource_path] = []
                #    if referer != None:
                #        requests[referer].append(t)

                #else:
                #    if referer == None and not(resource_path in response):
                #        response[resource_path] = []
                #    if referer != None:
                #        response[referer].append(t)

        #pprint.pformat(pages)
        #pprint.pprint(pages)
        return pages
#pprint.pprint(pages)

#for key in pages:
#    print key + " " + str(len(pages[key]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process MITM requests to form page fingerprints')
    parser.add_argument('log', help='Fingerprint log')
    args = parser.parse_args()
    filepath = args.log

    pages = PageFingerprintProcessor()
    fingerprints = pages.get_fingerprints(filepath)
    logger.info(pprint.pformat(fingerprints))


