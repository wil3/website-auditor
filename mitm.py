from miproxy.proxy import RequestInterceptorPlugin, ResponseInterceptorPlugin, AsyncMitmProxy
import pprint
import re
import logging

logging.basicConfig(level=logging.FATAL)

logger = logging.getLogger("fp")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('passive.csv')
logger.addHandler(fh)

class DebugInterceptor(RequestInterceptorPlugin, ResponseInterceptorPlugin):
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
	    if 'Host' in headers:
		host = headers['Host']
	    if 'Referer' in headers:
		referer = headers['Referer']
	    self.message.host = host
	    self.message.referer = referer

	    return data


        def do_response(self, data):
	    headers = self.get_headers(data)
	    len = '' 
	    if 'Content-Length' in headers:
		len = headers['Content-Length']
	
	    # The referer will tell us where its coming from
	    # and we want all the data we can get to make a fingerprint
	    # For a host outside the site is an even better indication 
	    # of the page visited
	    logger.info(str(self.message.referer) + "," + str(self.message.host) + "," + self.message.path + "," + len)
            return data
	
	def get_headers(self, data):
	    return dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", data))
	    

if __name__ == '__main__':
    proxy = None
    proxy = AsyncMitmProxy()
    proxy.register_interceptor(DebugInterceptor)
    try:
        proxy.serve_forever()
    except KeyboardInterrupt:
        proxy.server_close()
