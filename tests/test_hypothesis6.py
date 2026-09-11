import unittest
from nara.hypothesis6 import judge, money_value


def record(text, estimate=90_000_000, budget=100_000_000, law='국가계약법'):
    return {'id':'synthetic','meta':{'입찰추정가격':estimate,'배정예산금액':budget,
            '적용계약법':law,'업무구분':'일반용역','계약방법':'제한경쟁'},
            'docs':[{'doc_id':'doc','type':'공고','text':text}]}

class Hypothesis6Tests(unittest.TestCase):
    def test_korean_money(self):
        for text,value in [('3천만원',30_000_000),('1억 5천만원',150_000_000),
                           ('1.5억원',150_000_000),('50,000천원',50_000_000),
                           ('300백만원',300_000_000),('1억 5,000만원',150_000_000)]:
            self.assertEqual(money_value(text),value)

    def test_qualification_and_exact_evidence(self):
        r=record('3. 입찰 참가 자격\n\n가. 최근 5년간 실적이 1억 5천만원 이상인 업체\n\n4. 제출서류\n실적증명서')
        result=judge(r)
        self.assertEqual([result['judgments'][k]['위반여부'] for k in ('v2','v3')],[1,1])
        self.assertIn(result['judgments']['v3']['근거문구'],r['docs'][0]['text'])

    def test_budget_denominator_and_strict_boundaries(self):
        text='2. 입찰참가자격\n실적 1억원 이상인 업체\n3. 제출서류'
        self.assertEqual(judge(record(text))['judgments']['v3']['위반여부'],0)
        self.assertEqual(judge(record(text,budget=99_000_000))['judgments']['v3']['위반여부'],1)
        self.assertEqual(judge(record(text,estimate=230_000_000))['judgments']['v2']['위반여부'],0)

    def test_score_form_and_postcontract(self):
        for text in ['2. 평가표\n실적 3억원 이상: 5점',
                     '2. 입찰참가자격\n중소기업\n3. 평가표\n실적 3억원 이상: 5점',
                     '2. 입찰참가자격\n중소기업\n3. 서식\n실적 3억원 이상 기재',
                     '2. 입찰참가자격\n계약 후 실적 3억원 이상 보고',
                     '2. 입찰참가자격\n실적 3억원 이상 평가표 배점 5점']:
            self.assertEqual(sum(v['위반여부'] for v in judge(record(text))['judgments'].values()),0)

    def test_condition_scope_upper_bound(self):
        text='2. 입찰참가자격\n\n가. 자본금 10억원 이하\n\n나. 실적 3억원 이상인 업체\n3. 제출서류'
        self.assertEqual(judge(record(text))['judgments']['v2']['위반여부'],1)
        self.assertEqual(judge(record(text.replace('3억원 이상','3억원 이상 5억원 미만')))['judgments']['v2']['위반여부'],0)

    def test_unknown_and_unheaded(self):
        text='2. 입찰참가자격\n실적 3억원 이상인 업체\n3. 제출서류'
        result=judge(record(text,estimate=None,budget=None,law='미입력'))
        self.assertEqual(len(result['unknown_metadata']),3)
        self.assertFalse(any(x['위반여부'] for x in result['judgments'].values()))
        self.assertEqual(judge(record('평가에 필요한 실적 3억원 이상을 작성한다.'))['eligibility_sections'],0)

    def test_wrapped_condition(self):
        text='2. 입찰참가자격\n가. 최근 3년 실적이\n1억 5천만원 이상인 업체\n나. 중소기업\n3. 제출서류'
        self.assertEqual(judge(record(text))['judgments']['v3']['위반여부'],1)

if __name__=='__main__':unittest.main()
