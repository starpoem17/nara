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

    def test_document_guidance_does_not_open_eligibility(self):
        for guidance in [
            '※ 입찰참가자격의 자격요건을 확인할 수 있는 면허증 등 첨부',
            '※ 입찰참가자격 등록은 입찰참가등록 전일까지 완료해야 함',
            '3) 입찰참가자격상의 중소기업확인서 1부',
            '입찰참가자격: 등록증 사본 첨부',
        ]:
            with self.subTest(guidance=guidance):
                result=judge(record(guidance+'\n최근 3년 실적 3억원 이상 기재'))
                self.assertEqual(result['eligibility_sections'],0)
                self.assertFalse(any(v['위반여부'] for v in result['judgments'].values()))

    def test_heading_scope_notes_and_guidance_inside_eligibility(self):
        for heading in ['3. 입찰참가자격 ※ 공동수급 허용',
                        '입찰참가자격 (아래 조건을 모두 충족)',
                        '입찰 참가자격 및 방법',
                        '입찰참가자격 : 다음 조건을 모두 충족하는 자',
                        '※ 입찰참가자격은 아래 조건을 모두 충족할 경우로 한정합니다.']:
            with self.subTest(heading=heading):
                text=(heading+'\n※ 입찰참가자격 등록증 사본 첨부\n'
                      '가. 실적 3억원 이상인 업체')
                result=judge(record(text))
                self.assertEqual(result['eligibility_sections'],1)
                self.assertEqual([v['위반여부'] for v in result['judgments'].values()],[1,1])

    def test_form_and_evaluation_boundaries_exclude_following_clauses(self):
        for boundary in ['【별지서식 7-7】','【서식 11】','[서식 10호]',
                         '서식 10호','정량적 평가','정량적 평가항목 및 배점(20점)',
                         '가. 평가항목 및 배점','유사용역 수행실적 평가기준']:
            with self.subTest(boundary=boundary):
                text=('입찰참가자격\n중소기업인 업체\n'+boundary+
                      '\n※ 입찰참가자격의 면허증 사본 첨부\n'
                      '최근 3년 수행실적 3억원 이상 기재')
                result=judge(record(text))
                self.assertFalse(any(v['위반여부'] for v in result['judgments'].values()))
                self.assertEqual(result['candidates'],[])

    def test_boundary_preserves_prior_requirement_and_later_real_heading(self):
        text=('입찰참가자격\n실적 5천만원 이상인 업체\n'
              '【서식 11】\n실적 3억원 이상 기재\n'
              '입찰참가자격 (추가 요건)\n실적 6천만원 이상인 업체')
        result=judge(record(text))
        self.assertEqual([c['amount'] for c in result['candidates']],[50_000_000,60_000_000])
        self.assertEqual([v['위반여부'] for v in result['judgments'].values()],[1,0])

    def test_form_reference_does_not_exclude_real_requirement(self):
        text='입찰참가자격\n가. 실적 3억원 이상인 업체 (증빙은 【서식 11】로 제출)'
        result=judge(record(text))
        self.assertEqual([v['위반여부'] for v in result['judgments'].values()],[1,1])

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

    def test_deadline_qualification_sentence_does_not_close_section(self):
        for sentence in [
            '가. 입찰서 제출마감일 전일까지 아래의 자격을 모두 갖춘 자이어야 합니다.',
            '나. 제안서 제출 마감일 이전에 다음 자격을 구비한 업체',
        ]:
            with self.subTest(sentence=sentence):
                text=('2. 입찰참가자격\n'+sentence+
                      '\n① 실적 1억 5천만원 이상인 업체\n3. 제출서류')
                self.assertEqual([v['위반여부'] for v in judge(record(text))['judgments'].values()],[1,1])

    def test_child_numbering_keeps_requirements_but_next_section_closes(self):
        for heading,children,next_heading in [
            ('3. 입찰참가자격',['1)','2)'],'4. 사업일정'),
            ('Ⅱ. 입찰참가자격',['1.','2.'],'Ⅲ. 사업일정'),
            ('3) 입찰참가자격',['가.','나.'],'4) 사업일정'),
        ]:
            with self.subTest(heading=heading):
                text=(heading+'\n'+children[0]+' 중소기업인 업체\n'+
                      children[1]+' 실적 1억 5천만원 이상인 업체\n'+
                      next_heading+'\n실적 5억원 이상 기재')
                result=judge(record(text))
                self.assertEqual([c['amount'] for c in result['candidates']],[150_000_000])
                self.assertEqual([v['위반여부'] for v in result['judgments'].values()],[1,1])

    def test_submission_heading_still_closes_section(self):
        for heading in ['가. 입찰서 제출마감일','나. 제안서 제출 안내']:
            with self.subTest(heading=heading):
                result=judge(record('입찰참가자격\n중소기업\n'+heading+'\n실적 3억원 이상 기재'))
                self.assertEqual(result['candidates'],[])

    def test_wrapped_condition(self):
        text='2. 입찰참가자격\n가. 최근 3년 실적이\n1억 5천만원 이상인 업체\n나. 중소기업\n3. 제출서류'
        self.assertEqual(judge(record(text))['judgments']['v3']['위반여부'],1)

if __name__=='__main__':unittest.main()
