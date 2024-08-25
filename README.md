# screenwiper_ai

`uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

```
curl --location 'http://127.0.0.1:8000/analyze_image' \
--header 'Content-Type: application/json' \
--data '{"imageUrl": "https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/place3.png"}'
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
