### 신문고 사이트 민원 크롤러

https://www.epeople.go.kr/nep/pttn/gnrlPttn/pttnSmlrCaseList.npaid
사이트의 데이터를 분산 크롤합니다.

### library
- ray
- requests
- lxml 
- pandas

### run script
```
python crawl_sinmungo.py
```

### crawl data format
- 'title': 민원 질문 타이틀
- 'question': 질문 내용
- 'answer': 답변 내용
- 'agency': 처리기관
- 'datetime': 등록일자
- 'status_code': 반환 코드 (200: 성공, 500: 비공개처리로 답변 데이터 get을 할 수 없음)
### function explaination
```
@ray.remote
def start_crawl_sinmungo(i=1,page=20, cookie='JSESSIONID=F9d-is7ERKta3LgKQA33TbQ4.euser22'):
```
- page 첫번째 사이클에서 20개의 민원을 가져와서 처리
- cookie 는 오류가 날 경우, 직접 해당 사이트에 들어가 개발자도구>application tab > cookie값 확인 및 변경