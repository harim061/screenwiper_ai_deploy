from flask import Flask, render_template, request, jsonify
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image
import re
from datetime import datetime
import random
import requests
from io import BytesIO

app = Flask(__name__)

# &PaddleOCR 인스턴스 생성
ocr = PaddleOCR( lang='korean') 

def perform_ocr(image):
    """이미지에서 OCR 수행"""

    image_np = np.array(image)
    # OCR 수행
    result = ocr.ocr(image_np, cls=True)
    return result

def download_image_from_url(image_url):
    try:
        # 이미지 다운로드
        response = requests.get(image_url)
        response.raise_for_status()  # 다운로드 시 HTTP 오류 발생 시 예외 발생
        
        # Content-Type 헤더로 이미지 파일인지 확인
        content_type = response.headers.get('Content-Type')
        if not content_type or not content_type.startswith('image/'):
            raise ValueError("URL이 이미지 파일이 아닙니다.")

        # 이미지 바이트로 변환
        img = Image.open(BytesIO(response.content))

        # 이미지를 RGB로 변환 (OCR 처리를 위해 필요할 수 있음)
        img = img.convert('RGB')

        return img

    except requests.exceptions.RequestException as e:
        print(f"이미지 다운로드 중 오류가 발생했습니다: {e}")
        return None
    except (ValueError, IOError) as e:
        print(f"이미지 처리 중 오류가 발생했습니다: {e}")
        return None

# &줄바꿈 함수
def format_ocr_result(ocr_results):
    lines = []
    current_line = []
    
    last_y = None
    tolerance = 10 # 줄 간격 허용 오차

    for bbox, (text, confidence) in ocr_results[0]:
        # 현재 텍스트의 y 좌표
        y_coord = bbox[0][1]

        # 새 줄을 시작할 때 기준
        if last_y is None or abs(last_y - y_coord) > tolerance:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = []

        current_line.append(text)
        last_y = y_coord
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines)

# &카테고리1 (장소)
def extract_places(text):
    # 장소/주소 관련 단어를 체크하기 위한 패턴
    PLACE_KEYWORDS_PATTERN = r'\b(?:장소|주소)\b'
    
    # 주소 패턴 정의
    FULL_ADDRESS_PATTERN = (
        r'\b(?:서울|부산|대구|인천|광주|대전|울산|경기|경상|전라|충청|제주도)\b'  # 광역시/도 (필수)
        r'\s*'  # 광역시/도 뒤에 빈칸 허용
        r'(?:[^\s]{1,4})'  # 최대 4칸 시군구읍면리동 이름 (필수)
        r'\s*(?:\d+)?'  # 번지 부분 (선택적)
        r'\s*(?:\S*)?'  # 나머지 주소 부분 (선택적)
        r'(?:\s+(?:로|길))?'  # 도로명 (로, 길) (선택적)
        r'\s*'  #빈칸 허용
        r'\s*(?:\d*)'  # 도로명 뒤의 숫자 (선택적)
    )
    
    PROVINCE_PATTERN = r'\b(?:서울시|서울|부산|대구|인천|광주|대전|울산|경기|경상|전라|충청|제주도)\b'

    # '장소'나 '주소'라는 단어가 포함된 경우 우선 처리
    if re.search(PLACE_KEYWORDS_PATTERN, text):
        # '장소' 또는 '주소'라는 단어가 포함된 부분을 제거
        text = re.sub(PLACE_KEYWORDS_PATTERN, '', text).strip()
        text = text.lstrip(':').strip()
        
    # 주소 추출 시도
    address_match = re.search(FULL_ADDRESS_PATTERN, text)
    if address_match:
        address = address_match.group().strip()
        
        # ':' 제거
        address = address.lstrip(':').strip()
        
        return [address]
    
    # 광역시/도만 있는 경우를 처리
    province_match = re.search(PROVINCE_PATTERN, text)
    if province_match:
        return [province_match.group().strip()]
    
    return []

# &카테고리 2 (날짜)
def extract_dates_and_events(text):
    date_patterns = [
        r'\b(\d{4}-\d{2}-\d{2})\b',         # YYYY-MM-DD
        r'\b(\d{2}/\d{2}/\d{4})\b',         # MM/DD/YYYY
        r'\b(\d{2}\.\d{2}\.\d{4})\b',       # DD.MM.YYYY
        r'\b(\d{2}-\d{2}-\d{2})\b',         # DD-MM-YY
        r'\b(\d{4}년 \d{1,2}월 \d{1,2}일)\b'  # YYYY년 MM월 DD일
    ]
    
    dates_and_events = []

    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # 날짜 형식 정규화 및 변환
            try:
                if re.match(r'\d{4}-\d{2}-\d{2}', match):  # YYYY-MM-DD
                    date_obj = datetime.strptime(match, '%Y-%m-%d')
                elif re.match(r'\d{2}/\d{2}/\d{4}', match):  # MM/DD/YYYY
                    date_obj = datetime.strptime(match, '%m/%d/%Y')
                elif re.match(r'\d{2}\.\d{2}\.\d{4}', match):  # DD.MM.YYYY
                    date_obj = datetime.strptime(match, '%d.%m.%Y')
                elif re.match(r'\d{2}-\d{2}-\d{2}', match):  # DD-MM-YY
                    date_obj = datetime.strptime(match, '%d-%m-%y')
                elif re.match(r'\d{4}년 \d{1,2}월 \d{1,2}일', match):  # YYYY년 MM월 DD일
                    date_obj = datetime.strptime(match, '%Y년 %m월 %d일')
                else:
                    continue
                date_str = date_obj.strftime('%Y-%m-%d')
                
                # 일정 이름을 날짜가 포함된 텍스트에서 추출
                event_name = text.replace(date_str, '').strip()
                
                if event_name:  # 일정 이름이 비어있지 않은 경우
                    dates_and_events.append({"name": event_name, "date": date_str})
            
            except ValueError:
                pass
    
    return dates_and_events

# &카테고리 1 (요약 => 해시태그)
def remove_summary(text):
    hashtags = re.findall(r'#\S+', text)
    clean_text = re.sub(r'#\S+', '', text).strip()
    return clean_text, hashtags

# &카테고리 1 (랜덤 해시태그 설정)
def extract_summary(hashtags):
    if not hashtags:  
        return "해쉬태그 없더"
    summary = random.choice(hashtags).strip()
    return summary


# &카테고리1 (시간)
def extract_operating_hours(text):
    # Updated 영업 시간 정규식 패턴
    OPERATING_HOURS_PATTERN = (
        r'(?:매일|월요일|화요일|수요일|목요일|금요일|토요일|일요일)?\s*(\d{1,2}):(\d{2})\s*(?:[-~]?\s*)\s*(\d{1,2}):(\d{2})|'  # 24시간 형식
        r'(?:오전|오후)?\s*(\d{1,2}):(\d{2})\s*(?:[-~]?\s*)(?:오전|오후)?\s*(\d{1,2}):(\d{2})|'  # 오전/오후 형식
        r'(매일|월요일|화요일|수요일|목요일|금요일|토요일|일요일)\s*(\d{1,2}):(\d{2})\s*(?:[-~]?\s*)\s*(\d{1,2}):(\d{2})'
    )
    
    matches = re.findall(OPERATING_HOURS_PATTERN, text)
    operating_hours = []

    for match in matches:
        # 매칭된 그룹을 확인하여 빈 문자열을 제외한 부분만 처리
        match = [m for m in match if m]
        
        if len(match) == 4:
            # 24시간 형식
            start_time = f"{match[0]}:{match[1]}"
            end_time = f"{match[2]}:{match[3]}"
            operating_hours.append(f"{start_time} - {end_time}")
        
        elif len(match) == 6:
            # 오전/오후 형식
            start_period = match[0] if match[0] else ""
            end_period = match[4] if match[4] else ""
            start_time = f"{start_period} {match[1]}:{match[2]}" if start_period else f"{match[1]}:{match[2]}"
            end_time = f"{end_period} {match[3]}:{match[4]}" if end_period else f"{match[3]}:{match[4]}"
            operating_hours.append(f"{start_time} - {end_time}")
        
        elif len(match) == 8:
            # 요일 형식
            day = match[0]
            start_time = f"{match[1]}:{match[2]}"
            end_time = f"{match[3]}:{match[4]}"
            operating_hours.append(f"{day} {start_time} - {end_time}")
    
    return operating_hours



# &카테고리 1에 대한 JSON 응답 생성
def generate_category_1_response(image,image_url, text_results, extracted_places,hashtags):

    operating_hours = extract_operating_hours(text_results)
    summary = extract_summary(hashtags)

    return {
        "categoryId": 1,
        "title": "아직",  # !아직
        "address": " ".join(extracted_places), 
        "operatingHours": operating_hours, 
        "summary": summary, 
        "photoName": image.filename,
        "photoUrl": image_url 
    }

# &카테고리 2에 대한 JSON 응답 생성
def generate_category_2_response(image,image_url,extracted_events):
    
    return {
        "categoryId": 2, 
        "title": "아쥑", # !아직
        "list": extracted_events, 
        "photoName": image.filename,
        "photoUrl": image_url
    }

# &카테고리 3에 대한 JSON 응답 생성
def generate_category_3_response(image,image_url, text_results):
    """카테고리 3에 대한 JSON 응답 생성"""
    return {
        "categoryId": 3,
        "title": "아쥑", # !아직
        "summary": " ".join(text_results),  # !카테고리 3에 요약이 필요할 경우 처리 필요  
        "photoName": image.filename,
        "photoUrl":image_url
    }



@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    
    # URL 파라미터 받기
    image_url = request.form.get('imageUrl')
    if not image_url:
        return jsonify({'error': '이미지 URL이 제공되지 않았습니다.'}), 400
    
    # 이미지 다운로드
    img = download_image_from_url(image_url)
    if img is None:
        return jsonify({'error': '이미지 다운로드에 실패했습니다.'}), 400
    
    
    # OCR 수행
    ocr_results = perform_ocr(img)
    
    # OCR 결과 텍스트 추출 및 줄바꿈 포맷 적용
    formatted_text = format_ocr_result(ocr_results)

    # 해시태그
    formatted_text,hashtags = remove_summary(formatted_text)

    sentences = formatted_text.split('\n')

    # &날짜 추출 및 정보 저장
    # &장소 정보 추출
    extracted_places = []
    extracted_events = []


    for sentence in sentences:
        
        # &카테고리2 events
        extracted_events.extend(extract_dates_and_events(sentence))
        

        # &카테고리1 address 
        address_extracted = False    
        places = extract_places(sentence)

        if places:
            extracted_places.extend(places)
            address_extracted = True
        
        if address_extracted:
            continue
        

    # &카테고리 결정 
    if extracted_places:
        category_id = 1
    elif extracted_events:
        category_id = 2
    else:
        category_id = 3
    
    # &return 
    if category_id == 1:
        response_data = generate_category_1_response(img,image_url, formatted_text, extracted_places,hashtags)
    elif category_id == 2:
        response_data = generate_category_2_response(img,image_url,extracted_events)
    else:
        response_data = generate_category_3_response(img,image_url, formatted_text)
    
    return jsonify(response_data)


@app.route("/")
def index():
    return render_template('index.html')



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)