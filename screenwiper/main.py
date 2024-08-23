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

def extract_dates_and_events(text):
    date_patterns = [
        r'\b(\d{4}-\d{2}-\d{2})\b',         
        r'\b(\d{2}/\d{2}/\d{4})\b',         
        r'\b(\d{2}\.\d{2}\.\d{4})\b',       
        r'\b(\d{2}-\d{2}-\d{2})\b',         
        r'\b(\d{4}년 \d{1,2}월 \d{1,2}일)\b'  
    ]
    
    dates_and_events = []

    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                if re.match(r'\d{4}-\d{2}-\d{2}', match):
                    date_obj = datetime.strptime(match, '%Y-%m-%d')
                elif re.match(r'\d{2}/\d{2}/\d{4}', match):
                    date_obj = datetime.strptime(match, '%m/%d/%Y')
                elif re.match(r'\d{2}\.\d{2}\.\d{4}', match):
                    date_obj = datetime.strptime(match, '%d.%m.%Y')
                elif re.match(r'\d{2}-\d{2}-\d{2}', match):
                    date_obj = datetime.strptime(match, '%d-%m-%y')
                elif re.match(r'\d{4}년 \d{1,2}월 \d{1,2}일', match):
                    date_obj = datetime.strptime(match, '%Y년 %m월 %d일')
                else:
                    continue
                date_str = date_obj.strftime('%Y-%m-%d')
                event_name = text.replace(date_str, '').strip()
                if event_name:
                    dates_and_events.append({"name": event_name, "date": date_str})
            
            except ValueError:
                pass
    
    return dates_and_events

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

def generate_category_1_response(image, image_url, text_results, extracted_places, hashtags):
    operating_hours = extract_operating_hours(text_results)
    summary = extract_summary(hashtags)
    filename = os.path.basename(image_url)
    return {
        "categoryId": 1,
        "title": "아직",
        "address": " ".join(extracted_places),
        "operatingHours": operating_hours,
        "summary": summary,
        "photoName": filename,
        "photoUrl": image_url
    }

def generate_category_2_response(image, image_url, extracted_events):
    filename = os.path.basename(image_url)
    return {
        "categoryId": 2,
        "title": "아쥑",
        "list": extracted_events,
        "photoName": filename,
        "photoUrl": image_url
    }

def generate_category_3_response(image, image_url, text_results):
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
    
    # OCR 수행
    ocr_results = await perform_ocr(img)
    
    # OCR 결과 텍스트 추출 및 줄바꿈 포맷 적용
    formatted_text = format_ocr_result(ocr_results)

    # 해시태그
    formatted_text, hashtags = remove_summary(formatted_text)

    sentences = formatted_text.split('\n')

    extracted_places = []
    extracted_events = []

    for sentence in sentences:
        extracted_events.extend(extract_dates_and_events(sentence))
        address_extracted = False    
        places = extract_places(sentence)
        if places:
            extracted_places.extend(places)
            address_extracted = True
        if address_extracted:
            continue

    if extracted_places:
        category_id = 1
    elif extracted_events:
        category_id = 2
    else:
        category_id = 3
    
    if category_id == 1:
        response_data = generate_category_1_response(img, image_url, formatted_text, extracted_places, hashtags)
    elif category_id == 2:
        response_data = generate_category_2_response(img, image_url, extracted_events)
    else:
        response_data = generate_category_3_response(img, image_url, formatted_text)
    
    return JSONResponse(content=response_data)

@app.get("/")
async def index():
    return {"message": "Welcome to the OCR API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="debug")
