from Naver_Articrawler.newsCrawler import NewsCrawler

Crawler = NewsCrawler()

if __name__ == '__main__':
    ret = Crawler.getTitles('정치', 2020, 5, 2020, 5, 8, 10)