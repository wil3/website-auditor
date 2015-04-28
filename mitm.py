from miproxy.proxy import RequestInterceptorPlugin, ResponseInterceptorPlugin, AsyncMitmProxy
import pprint
import re
import logging
import urlparse
import base64
logging.basicConfig(level=logging.FATAL)

logger = logging.getLogger("fp")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('fingerprint.csv')
logger.addHandler(fh)

class RecordInterceptor(RequestInterceptorPlugin, ResponseInterceptorPlugin):

        current_page = None
        '''
        This mitm proxy records all the traffic leaving so we
        can attempt to fingerprint the page
        '''
#TODO we need the schema, if there is mixed content even easier
#
        def do_request(self, data):
	    headers = self.get_headers(data)
	    host = None
	    referer = None
            len = 0 
	    if 'Host' in headers:
		host = headers['Host']
#TODO for some reason
#Phantom is not setting the referer so we dont know
#what page its coming from 
	    if 'Referer' in headers:
		referer = headers['Referer']
	   
	    if 'Content-Length' in headers:
                try:
                    len = int(headers['Content-Length'])
                except:
                    pass
       
            #If we see this then it is a signal
            # that a new page is being requested
            #logger.debug("Host " +host)
            if host == '127.0.0.1:8080':
                parsed_url = urlparse.urlparse(self.message.path)
             #   logger.debug( parsed_url)
                page = urlparse.parse_qs(parsed_url.query)["page"][0]
              #  logger.debug("query=" + str(page))
                RecordInterceptor.current_page = base64.b64decode(page)
               # logger.debug("Current " + RecordInterceptor.current_page)

            self.message.host = host
	    self.message.referer = referer

	    logger.info('REQUEST' + "," \
                 + str(RecordInterceptor.current_page) + "," \
                 + str(referer) + "," \
                 + str(self.message.host) + "," \
                 + self.message.path + "," + str(len))
            # logger.info(headers)
	    return data


        def do_response(self, data):
	    headers = self.get_headers(data)
	    len = 0 
	    if 'Content-Length' in headers:
                try:
		    len = int(headers['Content-Length'])
                except:
                    pass
	
	    # The referer will tell us where its coming from
	    # and we want all the data we can get to make a fingerprint
	    # For a host outside the site is an even better indication 
	    # of the page visited
	    logger.info('RESPONSE' + "," \
                 + str(RecordInterceptor.current_page) + "," \
                 + str(self.message.referer) + "," \
                 + str(self.message.host) + "," \
                 + self.message.path + "," + str(len))
            return data
	
	def get_headers(self, data):
	    return dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", data))
	    

if __name__ == '__main__':
    proxy = None
    proxy = AsyncMitmProxy()
    proxy.register_interceptor(RecordInterceptor)
    try:
        proxy.serve_forever()
    except KeyboardInterrupt:
        proxy.server_close()
