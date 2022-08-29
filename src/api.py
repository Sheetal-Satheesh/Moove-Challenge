from typing import List
from flask import Flask, jsonify, render_template, request
import datetime, json
import db_init as di
import requests
import pandas as pd

app = Flask(__name__)
app.config["DEBUG"] = True
API_ENDPOINT = "https://my.geotab.com/apiv1"

db_path = di.get_db_path()
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=30)

@app.route('/')
def home():   
    return render_template("index.html")

@app.route('/trips', methods=['GET'])
def get_trips():
    conn = di.create_connection(db_path)
    res = conn.execute("SELECT device_id FROM vehicle")
    vehicles = [result[0] for result in res.fetchall()]
    di.close_connection(db_path)

      

    get_trips_data = {
        "method": "Get",
        "params": {
            "typeName": "Trip",
            "credentials": {
                "database": "moove",
                "sessionId": "2nR_L-I6A8F0K5DVF8srFQ",
                "userName": "moovechallengeuser@mooveconnected.com"
                },
            "search":{
                "fromDate": str(start_date),
                "toDate": str(end_date)
                }
        }
    }
    trips_data = requests.post(url = API_ENDPOINT, data = json.dumps(get_trips_data))
    trips_data_js = json.loads(trips_data.text)
    trips_result_data = trips_data_js['result']    
    expectedResult = [trip for trip in trips_result_data if trip['device']['id'] in vehicles]

    return expectedResult

@app.route('/driving_exceptions', methods=['GET'])
def get_drving_exceptions():
    conn = di.create_connection(db_path)
    res = conn.execute("SELECT device_id FROM vehicle")
    vehicles = [result[0] for result in res.fetchall()]
    di.close_connection(db_path)

    get_driving_exceptions_data = {
        "method": "Get",    
        "params": {
            "typeName": "ExceptionEvent",
            "credentials": {
                "database": "moove", "sessionId":"2nR_L-I6A8F0K5DVF8srFQ",
                "userName": "moovechallengeuser@mooveconnected.com"  
            },
        "search":{       
            "fromDate":str(start_date),            
            "toDate": str(end_date)
            }
        }
    }
    driving_exception_data = requests.post(url = API_ENDPOINT, data = json.dumps(get_driving_exceptions_data))
    driving_exception_data = json.loads(driving_exception_data.text)
    driving_exception_result_data = driving_exception_data['result']
    expectedResult = [dataE for dataE in driving_exception_result_data if dataE['device']['id'] in vehicles]
    return expectedResult

@app.route('/generate_report', methods=['GET'])
def generate_report():    
    args =  request.args
    today = datetime.datetime.now().isoformat()
    email = str(args.get('email'))
    start_date = args.get('startDate')
    end_date = args.get('endDate')

    conn = di.create_connection(db_path)
    res_trip = conn.execute("SELECT max(stop_time) FROM trips")
    max_end_time = datetime.datetime.strptime([result[0] for result in res_trip.fetchall()][0], '%Y-%m-%dT%H:%M:%S.%f%z') 
    max_end_time_data =  max_end_time.strftime('%Y-%m-%d')    
    res_driving_exception = conn.execute("SELECT max(active_to) FROM driving_exception")
    max_active_to = datetime.datetime.strptime([result[0] for result in res_driving_exception.fetchall()][0],'%Y-%m-%dT%H:%M:%S.%f%z') 
    max_active_to_data =  max_active_to.strftime('%Y-%m-%d')
        

    if end_date >= max_end_time_data:
        print("max_end_time_data",max_end_time_data)
        print("end_date", end_date)
        print("max_end_time", max_end_time)
        get_trips_data = {
            "method": "Get",
            "params": {
                "typeName": "Trip",
                "credentials": {
                    "database": "moove",
                    "sessionId": "2nR_L-I6A8F0K5DVF8srFQ",
                    "userName": "moovechallengeuser@mooveconnected.com"
                    },
                "search":{
                    "fromDate": str(max_end_time + datetime.timedelta(seconds=1)),
                    "toDate" : str(today)
                    }
            }
        }

        trips_data = requests.post(url = API_ENDPOINT, data = json.dumps(get_trips_data))
        trips_data_js = json.loads(trips_data.text)
        trips_result_data = trips_data_js['result']
        data_trips = []        
        db_cursor = conn.cursor()



        for dict_item in  trips_result_data:
            id = dict_item['id']
            device_id = dict_item['device']['id']
            start = dict_item['start']
            stop = dict_item['stop']
            distance = dict_item['distance']
            data_trips.append((id,device_id,start,stop,distance))
        
        db_cursor.executemany("INSERT INTO trips VALUES(?,?,?,?,?)", data_trips)
        conn.commit()
    
    if end_date >= max_active_to_data:
        get_driving_exceptions_data = {
            "method": "Get",    
            "params": {
                "typeName": "ExceptionEvent",
                "credentials": {
                    "database": "moove", "sessionId":"2nR_L-I6A8F0K5DVF8srFQ",
                    "userName": "moovechallengeuser@mooveconnected.com"  
                },
            "search":{       
                "fromDate":str(max_active_to + datetime.timedelta(seconds=1)),            
                "toDate": str(today)
                }
            }
        }
        driving_exception_data = requests.post(url = API_ENDPOINT, data = json.dumps(get_driving_exceptions_data))
        driving_exception_data = json.loads(driving_exception_data.text)
        driving_exception_result_data = driving_exception_data['result']
        data_except = []

        for dict_item in  driving_exception_result_data:
            id = dict_item['id']
            device_id = dict_item['device']['id']
            active_from = dict_item['activeFrom']
            active_to = dict_item['activeTo']
            rule_id = dict_item['rule']['id']
            data_except.append((id,device_id,active_from,active_to,rule_id))

        db_cursor.executemany("INSERT INTO driving_exception VALUES(?,?,?,?,?)", data_except)
        conn.commit()        
   
    res_df = pd.read_sql_query("SELECT license,vehicle.device_id,start_time,stop_time,distance FROM vehicle,trips WHERE vehicle.device_id = trips.device_id",conn)
    except_df = pd.read_sql_query("SELECT * From driving_exception",conn)

    res_df['Harsh Acceleration'] = ''
    res_df['Speeding'] = ''

    for index in res_df.index:
        counter_harsh_accerelation = 0
        counter_speeding = 0        
        for ind in except_df.index:
            if ((res_df['device_id'][index] == except_df['device_id'][ind]) and (except_df['rule_id'][ind] == "apUro_0nXOUmLV4SVlzK8Xw") and (res_df['start_time'][index] <= except_df['active_from'][ind]) and ((res_df['stop_time'][index] >= except_df['active_to'][ind]))):
                counter_harsh_accerelation = counter_harsh_accerelation + 1
            if ((res_df['device_id'][index] == except_df['device_id'][ind]) and (except_df['rule_id'][ind] == "abHSbCv2PKUWKSSGJMoiBnQ") and (res_df['start_time'][index] <= except_df['active_from'][ind]) and ((res_df['stop_time'][index] >= except_df['active_to'][ind]))):
                counter_speeding = counter_speeding + 1
        res_df.loc[index, 'Harsh Acceleration'] = counter_harsh_accerelation
        res_df.loc[index, 'Speeding'] = counter_speeding        
    
    res_df.drop('device_id', axis=1, inplace = True)   
    di.close_connection(db_path)

    data_list = list()
    for index in res_df.index:
        data = {
            "licensePlate": res_df["license"][index],
            "tripStart": res_df["start_time"][index],
            "tripEnd": res_df["stop_time"][index],
            "distance": res_df["distance"][index],
            "harshAcceleration": res_df["Harsh Acceleration"][index],
            "speeding": res_df["Speeding"][index]
        }
        data_list.append(data)    
    return jsonify({"result":data_list})

app.run()
    


