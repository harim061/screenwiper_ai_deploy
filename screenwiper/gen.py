import re
from krwordrank.word import KRWordRank

# 분석할 텍스트
text = '''
전시
place _archive 5월 서울에서 꼭 가봐야 할 전시회 13곳을 소개
합니다+ 플레이스 아카이브
1<미래긍정:노먼 포스터 포스터 | 파트너스       
세계적인: 거장 건축가노먼 포스터를 국내에 처음 소개하는전
20240425 -20240721
서울중구덕수궁길61_서울시립미술관
2/길드는서로들
/서울시립미술관의 2024년 전시 의제인'건축'을관 통하는전
시로건축의본질적 속성을'관계맺기'를 통해가치와 경험을만드
는행위로 파악하고 '관계맺기'를 다양한 개념적 접근으로 살펴보
전시
[ 20240410 -20240707
서울 관악구 남부순환로 2076 - 서울시립 남서울미술관
3<까르띠에 시간의 결정
<까르띠에 컬렉션으로대표되는소장품 아카이브 자 료등300
여점에달하는작품을선보이는 대규모 전시
20240501 - 20240630
서울중구을지로281_DDP 아트홀 컨퍼런스홀        
4{서울:서울 어디에나있고 아무데도 없는강홍구의 서울
Y오랜 기간서울을 탐구해온작가 강홍구의 작업을  아카이브로
재구성한전시
20240502 - 20240804
서울 종로구 평창문화로 101_서물시립 미술아카이 브
5영롱함을 넘어서
/ 김창열의 작고: 3주기를 맞이하여 열리는 김창열 개인전
'''

# 텍스트에서 숫자 제거
def remove_numbers(text):
    return re.sub(r'\d+', '', text)

# 전처리된 텍스트
clean_text = remove_numbers(text)
texts = clean_text.split('\n')

# 1. 키워드 추출
def extract_keywords(texts, min_count=1, max_length=20, beta=0.95, max_iter=10):
    wordrank_extractor = KRWordRank(min_count=min_count, max_length=max_length)
    keywords, rank, graph = wordrank_extractor.extract(texts, beta, max_iter)
    
    return keywords if keywords is not None else {}

keywords = extract_keywords(texts)

top_keywords = [word for word, r in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:3]]
result_sentence = ' '.join(top_keywords)

print("Extracted Keywords as Sentence:")
print(result_sentence)