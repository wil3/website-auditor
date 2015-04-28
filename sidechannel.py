
import argparse
import dpkt
import socket
import math
import binascii

class SSLSideChannel():
    '''
    Run this class with a pcap file to try and identiy which 
    pages are being visited
    '''
    TSL_APPLICATION_DATA = 23

    def __init__(self, filepath, client_ip):
        self.filepath = filepath
        self.client_ip = client_ip

    def process(self):
        f = open(self.filepath)
        pcap = dpkt.pcap.Reader(f)
        self._identify(pcap)
        f.close()

    def _identify(self, pcap):
        first = True
        start_time = 0
        last_request = 0
        pkt_counter = 0
        accum_length = 0
        server_ips = []
        last_src = None
        accum_resource_length = 0
        request_count = 0
        for ts, buf in pcap:

            pkt_counter += 1
            if first:
                start_time = ts
                last_request = ts
                first = False
               

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
            # A new resource is being requested by the client
            if ip_src == self.client_ip:
                request_count += 1
                if last_src != self.client_ip and last_src != None:
                    
                    print "Request to " + last_src + " complete. Total length " + str(accum_resource_length)
                   
                   
                    # New request so reset everything
                    accum_resource_length = 0
                    delta_time = ts - last_request
                    print "Time lapse since last resource " + str(delta_time)

                    #If enough time passes we can assume it is a new page

                    last_request = ts
            else:
                b = tcp.data[3] + tcp.data[4]
                data_len = int(binascii.hexlify(b), 16)
                accum_resource_length += data_len
                accum_length += data_len                
            
            if ip_src != self.client_ip and not (ip_src in server_ips):
                server_ips.append(ip_src)
            last_src = ip_src
                
            
        print "Total requests = " + str(request_count)    
        print "Total transferred to client = "  + str(accum_length) 
        print "Unique server IPs = " + str(len(server_ips))
        #print server_ips

        #process the ips and see if multipel resolve to the same domain
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Detect port scan')
    parser.add_argument('client_ip', help='IP address of the client')
    parser.add_argument('pcap', help='Location to pcap file')
    args = parser.parse_args()
    d = SSLSideChannel(args.pcap, args.client_ip)
    d.process()
    
