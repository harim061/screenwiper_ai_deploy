import requests

# 서버 URL
url = 'http://127.0.0.1:5000/analyze_image'

# 테스트 이미지 URL
image_url = 'https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/1724344939862_IMG_0476.PNG'

# 요청 보내기
response = requests.post(url, data={'imageUrl': image_url})

# 응답 처리
if response.status_code == 200:
    result = response.json()
    
    # 응답의 텍스트 결과와 날짜 추출
    text_results = result.get('summary', '')  # 'summary' 또는 'text_results'로 변경될 수 있음
    extracted_dates = result.get('dates', [])  # 'dates'는 카테고리 2의 경우에 해당할 수 있음
    
    print("인식된 텍스트:")
    print(text_results)
    
    print("\n추출된 날짜:")
    for date in extracted_dates:
        print(date)

    print("\n응답 데이터:")
    print(result)
else:
    print("Error:", response.text)
