from flask import Flask, render_template, request
import pandas as pd
import os
import nltk
from nltk.tokenize import word_tokenize
import requests
import json


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        file = request.files['file']
        file.save(os.path.join("UPLOAD_FOLDER", file.filename))
        df = pd.read_excel(file)
        # REMOVE INTEGER VALUES FROM TRANSACTION DETAILS
        df['TRANSACTION_DETAILS_WITHOUTINT']= df['TRANSACTION_DETAILS'].replace('\d+', '', regex=True)

        # SPLIT STRING TO REQUIRED PARTS

        df['SHOPNAME'] = df['TRANSACTION_DETAILS_WITHOUTINT'].str.split(' ').str[2:6]
        df['TRANSACTION_TYPE'] = df['TRANSACTION_DETAILS_WITHOUTINT'].str.split(' ').str[0:2]
        df['TRANSACTION_TYPE']= df['TRANSACTION_TYPE'].str.join(",")
        df['TRANSACTION_TYPE']= df['TRANSACTION_TYPE'].str.replace("," , " ")
        df['SHOPNAME']= df['SHOPNAME'].str.join(",")
        df['SHOPNAME']= df['SHOPNAME'].str.replace("," , " ")

        df['SHOPNAME'] = df['SHOPNAME'].replace(to_replace='SYSTEM', value="",regex=True)
        df['SHOPNAME'] = df['SHOPNAME'].replace(to_replace='ACH', value="",regex=True)
        df['SHOPNAME'] = df['SHOPNAME'].replace(to_replace='FROM', value="",regex=True)
        df['SHOPNAME'] = df['SHOPNAME'].replace(to_replace='-- ', value="",regex=True)
        df['SHOPNAME'] = df['SHOPNAME'].replace(to_replace='/', value="",regex=True)


        #Call google API

        rest_api_df = df.copy()

        GOOGLE_API_KEY = '##INSERT YOUR KEY HERE' 



        def google_place_api(address_value):
                type1 = None
                api_key = GOOGLE_API_KEY
                
                base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
                endpoint = f"{base_url}?input={address_value}&inputtype=textquery&fields=type&key={api_key}"
                # see how our endpoint includes our API key? Yes this is yet another reason to restrict the key
                r = requests.get(endpoint)
                if r.status_code == 200:
                        results = r.json()
                        type1 = str(results['candidates'])
                        return type1
                else:
                        type = "API PASSED"
                        return type1
        
        def enrich_with_geocoding_api(row):
                column_name = 'SHOPNAME'
                address_value = row[column_name]
                shopname = google_place_api(address_value)
                row['SHOP_TYPE'] = shopname
                return row

        rest_api_df = rest_api_df.apply(enrich_with_geocoding_api, axis=1) # axis=1 is important to use the row itself
        rest_api_df['SHOP_TYPE'] = rest_api_df['SHOP_TYPE'].str[13:42]
        rest_api_df['BAD_CATEGORY_TRANSACTION'] = rest_api_df['SHOP_TYPE'].str.contains('casion').any()

        #DUMMY DATA FOR CUSTOMER INFORMATION

        # intialise data of lists.
        testdata = df
        
        # Create DataFrame
        data1 = pd.DataFrame(testdata)

        return render_template('data.html', data=rest_api_df.to_html(), data1=data1.to_html())



if __name__ == '__main__':
    app.run(debug=True)
