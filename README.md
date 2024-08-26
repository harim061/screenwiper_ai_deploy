# screenwiper_ai

`uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

```
curl --location 'http://15.164.115.105:8080/analyze_images' \
--header 'Content-Type: application/json' \
--data '{"imageUrls": ["https://screen-s3-bucket.s3.ap-northeast-2.amazonaws.com/place4.png"]}'


curl --location 'http://15.164.115.105:8080/analyze_images' \
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

```
docker build -t holiday061/screenwiper:latest .

docker push holiday061/screenwiper:latest

sudo docker stop screenwiper
sudo docker rm screenwiper
sudo docker pull holiday061/screenwiper:latest
sudo docker run --name screenwiper -p 8080:8080 -d holiday061/screenwiper:latest



```
