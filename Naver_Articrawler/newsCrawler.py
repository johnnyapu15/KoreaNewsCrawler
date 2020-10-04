#!/usr/bin/env python
# -*- coding: utf-8, euc-kr -*-

from time import sleep, time
from bs4 import BeautifulSoup
from threading import Thread, current_thread
from multiprocessing import Process, Queue, Pool
from copy import deepcopy
import os
import platform
import calendar
import requests
import re


class NewsCrawler(object):
    def __init__(self):
        self.categories = {'정치': 100, '경제': 101, '사회': 102, '생활문화': 103, '세계': 104, 'IT과학': 105, '오피니언': 110,
                           'politics': 100, 'economy': 101, 'society': 102, 'living_culture': 103, 'world': 104, 'IT_science': 105, 'opinion': 110}
        self.needs = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"    
            }
        self.stat = {}
    def initStat(self, stat_name):
        got = self.stat.get(stat_name)
        if got != None:
            self.stat[stat_name] = None
    def addStat(self, stat_name, data):
        got = self.stat.get(stat_name)
        if got == None:
            self.stat[stat_name] = []
        self.stat[stat_name].append(data)
    def getStat(self, stat_name, rounding = 2):
        got = self.stat.get(stat_name)
        if got == None:
            return -1
        return round(sum(got) / len(got), rounding)
    def gettings(self, urls, q, n = 5):
        ths = []
        tmpQ = Queue()
        num = int(len(urls) / n) + 1
        for i in range(n):
            ths.append(Thread(target=self.getting, args=(urls[i * num: (i+1)*num], tmpQ)))
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        ret = []
        for i in range(n):
            ret.extend(tmpQ.get())
        q.put(ret)
        del ths, tmpQ, num
        
    def getting(self, urls, q):
        ret = []
        for url in urls:
            d = requests.get(url, headers=self.needs).content
            ret.append({
                'url':url,
                'data':d
            })
            del d
        if q != None:
            q.put(ret)
        return ret

    def analysing(self, func, q):
        data = q.get()
        q.put(func(data))

    def getTitles(self, cat, stY, stM, enY, enM, process_size = 2, getter_threads = 5):
        catNum = self.categories[cat]
        dateUrls = self.getDateUrls(catNum, stY, stM, enY, enM)
        urls = self.startQ(dateUrls, self.findPageUrls, process_size, getter_threads)
        ret = self.startQ(urls, self.crawlTitles, process_size, getter_threads)
        return ret

    def tmpJob(self, urls, analFunc, dataQ, getter_threads):
        #print(analFunc.__name__ + ' MANAGER START ' + str(current_thread()) + ': urls: ' + str(len(urls)))
        gettingTime = time()
        tmpQ = Queue()
        proc = Process(target = self.gettings, args = (urls, tmpQ, getter_threads))
        proc.start()
        while(tmpQ.qsize() == 0):
            sleep(1)
        ret = tmpQ.get()
        gettingTime = time() - gettingTime
        
        proc = Process(target=analFunc, args=(ret, dataQ))
        proc.start()
        analTime = time()
        proc.join()
        analTime = time() - analTime
        proc.terminate()
        self.addStat('get', gettingTime)
        self.addStat('analyze', analTime)
        #print(analFunc.__name__ + ' MANAGER END ... ' + str(current_thread()) + ', [' + str(round(gettingTime, 2)) + ' / ' + str(round(analTime, 2)) + ']')

    def startQ(self, urls, analyzer, process_size = 2, getter_threads = 10):
        print('Starting\t' + analyzer.__name__ + '\tprocess size: ' + str(process_size) + ' / thread size: ' + str(getter_threads))
        dataQ = Queue()
        st = time()
        num = int(len(urls)/process_size)
        ths = []
        self.initStat('get')
        self.initStat('analyze')
        for i in range(process_size + 1):
            tmp = urls[i*num:(i+1)*num]
            th = Thread(target=self.tmpJob, args=(tmp, analyzer, dataQ, getter_threads))
            ths.append(th)
        ret = []
        for th in ths:
            th.start()
        for i in range(process_size + 1):
            while(dataQ.qsize() == 0):
                sleep(1)
            ret.extend(dataQ.get())
        for th in ths:
            th.join()
        print('Done!\t\t' + analyzer.__name__ + '\twith ' + str(round(time() - st, 2)) + 's avg of getting / analyzing: (' + str(self.getStat('get')) + 's / ' + str(self.getStat('analyze')) + 's)')
        return ret

    @staticmethod
    def crawlTitles(requests, dataQ):
        post = []
        for request in requests:
            cnts = request['data']
            url = request['url']
            document = BeautifulSoup(cnts, 'html.parser')
            post_temp = document.select('.list_body li')
            for line in post_temp:
                line_a = line.select('a')[0]
                line_writing = line.select('.writing')[0].text
                line_date = line.select('.date')[0].text
                txt = line_a.text
                if txt != '':
                    post.append( {
                        'date':line_date,
                        'writing':line_writing,
                        'url':url,
                        'title':txt,
                        'href':line_a.get('href')
                    })
            del post_temp
        dataQ.put(post)
        return post
    @staticmethod
    def findPageUrls(requests, dataQ):
        made_urls = []
        for request in requests:
            cnts = request['data']
            url = request['url']
            document_content = BeautifulSoup(cnts, 'html.parser')
            headline_tag = document_content.find('div', {'class': 'paging'}).find('strong')
            regex = re.compile(r'<strong>(?P<num>\d+)')
            match = regex.findall(str(headline_tag))
            totalpage = int(match[0])
            url = url.replace('&page=10000', '')
            for page in range(1, totalpage + 1):
                made_urls.append(url + "&page=" + str(page))
        dataQ.put(made_urls)
        return made_urls
        
    @staticmethod
    def getDateUrls(category_num, start_year, start_month, end_year, end_month):
        made_urls = []
        category_url = "http://news.naver.com/main/list.nhn?mode=LSD&mid=sec&listType=title&sid1=" + str(category_num) + "&date="
        for year in range(start_year, end_year + 1):
            if start_year == end_year:
                year_startmonth = start_month
                year_endmonth = end_month
            else:
                if year == start_year:
                    year_startmonth = start_month
                    year_endmonth = 12
                elif year == end_year:
                    year_startmonth = 1
                    year_endmonth = end_month
                else:
                    year_startmonth = 1
                    year_endmonth = 12
            for month in range(year_startmonth, year_endmonth + 1):
                for month_day in range(1, calendar.monthrange(year, month)[1] + 1):
                    if len(str(month)) == 1:
                        month = "0" + str(month)
                    if len(str(month_day)) == 1:
                        month_day = "0" + str(month_day)
                    url = category_url + str(year) + str(month) + str(month_day)
                    made_urls.append(url + "&page=10000")
        return made_urls