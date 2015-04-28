import csv
import pprint
import socket

# Load balancing is messing up resulst because we are getting multiple IPs
# assume single ip for domain
pages = {}
with open('post_process.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        url = row[0]
        domain = row[1]
        #ip = socket.gethostbyname(domain)

        if not (url in pages):
            pages[url] = []

        if not(domain in pages[url]):
            pages[url].append(domain)

pprint.pprint(pages)

for key in pages:
    print key + " " + str(len(pages[key]))
