from flask import Flask,request,abort
from app.Config import *
import json
import pickle
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials

from keras.models import load_model
from pythainlp.tokenize import word_tokenize
from keras.utils import pad_sequences
from keras.models import Sequential
from keras.layers import Embedding, Bidirectional, LSTM, GlobalMaxPooling1D, Dense
from keras.preprocessing.text import Tokenizer
import numpy as np

Channel_access_token = " your-token "
app = Flask(__name__)

@app.route('/',methods=['POST' , 'GET'])
def webhook():
    if request.method == 'POST':
        payload = request.get_json()
        events = payload['events']
        for event in events:
            event_type = event['type']
            if event_type == 'message':
                user_message = event['message']['text']
                print(user_message)
                message = NLP_model(user_message)
                Reply_message = get_reply(message)
                ReplyMessage(event['replyToken'], Reply_message, Channel_access_token)
        return 'OK', 200
    

def NLP_model(message):
    with open('tool2.p','rb') as f:
        tokenizer  = pickle.load(f)

    model = load_model("NLP.h5")

    tokenizer.fit_on_texts(message)
    text_to_predict = [message]
    tokenized_text = [word_tokenize(text, keep_whitespace=False) for text in text_to_predict]
    text_sequences = tokenizer.texts_to_sequences(tokenized_text)
    padded_sequence = pad_sequences(text_sequences, maxlen=11, padding="post")
    predicted_class = model.predict(padded_sequence)
    
    predicted_class_index = np.argmax(predicted_class)
    class_labels = ['0', '1', '2', '3', '4', '5', '6']
    predicted_label = class_labels[predicted_class_index]

    for text, prediction in zip(text_to_predict, predicted_label):
        print(text, prediction)
    f.close() 
    return predicted_label  

def get_reply(message):
    # Initialize Google Sheets client
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
    gc = gspread.authorize(creds)
    # Open the Google Sheets
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.worksheet("Label")
    
    # Find the row with the matching message
    cell = worksheet.find(message, in_column=2)
    
    if cell:
        # Get the corresponding reply from column 1
        return worksheet.cell(cell.row, 1).value
    else:
        return "ฉันไม่เข้าใจที่คุณถาม"
    
def ReplyMessage(Reply_token,TextMessage,Line_Acees_Token):
    LINE_API = 'https://api.line.me/v2/bot/message/reply/'
    
    Authorization='Bearer {}'.format(Line_Acees_Token)
    print(Authorization)
    headers={
        'Content-Type':'application/json; char=UTF-8',
        'Authorization': Authorization
    }

    data={
        "replyToken":Reply_token,
        "messages":[{
            "type":"text",
            "text":TextMessage
        }
        ]
    }
    data=json.dumps(data) # ทำเป็น json
    r=requests.post(LINE_API,headers=headers,data=data)
    return 200

