from flask import Flask, render_template, request, send_from_directory, Response
import tensorflow as tf
import numpy as np

app = Flask(__name__)


# model =tf.keras.models.load_model('path')

# @app.route("/predict",methods=['post'])
# def predict():
    
#     input_data = request.json['input']
    
    
#     prediction = model.predict(input_data)
    
#     return jsonify({'prediction': prediction.tolist()})


@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
