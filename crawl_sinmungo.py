import ray # 분산처리
import requests
import re
from lxml import html
import pandas as pd

def get_cookie(): # TODO 쿠키 사용하기
    url = 'https://www.epeople.go.kr/nep/pttn/gnrlPttn/pttnSmlrCaseList.npaid'
    res = requests.get(url)
    data = res.cookies.get_dict()
    return data['JSESSIONID']


@ray.remote
def start_crawl_sinmungo(i=1,page=20, cookie='JSESSIONID=F9d-is7ERKta3LgKQA33TbQ4.euser22'):
    
    url = 'https://www.epeople.go.kr/nep/pttn/gnrlPttn/pttnSmlrCaseList.npaid' # 건의 리스트 url
    detail_url = 'https://www.epeople.go.kr/nep/pttn/gnrlPttn/pttnSmlrCaseDetail.npaid' # 건의 1개의 내용관련 url
    title_list = []
    agency_list = []
    date_list = []
    question_list = []
    answer_list = []
    status_code_list = []

    form_data = {
        'pageIndex':i,
        'rqstStDt': '2014-01-01', # 원하는 기간 설정
        'rqstEndDt': '2021-06-09',
        'recordCountPerPage': page
    }
    headers={
        'Cookie':cookie
    }
    # 신문고 건의 리스트 가져오기 
    res = requests.post(url,headers=headers, data=form_data)
    root = html.fromstring(res.text.strip())
    rows = root.xpath('//table[contains(@class, tbl)]/tbody/tr')

    # 건의 타이틀
    title = [i.xpath('.//td[@class="left"]/a/text()')[0] for i in rows]
    result = [i.xpath('.//td/text()') for i in rows]
    title_list += title
    # 처리기관
    agency = [i[1] for i in result]
    agency_list += agency
    # 등록일
    date = [i[2] for i in result]
    date_list+= date
    # 내용을 가져오기 위한 코드들 저장
    detail_code = [re.sub('javaScript:fn_detail|;|\(|\)|\'','',i.xpath('.//td/a/@onclick')[0]) for i in rows] # contents
    ep_union_sn,duty_sctn_nm = [],[]
    for code in detail_code:
        sn, nm =tuple(map(str, code.split(',')))[1:]
        ep_union_sn.append(sn)
        duty_sctn_nm.append(nm)


    for idx in tqdm(range(page)):

        headers={
            'Cookie':cookie
        }
        form_data = {
            'epUnionSn': ep_union_sn[idx],
            'rqstStDt': '2014-01-01', # 원하는 기간 설정
            'rqstEndDt': '2021-06-09',
            'dutySctnNm':duty_sctn_nm[idx],
            '_csrf': '018df459-bfe7-4639-9667-0da86f242d89'

        }
        res = requests.post(detail_url, headers=headers, data=form_data)
        if res.status_code ==200:
            # 신문고 민원 사이트가 들어가지면

            root=html.fromstring(res.text.strip())

            # 질문 내용 
            question_content = ' '.join([i.strip() for i in root.xpath('//div[@class="samC_c"]/text()')])

            # 답변 내용
            answer = ' '.join([i.strip() for i in root.xpath(
                        '//div[@class="samBox ans"]'+
                          '/div[@class="sam_cont"]'+\
                          '/div[@class="samC_top"]/*/text()|//div[@class="samBox ans"]'+
                          '/div[@class="sam_cont"]'+\
                          '/div[@class="samC_top"]/text()|div[@class="samBox ans"]'+
                          '/div[@class="sam_cont"]'+\
                          '/div[@class="samC_top"]/span/span/span/text()')]).replace(u'\xa0', u' ')
            question_list.append(question_content)
            answer_list.append(answer)
            status_code_list.append(res.status_code)
        elif res.status_code ==500:
            # 비공개 처리로 들어가지 못할때
            # print('500', title[idx])
            # 타이틀, 관련부처, 등록일만 저장, 질문내용, 답변내용은 None 으로
            question_list.append(None)
            answer_list.append(None)
            status_code_list.append(res.status_code)
        else:

            # 그외 cookie 값 오류로 권한 에로 403 결과가 나올때, 쿠키 변경해야함.
            print('error {}'.format(res.status_code), title[idx])

            return False
    return [title_list,question_list,answer_list,agency_list,date_list,status_code_list]
if __name__ == '__main__':
    ray.init()
    cookie = 'JSESSIONID='+get_cookie() # cookies 를 직접 넣어야함

    results = [start_crawl_sinmungo.remote(i=idx, page=200) for idx in range(1,100)]
    contents = ray.get(results)
    title_list, question_list, answer_list, agency_list, date_list, status_code_list = [],[],[],[],[],[]
    for i in contents:
        title_list += i[0]
        question_list += i[1]
        answer_list += i[2]
        agency_list += i[3]
        date_list += i[4]
        status_code_list += i[5]

    data = {
        'title': title_list,
        'question': question_list,
        'answer': answer_list,
        'agency': agency_list,
        'datetime':date_list,
        'status_code':status_code_list
    }

    df = pd.DataFrame(data)
    df.to_csv('results.csv', index=False)
    print('Finished crawl data number {}'.format(len(df)))
