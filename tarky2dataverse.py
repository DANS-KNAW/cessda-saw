#!/usr/bin/python

import urllib2
import time
from subprocess import Popen, PIPE, STDOUT
from settings import *
import sys
from BeautifulSoup import *
from paste.util.multidict import MultiDict
import re
import json

def read_remote_page(url):
    response = urllib2.urlopen(url)

    html = response.read()
    return html

links = []
mapfile = open(newmap,'w')
lexicon = {}
with open(humap) as fp:
    for textline in fp:
	textline = textline.rstrip('\n')
	words = textline.split('\t')
	try:
	   lexicon[words[0]] = words[1]
	except:
	   skip = 1

indexpage = read_remote_page(url)

def get_indexpage(indexpage):
    indexscan = {}
    parsed_html = BeautifulSoup(indexpage) #, "html.parser")
    items = parsed_html.findAll('td', attrs={'valign':'top'})
    for item in items:
        #print item
        title = item.find('a') #, attrs={'img':'class bdtIcon'})
        try:
            indexscan[title['href']] = title.text
        except:
            skip = 1
    return indexscan

def cleaner(thisvalue):
    if thisvalue:
	thisvalue = re.sub(r'(<h1>|<\/h1>|\&ndash\;|<i>|<\/i>|<p>\s*|\s*<\/p>|\n)', '', str(thisvalue))
	thisvalue = re.sub('(<p class.+)', '', str(thisvalue))
	regvalue = re.match('<a\s+href.+?>(.+?)<\/a>', str(thisvalue))
	if regvalue:
	    thisvalue = regvalue.group(1)
    return thisvalue

i = get_indexpage(indexpage)
for inturl in i:
    idsm = re.search('TDATA\-(\S+)', inturl, re.MULTILINE)
    xmldatafile = 'somefile'
    if idsm:
	xmldatafile = "./data/%s.xml" % idsm.group(1)
    xmlfile = open(xmldatafile,'w')

    html = read_remote_page(inturl)
    parsed_html = BeautifulSoup(html) #, "html.parser")
    items = parsed_html.findAll('p') #, attrs={'class':'toolDataItemName'})
    mainkey = ''
    
    d = MultiDict()
    DEBUG = 0
    for item in items:
        cleanitem = item
        thiskey = item.find('b') #, attrs={'img':'class bdtIcon'})
        if thiskey:
            value = str(item)
            value = value.replace(str(thiskey), '')
	    value = cleaner(value)
            if DEBUG:
                print "X %s" % value
            mainkey = thiskey
	    if value:
                d.add(thiskey.text, value)
        else:
            if mainkey:
                if DEBUG:
                    print mainkey.text
                    print item
                d.add(mainkey.text, item)

    # final result
    shown = {}

    xmlfile.write("<?xml version=\"1.0\"?>\n")
    xmlfile.write("<entry xmlns=\"http://www.w3.org/2005/Atom\"\n")
    xmlfile.write("       xmlns:dcterms=\"http://purl.org/dc/terms/\">\n")
    xmlfile.write("   <dcterms:source>%s</dcterms:source>\n" % inturl)

    for thiskey in d:
	dckey = ''
	if thiskey in lexicon:
	    dckey = lexicon[thiskey]
	    if not dckey:
		dckey = 'dcterms:subject'

        if thiskey not in shown:
	    mapfile.write("%s\t\n" % thiskey)
            try:
                if d.getall(thiskey)[1]:
		    for ix in range(0,len(d.getall(thiskey))):
			value = d.getall(thiskey)[ix]
			if dckey:
			    value = cleaner(value)
			    if value:
			        xmlfile.write("	<%s>%s</%s>\n" % (dckey, value, dckey))
            except:
		if dckey:
		    if d.getall(thiskey)[0]:
		        value = cleaner(str(d.getall(thiskey)[0]))
			if value:
		            xmlfile.write("   <%s>%s</%s>\n" % (dckey, value, dckey))
            shown[thiskey] = 'yes'

    xmlfile.write("</entry>")
    xmlfile.close()

    if PUBLISH:
        cmd = "curl -u '%s': --data-binary \"@%s\" -H \"Content-Type: application/atom+xml\" %s/dvn/api/data-deposit/v1.1/swordv2/collection/dataverse/tarki" % (token, xmldatafile, host)
	print cmd
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        out, err = p.communicate()
	handlestring = re.search(r'edit-media\/study\/(\S+)\"', out, re.MULTILINE)
	if handlestring:
	    handle = handlestring.group(1)
	    if handle:
		cmd = "cat /dev/null | curl -u '%s': -X POST -H \"In-Progress: false\" --data-binary @- %s/dvn/api/data-deposit/v1.1/swordv2/edit/study/%s" % (token, host, handle)
		p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
		print handle
    time.sleep(1)

mapfile.close()
