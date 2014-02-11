import pylibmc
import os

cache = pylibmc.Client(["127.0.0.1"], binary=True,behaviors={"tcp_nodelay": True,"ketama": True})

sites = cache.get('sites')

print '# %s' % len(sites.keys())
cols = 4

style = '''
<style type='text/css'>
    ul,li {
        list-style:none;
    }
    .main {
        padding:0px;
    }
    .main li {
        margin-bottom:2px;
    }
    .main ul {
        padding:0px;
    }
    .col {
        width: 225px;
        float:left;
    }

    .col a:visited { color: purple; }
    .col + col {
        margin-left: 5px;
    }
</style>
'''

template = u"<li><a href='http://{0}'>{1}</a></li>"

collen = len(sites.keys())/cols

count = 0

output = u'''
<em style='opacity:.85;padding-right:5px;'>links collected from a web crawler starting on a friends page
   and following each successive 'friends' 'links' or 'artists' list until
   all options are exhausted</em>
<br>
<ul class='main'>'''
first_run = True
for item in sites.items():

    if count % collen == 0:
        if not first_run: output +='</ul></li>'
        else: first_run = False
        output += "<li class='col'><ul>"

    count += 1
    output += template.format( item[0], item[1]['name'] )

output +='</ul></li></ul>'

print style + output