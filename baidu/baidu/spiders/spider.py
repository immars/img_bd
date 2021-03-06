#
# -*- coding: utf-8 -*-
import sys
import scrapy
import urllib2
import json
import re
from scrapy.spiders import CrawlSpider,Spider, Rule
from scrapy.linkextractors import LinkExtractor


def prop_get(pmap, names):
    tmp = None
    for name in names:
        if not tmp:
            tmp = pmap.get(name)
        else:
            break
    if not tmp:
        tmp = ''

    return tmp

'''
seed image url:
    http://www.elongstatic.com/gp2/M00/48/54/rIYBAFNWuh2AMKvgAADWYi3r560716.jpg

main page:
    http://image.baidu.com/n/pc_search?queryImageUrl=http%3A%2F%2Fwww.elongstatic.com%2Fgp2%2FM00%2F48%2F54%2FrIYBAFNWuh2AMKvgAADWYi3r560716.jpg&fm=stuhome&uptype=urlsearch

image url:


markets:
    www.taobao.com/market/xxxx/yyyy.php
    important woman markets:
    http://www.taobao.com/market/nvzhuang/index.php
    http://www.taobao.com/market/mei/index.php
    http://www.taobao.com/market/nvbao/shouye.php
    http://www.taobao.com/market/nvxie/citiao/index.php

lists:
    http://s.taobao.com/list?q=%D6%D0%B8%FA
item:
    http://item.taobao.com/item.htm?id=41297993338


http://www.taobao.com/market/nvbao/shouye.php?spm=a217q.7279049.a214d6o.10.i0aDxl
http://s.taobao.com/list?q=%C5%AE%B0%FC+%C1%F7%CB%D5

http://detail.tmall.com/item.htm?id=43146919700&ali_refid=a3_430329_1006:1103685483:N:%C5%A3%D7%D0%CD%E2%CC%D7:5b0ac9df717b2ae4136d1507ba93ccc6&ali_trackid=1_5b0ac9df717b2ae4136d1507ba93ccc6&spm=a217f.1256815.1998111894.1793.la1FiE&scm=1029.minilist-17.1.16#detail
http://gi3.md.alicdn.com/bao/uploaded/i3/TB1iW.iGVXXXXajXXXXXXXXXXXX_!!0-item_pic.jpg_430x430q90.jpg

'''


class BaiduSpider(Spider):
    name = "baidu"
    allowed_domains = ["baidu.com"]

    def imgsearch_requests(self, seeds):
        return [scrapy.http.Request("http://image.baidu.com/n/pc_search?queryImageUrl=%s&fm=stuhome&uptype=urlsearch" % (urllib2.quote(s))) for s in seeds] + \
            [scrapy.http.Request("http://image.baidu.com/n/similar?queryImageUrl=%s&pn=28&rn=100&sort=&fr=pc" % (urllib2.quote(s))) for s in seeds]

    def parse_url_jsons(self, path):
        seeds = open(path).readlines()
        self.log("start_request seed length:%d" % len(seeds))
        requests = []
        for seed in seeds:
            try:
                j = json.loads(seed)
                for url in j["image_urls"]:
                    requests.append(url)
            except Exception, e:
                self.log(e.message)
                pass
        return requests

    def parse_path_jsons(self, path):
        seeds = open(path).readlines()
        self.log("start_request seed length:%d" % len(seeds))
        requests = []
        for seed in seeds:
            try:
                j = json.loads(seed)
                for i in j["images"]:
                    requests.append(i['path'])
            except Exception, e:
                self.log(e.message)
                pass
        return requests


    def start_requests(self):
        requests = self.parse_url_jsons("/home/disk1/mulisen/crawler/bcrawl/scrapyd/items/baidu/lianjia/46845cc5340b11e5860db8f6b1123a15.jl")
        self.log("start_requests length:%d" % len(requests))
        # seeds = [img['url'] for img in [json.loads(line) for line in seeds]]
        requests = self.imgsearch_requests(requests)

        # requests = [scrapy.http.Request("http://image.baidu.com/n/pc_search?queryImageUrl=%s&fm=stuhome&uptype=urlsearch" % (urllib2.quote(s))) for s in seeds]
        for req in requests:
            yield req
        #requests = [scrapy.http.Request("http://image.baidu.com/n/similar?queryImageUrl=%s&pn=28&rn=100&sort=&fr=pc" % (urllib2.quote(s))) for s in seeds]
        #for req in requests:
        #    yield req

    def parse(self, response):
        if response.url.startswith("http://image.baidu.com/search/index?"):
            self.log("text search page! %s" % response.url)
            p=re.compile("\"middleURL\":\"([^\"]*)\"")
            image_urls = [ i.group(1) for i in p.finditer(response.body)]
            # yield {"type": "txtsearch", "url": response.url, "image_urls": image_urls}
            pass
        elif response.url.startswith("http://image.baidu.com/n/pc_search?"):
            self.log('image search page! %s' % response.url)
            texts = response.css("#guessInfo div.guess-info-text a::text").extract()
            requests = [scrapy.http.Request("http://image.baidu.com/search/index?tn=baiduimage&ps=1&ct=201326592&lm=-1&cl=2&nc=1&ie=utf-8&word=%s" % (t)) for t in texts]
            for req in requests:
                yield req
        elif response.url.startswith("http://image.baidu.com/n/similar?"):
            self.log("getting json")
            j = json.loads(response.body)
            image_urls = [i["objURL"] for i in j['data']]
            yield {"type":"imgsearch", "image_urls": image_urls}

class LianjiaSpider(CrawlSpider):
    name="lianjia"
    allow_domains = ["bj.lianjia.com"]
    #  start_urls = ["http://bj.lianjia.com/ershoufang/"]

    def start_requests(self):
        yield scrapy.http.Request("http://bj.lianjia.com/ershoufang/")
        for i in range(2, 3579):
            yield scrapy.http.Request("http://bj.lianjia.com/ershoufang/pg%d" % i)

    rules = (
        # Extract links matching 'category.php' (but not matching 'subsection.php'
        # and follow links from them (since no callback means follow=True by default).
        Rule(LinkExtractor(allow=('/ershoufang/pg.*', )), follow=True),
        Rule(LinkExtractor(allow=('/ershoufang/BJ.*\.html', )), callback='parse_house'),
    )

    def parse_house(self, response):
        self.log('Hi, this is an house page! %s' % response.url)
        # image_urls=response.css("#semiContent p a img::attr(obj-url)").extract()
        # yield {"image_urls":image_urls}
        image_urls = [url.replace("600x450","800x600") for url in response.css('li.actShowImg img::attr("data-url")').extract()]
        yield {"image_urls": image_urls}


"""
    to8to.com
"""
class To8ToSpider(Spider):
    name="to8to"
    allow_domains = ["to8to.com"]
    #  start_urls = ["http://bj.lianjia.com/ershoufang/"]

    def start_requests(self):
        yield scrapy.http.Request("http://xiaoguotu.to8to.com/list-h6s9i0")
        for i in range(2, 53):
            yield scrapy.http.Request("http://xiaoguotu.to8to.com/list-h6s9i0p%d" % i)
    """
    rules = (
        # Extract links matching 'category.php' (but not matching 'subsection.php'
        # and follow links from them (since no callback means follow=True by default).
        Rule(LinkExtractor(allow=('/list-h6s9i0p*', )), follow=True, callback='parse_index'),
        Rule(LinkExtractor(allow=('/p.*\.html', )), callback='parse_house'),
        Rule(LinkExtractor(allow=('/getxgtjson.*', )), callback='parse_json'),
    )
    """

    def parse_index(self, response):
        hrefs = [h[2:-5] for h in response.css("div.item a::attr(href)").extract()]
        return [scrapy.http.Request("http://xiaoguotu.to8to.com/getxgtjson.php?a2=1&a12=&a11=%s&a1=0&a17=1" % item_id) for item_id in hrefs]

    def parse_house(self, response):
        self.log('Hi, this is an house page! %s' % response.url)
        # image_urls=response.css("#semiContent p a img::attr(obj-url)").extract()
        # yield {"image_urls":image_urls}
        # image_urls = [url.replace("600x450","800x600") for url in response.css('li.actShowImg img::attr("data-url")').extract()]
        # yield {"image_urls": image_urls}

    def parse_json(self, response):
        data = json.loads(response.body)
        paths = [ d['l']['s'] for d in data['dataImg']]
        bigpaths = ['http://pic2.to8to.com/case/' + p[:-10] + 'l1' + p[-8:-4] + '_sp' + p[-4:] for p in paths]
        self.log("image got:%d" %len(bigpaths))
        return [{"image_urls": bigpaths}]

    def parse(self, response):
        if response.url.startswith("http://xiaoguotu.to8to.com/list-h6s9i0"):
            for req in self.parse_index(response):
                yield req
        elif response.url.startswith("http://xiaoguotu.to8to.com/getxgtjson"):
            for req in self.parse_json(response):
                yield req


'''
class BaiduSpider(CrawlSpider):
    name="baidu"
    allow_domains = ["baidu.com"]

    def start_requests(self):
        seeds = ["http://www.elongstatic.com/gp2/M00/48/54/rIYBAFNWuh2AMKvgAADWYi3r560716.jpg"]
        requests = [scrapy.http.Request("http://image.baidu.com/n/pc_search?queryImageUrl=%s&fm=stuhome&uptype=urlsearch" % (urllib2.quote(s))) for s in seeds]
        for req in requests:
            yield req
        requests = [scrapy.http.Request("http://image.baidu.com/n/similar?queryImageUrl=%s&pn=28&rn=100&sort=&fr=pc" % (urllib2.quote(s))) for s in seeds]
        for req in requests:
            yield req

    rules = (
        # Extract links matching 'category.php' (but not matching 'subsection.php'
        # and follow links from them (since no callback means follow=True by default).
        Rule(LinkExtractor(allow=('/n/pc_search?queryImageUrl', )), callback='parse_imgsearch'),
        Rule(LinkExtractor(allow=('/n/similar?queryImageUrl', )), callback='follow_json'),
        Rule(LinkExtractor(allow=('/search/index', )), callback='parse_txtsearch'),
    )

    def follow_json(self, response):
        self.log("getting json")
        j = json.loads(response.body)
        image_urls = [i["objURL"] for i in j['data']]
        yield {"image_urls": image_urls}

    def parse_imgsearch(self, response):
        self.log('Hi, this is an item page! %s' % response.url)
        # image_urls=response.css("#semiContent p a img::attr(obj-url)").extract()
        # yield {"image_urls":image_urls}
        texts = response.css("#guessInfo div.guess-info-text a::text").extract()
        requests = [scrapy.http.Request("http://image.baidu.com/search/index?tn=baiduimage&ps=1&ct=201326592&lm=-1&cl=2&nc=1&ie=utf-8&word=%s" % (t)) for t in texts]
        for req in requests:
            yield req

    def parse_txtsearch(self, response):
        return

'''
'''
    TMALL spider
main pages:
    http://nvzhuang.tmall.com/
    http://nvxie.tmall.com/
    http://bag.tmall.com/

topic pages:
    http://www.tmall.com/go/market/promotion-act/xiangbaofenqigoudierqi.php
    http://www.tmall.com/go/market/promotion-act/xiangbaowoshinianhuo.php
    http://www.tmall.com/go/market/fushi/chongaizj.php
    http://www.tmall.com/go/market/fushi/module2014-1.php
    http://www.tmall.com/go/market/fushi/loveziji.php
    http://www.tmall.com/go/market/fushi/module2014-2.php


market lists:
        page down:s=60
    http://list.tmall.com/search_product.htm?&vmarket=48386
    http://list.tmall.com/search_product.htm?sort=s&cat=51024008
    http://list.tmall.com/search_product.htm?sort=s&cat=51024008
    http://list.tmall.com/search_product.htm?brand=3713796&q=MCM&sort=s

brand pages:
        or:
    http://xxx.tmall.com/index.htm
    http://memxiangbao.tmall.com/
    http://qiwang.tmall.com/
    http://panbixuan.tmall.com/
    http://panbixuan.tmall.com/

item:
    http://detail.tmall.com/item.htm?id=13505747865

'''
class TMallSpider(CrawlSpider):
    name="tmall"
    allow_domains = ["tmall.com"]

    start_urls = ["http://nvzhuang.tmall.com/","http://nvxie.tmall.com/","http://bag.tmall.com/"]

    rules = (
        # Extract links matching 'category.php' (but not matching 'subsection.php'
        # and follow links from them (since no callback means follow=True by default).
        Rule(LinkExtractor(allow=('/go/market/.*\.php', ), ), callback='check_response', follow=True, process_links='prolink_market', process_request='handle_cookie'),
        Rule(LinkExtractor(allow=('/list\?', ), ), callback='check_response', follow=True, process_links='prolink_list', process_request='handle_cookie'),
        Rule(
            LinkExtractor(allow=('/', '/index.htm'),
                allow_domains=("tmall.com",),
                deny_domains=("www.tmall.com",),
            ),
            callback='parse_brand',
            process_links='prolink_brand', process_request='handle_cookie'),
        # Extract links matching 'item.php' and parse them with the spider's method parse_item
        Rule(LinkExtractor(allow=('item\.htm', ), allow_domains=("detail.tmall.com"), deny_domains=("chaoshi.detail.tmall.com",), ), process_links='prolink_item', callback='parse_item'),
    )

    def check_response(self, response):
        # self.log("response[%s]: %s" % (response.url, response.headers))
        pass

    def prolink_market(self, links):
        """
        http://www.tmall.com/go/market/promotion-act/xiangbaofenqigoudierqi.php
        """
        # self.log("market found:%s" % links)
        for l in links:
            l.url=l.url.split('?')[0]
        # self.log("market link processed:%s" % links)
        return links

    def prolink_list(self, links):
        """
        page down:s=60
        http://list.tmall.com/search_product.htm?&vmarket=48386
        http://list.tmall.com/search_product.htm?sort=s&cat=51024008
        http://list.tmall.com/search_product.htm?sort=s&cat=51024008
        http://list.tmall.com/search_product.htm?brand=3713796&q=MCM&sort=s
        """
        for l in links:
            url = l.url
            qparam=filter(lambda x:any(x.startswith(pre) for pre in ["vmarket=","sort=","cat=","brand=","q=","s="]), url[url.index('?')+1:].split('&'))
            if(len(qparam)>0):
                l.url= "%s?%s" % (url[:url.index('?')], qparam[0])
        # self.log("search link processed:%s" % links)
        return links

    def prolink_brand(self, links):
        """
        or:http://xxx.tmall.com/index.htm
        http://memxiangbao.tmall.com/
        http://qiwang.tmall.com/
        http://panbixuan.tmall.com/
        http://panbixuan.tmall.com/
        """
        # self.log("market found:%s" % links)
        for l in links:
            l.url=l.url.split('?')[0]
        # self.log("market link processed:%s" % links)
        return links

    def parse_brand(self, response):
        """
        decide wether this xxx.tmall.com is a brand shop:
        http://yintai.tmall.com
            or a tmall channel:
http://jia.tmall.com

        """
        if len(response.css("#shopExtra")) == 0:
            self.log("DENIED brand url:%s" % response.url)
            return []

        return self._requests_to_follow(response)

    def prolink_item(self, links):
        """
        http://detail.tmall.com/item.htm?id=13505747865
        """
        for l in links:
            url = l.url
            qparam=filter(lambda x:x.startswith("id="), url[url.index('?')+1:].split('&'))
            if(len(qparam)>0):
                l.url= "%s?%s" % (url[:url.index('?')], qparam[0])
        #self.log("item link processed:%s" % links)
        return links

    def handle_cookie(self, request):
        # auto handled?
        # url_stack
        if not request.meta:
            request.meta={}
        if not request.meta.get('url_stack'):
            request.meta['url_stack']=[]
        #request.meta['url_stack'].append({'url':request.url, 'text':request.meta['link_text']})
        #self.log("handle_cookie: meta:%s" % request.meta)
        return request

    def parse_item(self, response):
        self.log("item response meta:%s" % response.meta)
        if len(response.css(".errorPage")) > 0:
            self.log('item NOT FOUND page: %s' % response.url)
            return

        self.log('Hi, this is an item page! %s' % response.url)
        item = ProductItem()
        image_urls=response.css("#J_UlThumb img::attr('src')").extract()
        item['image_urls'] = [url.replace('60x60','430x430') for url in image_urls]
        #http://img02.taobaocdn.com/imgextra/i2/2118504882/TB285zRaVXXXXazXXXXXXXXXXXX_!!2118504882.jpg_50x50.jpg
        item['name'] = response.css("div.tb-detail-hd h1::text").extract()
        item['price'] = response.css("div.tb-property-cont em.tb-rmb-num::text").extract()
        item['url'] = response.url
        item['id'] = response.url.split('id=')[1]
        item['url_stack'] = response.meta.get('url_stack')
        props = [x.split(u":\xa0") for x in response.css("#J_AttrUL li::text").extract()]
        pmap = {}
        for p in props:
            if(len(p)==2):
                pmap[p[0]]=p[1]

        item['material'] = prop_get(pmap, [u'材质', u'面料', u'面料材质', u'鞋面材质'])
        item['collar'] = prop_get(pmap, [u'领子'])
        item['thickness'] = prop_get(pmap, [u'厚薄'])
        item['pattern'] = prop_get(pmap, [u'图案'])
        item['style'] = prop_get(pmap, [u'款式'])
        item['brand'] = prop_get(pmap, [u'品牌'])
        item['sleeve'] = prop_get(pmap, [u'袖长'])
        item['zipper'] = prop_get(pmap, [u'衣门襟'])
        item['skirt'] = prop_get(pmap, [u'裙长'])
        item['shoe_head'] = prop_get(pmap, [u'鞋头款式'])
        item['heel'] = prop_get(pmap, [u'鞋跟'])
        item['handle'] = prop_get(pmap, [u'提拎部件类型'])
        item['girdle'] = prop_get(pmap, [u'肩带样式'])
        item['hardness'] = prop_get(pmap, [u'箱包硬度'])
        item['shape'] = prop_get(pmap, [u'形状'])
        item['case_handle'] = prop_get(pmap, [u'有无拉杆'])
        item['wheel'] = prop_get(pmap, [u'滚轮样式'])
        return item


