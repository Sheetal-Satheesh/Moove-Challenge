import os
from typing import List
from flask import Flask, jsonify, render_template, request
import datetime, json
import db_init as di
import requests

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
    print("db_path: ", db_path)
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
   
    res = conn.execute("SELECT license,vehicle.device_id,start_time,stop_time,distance FROM vehicle,trips WHERE vehicle.device_id = trips.device_id")
    res_df = [list(result) for result in res.fetchall()]
    exceptions = conn.execute("SELECT * From driving_exception")
    except_df = [list(result) for result in exceptions.fetchall()]
    di.close_connection(db_path)
    
    data_list = list()
    for trip in res_df:
        counter_harsh_accerelation = 0
        counter_speeding = 0        
        for exception in except_df:
            if ((trip[1] == exception[1]) and (exception[4] == "apUro_0nXOUmLV4SVlzK8Xw") and (trip[2] <= exception[2]) and (trip[3] >= exception[3])):
                counter_harsh_accerelation = counter_harsh_accerelation + 1
            if ((trip[1] == exception[1]) and (exception[4] == "abHSbCv2PKUWKSSGJMoiBnQ") and (trip[2] <= exception[2]) and (trip[3] >= exception[3])):
                counter_speeding = counter_speeding + 1
        data = {
            "licensePlate": trip[0],
            "tripStart": trip[2],
            "tripEnd": trip[3],
            "distance": trip[4],
            "harshAcceleration": counter_harsh_accerelation,
            "speeding": counter_speeding
        }
        data_list.append(data)
            
    return jsonify({"result":data_list})

port = int(os.environ.get("PORT", 8000))
app.run(host="0.0.0.0", port=port)
    


