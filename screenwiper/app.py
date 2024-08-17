from flask import Flask, render_template, request, jsonify
import cv2
import easyocr
import numpy as np
from PIL import ImageFont, ImageDraw, Image
import base64
import io
import re
from hanspell import spell_checker
from datetime import datetime

app = Flask(__name__)

# easyocr Reader 인스턴스 생성
reader = easyocr.Reader(['ko', 'en'])

def perform_ocr(image):
    """이미지에서 OCR 수행"""
    return reader.readtext(image)

def encode_image_to_base64(image):
    """PIL 이미지를 base64로 인코딩"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def correct_text(text):
    try:
        # 한국어 맞춤법 검사
        checked_ko = spell_checker.check(text)
        corrected_ko = checked_ko.checked if hasattr(checked_ko, 'checked') else text
    except Exception as e:
        print(f"한국어 맞춤법 검사 중 오류 발생: {e}")
        corrected_ko = text
        
    return corrected_ko


def extract_dates(text):
    """텍스트에서 날짜를 추출하는 함수"""
    date_patterns = [
        r'\b(\d{4}-\d{2}-\d{2})\b',         # YYYY-MM-DD
        r'\b(\d{2}/\d{2}/\d{4})\b',         # MM/DD/YYYY
        r'\b(\d{2}\.\d{2}\.\d{4})\b',       # DD.MM.YYYY
        r'\b(\d{2}-\d{2}-\d{2})\b',         # DD-MM-YY
        r'\b(\d{4}년 \d{1,2}월 \d{1,2}일)\b'  # YYYY년 MM월 DD일
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # 날짜 형식 정규화 및 변환
            try:
                # 여러 형식에 대해 처리
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
                dates.append(date_obj.strftime('%Y-%m-%d'))
            except ValueError:
                pass
    return dates



@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    # 이미지 파일 받기
    if 'image' not in request.files:
        return jsonify({'error': '이미지 파일이 제공되지 않았습니다.'}), 400
    
    image_file = request.files['image']
    
    # 이미지 읽기
    image_bytes = image_file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # OCR 수행
    ocr_results = perform_ocr(img)
    
    # OCR 결과 텍스트 추출 및 맞춤법 검사
    text_results = [i[1] for i in ocr_results]
    corrected_results = [correct_text(text) for text in text_results]

    # 날짜 추출 및 정보 저장
    extracted_dates = []
    for text in corrected_results:
        dates = extract_dates(text)
        if dates:
            # 날짜가 존재하면 저장
            extracted_dates.extend(dates)
    
    response_data = {
        'text_results': corrected_results,
        'dates': extracted_dates if extracted_dates else None
    }
    
    return jsonify(response_data)


@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)