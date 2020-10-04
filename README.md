# NewsCrawler with multiproc/threads
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Forked from lumyjuwon/KoreaNewsCrawler
  lumyjuwon님의 KoreaNewsCrawler를 참고하여 멀티쓰레드/프로세스를 더 활용할 수 있는 크롤러를 만들었습니다. 

## Method
  
* **getTitles(category, startyear, startmonth, endyear, endmonth, process_size, getter_threads)**
  
 이 메서드는 기사의 제목을 크롤링하는 메서드입니다.
 리턴값은 다음 형태의 정보를 배열로 지닙니다.

```
{
  'date': '2020.05.28. 오전 11:21', 
  'writing': '데일리안', 
  'url': 'http://news.naver.com/main/list.nhn?mode=LSD&mid=sec&listType=title&sid1=100&date=20200528&page=43', 
  'title': '<포토> 원내대책회의 주재하는 김태년', 
  'href': 'https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=100&oid=119&aid=0002404281'
}
```

  
## Example
```
from newsCrawler import NewsCrawler

Crawler = NewsCrawler()  
# param: 카테고리, 시작연도, 시작월, 끝연도, 끝월, 프로세스 개수, 수집 스레드 개수
ret = Crawler.getTitles('정치', 2020, 5, 2020, 6, 4, 10)
```
## Multi Process 안내
  크롤링 작업은 크게 두 가지 단계로 나누어집니다.
  첫 번째는 네트워크를 이용한 html 페이지 수집 단계,
  두 번째는 수집된 페이지를 데이터로 가공하는 가공 단계입니다.
  이에 멀티프로세서를 적절히 활용하기 위해 다음 구조로 변경하였습니다.
  
  * 메인 프로세스는 n개의 수집 프로세스를 생성합니다.
  * 각 수집 프로세스는 다시 m개 만큼의 네트워크 수집 스레드를 이용해 병렬 수집합니다.
  * 수집이 완료되면 가공 프로세스를 생성하여 가공합니다.
  
  n은 프로세스의 개수입니다. 가공 프로세스의 개수와 동일하며, 각 프로세스는
  입력 범위(수집할 범위)를 n만큼 나누어 작업합니다.
  
  m은 프로세스 내 수집 스레드의 개수입니다.
  크롤링시에는 연속된 네트워크 환경이 아니라, 지속적으로 다른 url에 접근하기 때문에
  네트워크 속도보다 컴퓨팅 속도에 의존할 수 있습니다. 때문에 멀티 스레드를 이용합니다.


  
  
 
## License
 Apache License 2.0
 
