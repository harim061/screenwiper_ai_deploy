import requests

# 서버 URL
url = 'http://15.164.115.105:8080/analyze_image'
# url = 'http://127.0.0.1:8000/analyze_image'

# 일정
# https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/1724418374514_%E1%84%8B%E1%85%B5%E1%86%AF%E1%84%8C%E1%85%A5%E1%86%BC.png

#문래동멘
# 

# 테스트 이미지 URL
#image_url = 'https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/1724350887204_test.png'
#image_url = 'https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/test_img3.jpeg'
image_url = 'https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/1724418374514_%E1%84%8B%E1%85%B5%E1%86%AF%E1%84%8C%E1%85%A5%E1%86%BC.png'

# 요청 보내기
response = requests.post(url, json={'imageUrl': image_url})

# 응답 처리
if response.status_code == 200:
    result = response.json()
    
    print("\n응답 데이터:")
    print(result)
else:
    print("Error:", response.text)

