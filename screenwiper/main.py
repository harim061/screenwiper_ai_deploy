from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from paddleocr import PaddleOCR
import numpy as np
from PIL import Image
import re
from datetime import datetime
import random
import aiohttp
import os
from io import BytesIO
import asyncio
from krwordrank.word import KRWordRank

app = FastAPI()

# PaddleOCR 인스턴스 생성
ocr = PaddleOCR(lang='korean')

class ImageUrl(BaseModel):
    imageUrl: str

async def perform_ocr(image: Image.Image):
    image_np = np.array(image)
    result = ocr.ocr(image_np, cls=True)
    return result

async def download_image_from_url(image_url: str) -> Image.Image:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                response.raise_for_status()
                content_type = response.headers.get('Content-Type')
                if not content_type or not content_type.startswith('image/'):
                    raise ValueError("URL이 이미지 파일이 아닙니다.")
                img = Image.open(BytesIO(await response.read()))
                img = img.convert('RGB')
                img.save('downloaded_image.jpg')  # 이미지 파일 저장하여 확인
                return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"이미지 다운로드 중 오류가 발생했습니다: {e}")

def format_ocr_result(ocr_results):
    lines = []
    current_line = []
    
    last_y = None
    tolerance = 10 # 줄 간격 허용 오차

    for bbox, (text, confidence) in ocr_results[0]:
        y_coord = bbox[0][1]

        if last_y is None or abs(last_y - y_coord) > tolerance:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = []

        current_line.append(text)
        last_y = y_coord
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines)

def remove_summary(text):
    hashtags = re.findall(r'#\S+', text)
    clean_text = re.sub(r'#\S+', '', text).strip()
    return clean_text, hashtags

def extract_summary(hashtags):
    if not hashtags:
        return "해쉬태그 없더"
    summary = random.choice(hashtags).strip()
    return summary

def extract_places(text):
    PLACE_KEYWORDS_PATTERN = r'\b(?:장소|주소)\b'
    FULL_ADDRESS_PATTERN = (
        r'\b(?:서울|부산|대구|인천|광주|대전|울산|경기|경상|전라|충청|제주도)\b' 
        r'\s*'  
        r'(?:[^\s]{1,4})'  
        r'\s*(?:\d+)?'  
        r'\s*(?:\S*)?'  
        r'(?:\s+(?:로|길))?'  
        r'\s*'  
        r'\s*(?:\d*)'  
    )
    PROVINCE_PATTERN = r'\b(?:서울시|서울|부산|대구|인천|광주|대전|울산|경기|경상|전라|충청|제주도)\b'

    if re.search(PLACE_KEYWORDS_PATTERN, text):
        text = re.sub(PLACE_KEYWORDS_PATTERN, '', text).strip()
        text = text.lstrip(':').strip()
        
    address_match = re.search(FULL_ADDRESS_PATTERN, text)
    if address_match:
        address = address_match.group().strip()
        address = address.lstrip(':').strip()
        return [address]
    
    province_match = re.search(PROVINCE_PATTERN, text)
    if province_match:
        return [province_match.group().strip()]
    
    return []


def parse_date(date_str):
    formats = [
        '%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y', '%y-%m-%d', '%Y년 %m월 %d일',
        '%Y%m%d'  # YYYYMMDD 형식 추가
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def extract_dates_and_events(text):
    date_patterns = [
        # r'\b(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
        # r'\b(\d{2}/\d{2}/\d{4})\b',  # MM/DD/YYYY or DD/MM/YYYY
        # r'\b(\d{2}\.\d{2}\.\d{4})\b',  # DD.MM.YYYY
        # r'\b(\d{2}-\d{2}-\d{2})\b',  # DD-MM-YY or YY-MM-DD
        # r'\b(\d{4}년 \d{1,2}월 \d{1,2}일)\b',  # YYYY년 MM월 DD일
        # r'\b(\d{8})\b',  # YYYYMMDD
        r'\b(\d{4}-\d{2}-\d{2})\s*[-~]?\s*(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD - YYYY-MM-DD
        r'\b(\d{8})\s*[-~]?\s*(\d{8})\b',  # YYYYMMDD - YYYYMMDD
        r'\b(\d{4}년 \d{1,2}월 \d{1,2}일)\s*[-~]?\s*(\d{4}년 \d{1,2}월 \d{1,2}일)\b'  # YYYY년 MM월 DD일 - YYYY년 MM월 DD일
    ]
    
    events = []
    lines = text.split('\n')
    
    for i in range(len(lines)):
        line = lines[i]
        for pattern in date_patterns:
            matches = re.findall(pattern, line)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        start_date = parse_date(match[0])
                        end_date = parse_date(match[1])
                    else:
                        start_date = parse_date(match)
                        end_date = start_date

                    if start_date:
                        event_name = ""
                        
                        
                        # 이전 줄에서 이벤트 이름 찾기
                        if i > 0:
                            event_name = lines[i-1].strip()
                        
                        # 현재 줄에서 날짜를 제외한 부분을 이벤트 이름에 추가
                        current_line_without_date = re.sub(pattern, '', line).strip()
                        if current_line_without_date:
                            event_name += " " + current_line_without_date if event_name else current_line_without_date
                        
                        date_range = f"{start_date} - {end_date}"
                        
                        events.append({
                            "name": event_name.strip(),
                            "date": date_range
                        })
    
    return events

def extract_operating_hours(text):
    OPERATING_HOURS_PATTERN = (
        r'(?:매일|월요일|화요일|수요일|목요일|금요일|토요일|일요일)?\s*(\d{1,2}):(\d{2})\s*(?:[-~]?\s*)\s*(\d{1,2}):(\d{2})|'  
        r'(?:오전|오후)?\s*(\d{1,2}):(\d{2})\s*(?:[-~]?\s*)(?:오전|오후)?\s*(\d{1,2}):(\d{2})|'  
        r'(매일|월요일|화요일|수요일|목요일|금요일|토요일|일요일)\s*(\d{1,2}):(\d{2})\s*(?:[-~]?\s*)\s*(\d{1,2}):(\d{2})'
    )
    
    matches = re.findall(OPERATING_HOURS_PATTERN, text)
    operating_hours = []

    for match in matches:
        match = [m for m in match if m]
        
        if len(match) == 4:
            start_time = f"{match[0]}:{match[1]}"
            end_time = f"{match[2]}:{match[3]}"
            operating_hours.append(f"{start_time} - {end_time}")
        
        elif len(match) == 6:
            start_period = match[0] if match[0] else ""
            end_period = match[4] if match[4] else ""
            start_time = f"{start_period} {match[1]}:{match[2]}" if start_period else f"{match[1]}:{match[2]}"
            end_time = f"{end_period} {match[3]}:{match[4]}" if end_period else f"{match[3]}:{match[4]}"
            operating_hours.append(f"{start_time} - {end_time}")
        
        elif len(match) == 8:
            day = match[0]
            start_time = f"{match[1]}:{match[2]}"
            end_time = f"{match[3]}:{match[4]}"
            operating_hours.append(f"{day} {start_time} - {end_time}")
    
    return operating_hours


def analyze_sentence_for_category(sentence):
    # 날짜 및 일정 먼저 추출 시도
    extracted_events = extract_dates_and_events(sentence)
    
    if extracted_events:
        return 2, extracted_events  # 일정인 경우 카테고리 2로 분류
    
    # 영업시간 추출 시도
    operating_hours = extract_operating_hours(sentence)
    
    if operating_hours:
        return 1, operating_hours  # 영업시간인 경우 카테고리 1로 분류
    
    # 장소 정보 추출 시도
    extracted_places = extract_places(sentence)
    
    if extracted_places:
        return 1, extracted_places  # 장소인 경우 카테고리 1로 분류
    
    return 3, None  # 그 외는 카테고리 3으로 분류

# 텍스트에서 숫자 제거
def remove_numbers(text):
    return re.sub(r'\d+', '', text)

def extract_keywords(texts, min_count=1, max_length=20, beta=0.95, max_iter=10):
    wordrank_extractor = KRWordRank(min_count=min_count, max_length=max_length)
    keywords, rank, graph = wordrank_extractor.extract(texts, beta, max_iter)
    
    return keywords if keywords is not None else {}

def generate_category_1_response( image_url, formatted_text, extracted_places, hashtags):
    operating_hours = extract_operating_hours(formatted_text)
    summary = extract_summary(hashtags) if hashtags else ""
    filename = os.path.basename(image_url)
    
    # extracted_places를 문자열로 변환
    # places_str = " ".join([str(place) for place in extracted_places])
    
    return {
        "categoryId": 1,
        "title": "카카오지도 연결",
        "address": extracted_places[0],
        "operatingHours": operating_hours,
        "summary": summary,
        "photoName": filename,
        "photoUrl": image_url
    }


def generate_category_2_response( image_url, formatted_text,extracted_events):
    filename = os.path.basename(image_url)

    # 키워드 추출
    clean_text = remove_numbers(formatted_text)
    texts = clean_text.split('\n')

    keywords = extract_keywords(texts)
    top_keywords = [word for word, r in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:3]]
    keywords_summary = ' '.join(top_keywords)

    return {
        "categoryId": 2,
        "title": keywords_summary,
        "list": extracted_events,
        "photoName": filename,
        "photoUrl": image_url
    }

def generate_category_3_response( image_url, formatted_text):
    filename = os.path.basename(image_url)
    return {
        "categoryId": 3,
        "title": "아쥑",
        "summary": " ".join(text_results),
        "photoName": filename,
        "photoUrl": image_url
    }


@app.post("/analyze_image")
async def analyze_image(image_url: ImageUrl):
    image_url = image_url.imageUrl

    if not image_url:
        raise HTTPException(status_code=400, detail="이미지 URL이 제공되지 않았습니다.")
    
    img = await download_image_from_url(image_url)
    
    try:
        # OCR 수행 - 시간 제한 15초
        ocr_results = await asyncio.wait_for(perform_ocr(img), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="분석 실패: 시간이 초과되었습니다.")
    

    # OCR 결과 텍스트 추출 및 줄바꿈 포맷 적용
    formatted_text = format_ocr_result(ocr_results)


    # 해시태그
    formatted_text, hashtags = remove_summary(formatted_text)
    print(formatted_text)

    extracted_events = extract_dates_and_events(formatted_text)
    
    if extracted_events:
        print("Extracted events:", extracted_events)
        response_data = generate_category_2_response( image_url, formatted_text,extracted_events)
    else:
        extracted_places = extract_places(formatted_text)
        if extracted_places:
            print("Extracted places:", extracted_places)
            response_data = generate_category_1_response(image_url, formatted_text, extracted_places, hashtags)
        else:
            print("No events or places found. Categorizing as 3.")
            summarized_text = formatted_text
            response_data = generate_category_3_response(image_url,formatted_text)
    
    print("Response category:", response_data["categoryId"])
    return JSONResponse(content=response_data)

@app.get("/")
async def index():
    return {"message": "Welcome to the OCR API"}

if __name__ == "__main__":
    import uvicorn
    # 8080
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="debug")
