import requests
import json

url = 'http://localhost:5000/analyze_image'
files = {'image': open('./test_img/test4.png', 'rb')}

response = requests.post(url, files=files)

if response.status_code == 200:
    result = response.json()
    print("인식된 텍스트:")
    for text in result['text_results']:
        print(text)


else:
    print("Error:", response.text)
