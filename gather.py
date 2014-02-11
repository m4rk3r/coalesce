import re
import requests
import time

from collections import defaultdict
from urlparse import urlparse,urljoin
from bs4 import BeautifulSoup as BS
import pylibmc
from funcy import concat

cache = pylibmc.Client(["127.0.0.1"], binary=True,behaviors={"tcp_nodelay": True,"ketama": True})

seed = 'http://www.michael-hunter.net'

link_excludes = ['work','about','news','cv','resume','projects','images','videos','sculpture']
domain_excludes = ['twitter.com','facebook.com','flicker.com','vimeo.com','blogger.com',
    'google.com','blogspot.com','tumblr.com','digg.com','wordpress.org','amazon.com','mark-beasley.com',
    'bambi-boyblogspotcom.blogspot.nl','httpbambi-boyblogspotcom.blogspot.nl']

link_page_re = re.compile('^'+'|'.join(['links','friends'])+'$',flags=re.I) # ,'artists'
#name_re = re.compile(r"^(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)|(([\'\-a-z\s0-9]+){1,3})$",flags=re.I)
name_re = re.compile(r"^([\'\-a-z\s0-9]+){1,3}$",flags=re.I)

associations = {}
if not cache.get('associations'):
    # domain: { sites: [], name: 'link text' },
    cache.set('associations',{})

sites = {}
if not cache.get('sites'):
    # domain: hits
    # 'mark-basley.com': 1,
    cache.set('sites', {} )

def get_bs_for_url(url):
    global sites

    if not url.startswith('http'): url = 'http://'+url
    try:
        response = requests.get(url)
        return BS(requests.get(url).text)
    except:
        print 'removing ',base_url(url)
        try:
            del sites[ base_url(url) ]
        except:
            pass
        return None

def base_url(url,strip_sub=False):
    if not (url.startswith('http') or url.startswith('www.')): return url
    if strip_sub:
        return '.'.join(urlparse(url).netloc.split('.')[-2:])
    else:
        return urlparse(url).netloc.replace('www.','')

def find_link_page( url ):
    p = get_bs_for_url( url )
    if not p: return None
    link = p.find('a', text=link_page_re)
    return link

def is_absolute(url):
    return bool(urlparse(url).scheme) and not url.startswith('mailto:')

def get_next_url():
    for key in sites.keys():
        if key not in associations.keys():
            return key

def find_external_links( url ):
    _url = base_url(url)
    p = get_bs_for_url( url )
    if not p: return []
    links = p.find_all('a', text=name_re)
    results = []
    for obj in links:
        if ( base_url(obj.get('href','')) != _url and
             obj.text.lower().strip() not in link_excludes and
             is_absolute(obj.get('href','')) and
             base_url(obj.get('href',''),strip_sub=True) not in domain_excludes
             and urlparse(obj.get('href','')).netloc != 'http:'
            ):
            print 'adding: ',obj.get('href','')
            results.append( [obj.get('href',''), obj.text] )

    return results


def process_domain(url):
    # use in-memory dict, set cache at interval & end
    #associations = cache.get('associations')
    #sites = cache.get('sites')
    global associations
    global sites

    if base_url(url) in associations.keys():
        return associations[ base_url(url) ]

    l = find_link_page( url )
    if l:
        link_pg = (l.get('href','') if is_absolute(l.get('href',''))
            else urljoin(url+'/', l.get('href','').strip('/')))
        print 'found link page: ',link_pg
        links = find_external_links( link_pg )
        # increment occurance
        for link in links:
            _url = base_url(link[0])
            if _url in sites.keys():
                sites[ _url ]['hitcount'] += 1
            else:
                sites[ _url ] = {
                    'name':link[1],
                    'hitcount':1
                }

        associations[ base_url(url) ] = {
            'linkages': links,
        }
    else:
        associations[base_url(url)] = {
            'linkages':[]}


if __name__=='__main__':
    obj = process_domain( seed )
    step = 0
    while len(associations.keys()) < len(sites.keys()):
        _url = get_next_url()
        print 'exploring: ',_url
        process_domain( _url )

        step += 1
        if step%50==0:
            cache.set('associations',associations)
            cache.set('sites',sites)


    # final assignment
    cache.set('associations',associations)
    cache.set('sites',sites)

