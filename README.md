# screenwiper_ai

`uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

```
curl --location 'http://127.0.0.1:5000/analyze_images' \
--header 'Content-Type: application/json' \
--data '{"imageUrls": ["https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/place3.png"]}'


curl --location 'http://127.0.0.1:5000/analyze_images' \
--header 'Content-Type: application/json' \
--data '{
  "imageUrls": [
    "https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/place2.png",
    "https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/place3.png"
  ]
}'

```

```
screenwiper_ai/
├── Dockerfile
├── requirements.txt
├── screenwiper/
│   ├── main.py
│   ├── templates/
│   ├── test_img/
│   └── test_script.py
└── screenwiperV/
```
