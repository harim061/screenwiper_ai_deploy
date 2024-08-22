import requests

# 서버 URL
url = 'http://18.232.142.57:5000//analyze_image'

# 테스트 이미지 파일 경로
# file_path = './test_img/test3.png'
image_url = 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fm.youtube.com%2Fwatch%3Fv%3DMbzMm8gcEfU&psig=AOvVaw0h7peOB7-H-TwrYhHeiF2u&ust=1724430035064000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCNisv8-AiYgDFQAAAAAdAAAAABAE'

# 이미지 파일 열기 및 요청 보내기
"""
with open(file_path, 'rb') as image_file:
    files = {'image': image_file}
    response = requests.post(url, files=files)
"""

# ?api 연결 후 url로 변경  

# 테스트 이미지 URL
# image_url = 'https://your-s3-bucket-url/test_img/map-test.png'

# 요청 보내기
response = requests.post(url, data={'imageUrl': image_url})


# 응답 처리
if response.status_code == 200:
    result = response.json()
    
    # 응답의 텍스트 결과와 날짜 추출
    text_results = result.get('text_results', [])
    extracted_dates = result.get('dates', [])
    
    print("인식된 텍스트:")
    for text in text_results:
        print(text)
    
    print("\n추출된 날짜:")
    for date in extracted_dates:
        print(date)

    print("\n응답 데이터:")
    print(result)
else:
    print("Error:", response.text)
