
import argparse
import dpkt
import socket
import math
import binascii
import pprint
import logging
from website_fingerprinter import *
import operator
import requests
from requests.exceptions import SSLError 
import re
logger = logging.getLogger("sidechannel")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('sidechannel.log')
logger.addHandler(fh)

class WebPage():

    def __init__(self):
        self.transactions = []

    def add_transaction(self, t):
        self.transactions.append(t)

    def __repr__(self):
        return self._to_str()
    
    def __str__(self):
        return self._to_str()

    def _to_str(self):
        return pprint.pformat(self.transactions)

    def rx(self):
        return sum([ t.rx() for t in self.transactions])

    def tx(self):
        return sum([ t.tx() for t in self.transactions])

class Resource():
    def __init__(self):
        #index by port
        self.transactions = [] 

    def __repr__(self):
        return self._to_str()
    
    def __str__(self):
        return self._to_str()

    def _to_str(self):
        s = sorted(self.transactions, key=operator.attrgetter('pkt_num'))
        return pprint.pformat(s)
    
    def rx(self):
        rx_total = 0
        for t in self.transactions:
            if t.flow == Transaction.RESPONSE:
                rx_total += t.len
        return rx_total

    def tx(self):
        tx_total = 0
        for t in self.transactions:
            if t.flow == Transaction.REQUEST:
                tx_total += t.len
        return tx_total

class ResourceTransaction():

    def __init__(self, pkt_num, flow, remote_ip, host, client_port, len):
        self.flow = flow
        self.pkt_num = pkt_num        
        self.dst = remote_ip
        self.host = host
        self.len = len
        self.port = client_port
        self.host_mapping = {}

    def ip_host_mapping(self):
        pass

    def __repr__(self):
        return self._to_str()
    
    def __str__(self):
        return self._to_str()

    def _to_str(self):
        flow = '>'
        if self.flow == Transaction.RESPONSE:
            flow = '<'
        return  flow + " #" + str(self.pkt_num) + " " + str(self.port) + " " +  self.dst + "(" + str(self.host) + ") " + str(self.len)

class SSLSideChannel():
    '''
    Run this class with a pcap file to try and identiy which 
    pages are being visited
    '''
    TSL_APPLICATION_DATA = 23

    def __init__(self, filepath, client_ip):
        self.filepath = filepath
        self.client_ip = client_ip
        self.ip_host_mappings = {}

    def process(self):
        f = open(self.filepath)
        pcap = dpkt.pcap.Reader(f)
        pages = self._identify(pcap)
        f.close()
        return pages

    def move_requests_to_resource(self,requests):
        page = WebPage()
        for port in requests:
            resource_transactions = requests[port]
            resource = Resource()
            resource.transactions += resource_transactions
            page.add_transaction(resource)
        
        return page
    
    def _extract_domain_from_exception(self, e):
        m = re.match('(.*match[\w\s]+)(.*)', e)
        domains = m.group(2)

        return domains.split(",")

    def resolve_host(self, ip):
        if ip == self.client_ip:
            return None

        url = "https://" + ip

        try:
            requests.get(url)
        except SSLError as e:
            domain = self._extract_domain_from_exception(str(e))
            return domain[0]

    def add_host_if_missing(self, ip):
        host = None
        #Do we have the host for the dest?
        if not(ip in self.ip_host_mappings):
               host = self.resolve_host(ip) 
               if host:
                   self.ip_host_mappings[ip] = host
        else:
            host = self.ip_host_mappings[ip]
        return host

    def _identify(self, pcap):
        pages = []
        first = True
        start_time = 0
        last_request = 0
        pkt_counter = 0
        accum_length = 0
        server_ips = []
        last_src = None
        accum_resource_length = 0
        request_count = 0
        requests = {}
        resource = Resource()
        for ts, buf in pcap:

            pkt_counter += 1
            if first:
                start_time = ts
                last_request = ts
                first = False
            
            #if pkt_counter < 450:
            #    continue

            eth = dpkt.ethernet.Ethernet(buf)
            if not isinstance(eth.data, dpkt.ip.IP):
                continue
            ip = eth.data
            if not isinstance(ip.data, dpkt.tcp.TCP):
                continue

            tcp = ip.data
            if tcp.dport != 443 and tcp.sport != 443:
                continue

            if len(tcp.data) <= 0:
                continue

            if ord(tcp.data[0]) != self.TSL_APPLICATION_DATA:
                continue

            ip_src = socket.inet_ntoa(ip.src)
            ip_dst = socket.inet_ntoa(ip.dst)
           
            if ip_src != self.client_ip and ip_dst != self.client_ip:
                continue 

            b = tcp.data[3] + tcp.data[4]
            data_len = int(binascii.hexlify(b), 16)


            #Look at the time different from last request and see 
            # if a new page request
            delta_time = ts - last_request
            last_request = ts
           
#TODO This is a hack, remove
            if delta_time > 15:
                page = self.move_requests_to_resource(requests)

                pages.append(page)
                #logger.info(pprint.pformat(requests))
                #logger.info(pprint.pformat(page))
                #New page!
                request_count += 1
                requests = {}

            # A new resource is being requested by the client
            # assume new port is being used for each resource
            #TODO make sure this is correct 
            if ip_src == self.client_ip:
                
                host = self.add_host_if_missing(ip_dst)
                
                if not(tcp.sport in requests):
                    requests[tcp.sport] = []

                r =ResourceTransaction(\
                                       pkt_counter,\
                                       Transaction.REQUEST, \
                                       ip_dst,\
                                       host,\
                                       tcp.sport, \
                                       data_len)
                requests[tcp.sport].append(r)

            else:
                host = self.add_host_if_missing(ip_src)

                if not(tcp.dport in requests):
                    requests[tcp.dport] = []
                    
                r = ResourceTransaction(\
                                        pkt_counter,\
                                        Transaction.RESPONSE,\
                                        ip_src,\
                                        host,\
                                        tcp.dport,\
                                        data_len)

                requests[tcp.dport].append(r)

        print "Total requests = " + str(request_count)    
        print "Total transferred to client = "  + str(accum_length) 
        print "Unique server IPs = " + str(len(server_ips))
        print str(len(pages))
        #print server_ips
        return pages

    def print_stats(self,pages):
        for page in pages:
            logger.info("Resource requests " + str(len(page.transactions)))
            logger.info("Bytes sent " + str(page.tx()))
            logger.info("Bytes received " + str(page.rx()))
            logger.info(pprint.pformat(page))
            logger.info("\n")
        #process the ips and see if multipel resolve to the same domain
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Detect port scan')
    parser.add_argument('client_ip', help='IP address of the client')
    parser.add_argument('pcap', help='Location to pcap file')
    args = parser.parse_args()
    d = SSLSideChannel(args.pcap, args.client_ip)
    pages = d.process()
    d.print_stats(pages)

