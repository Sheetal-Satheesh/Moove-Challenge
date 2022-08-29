import requests, json
import db_init as di

API_ENDPOINT = "https://my.geotab.com/apiv1"

get_vehicle_data = {
    "method":"Get",
    "params": {
    "typeName": "Device",
    "credentials": {
        "database": "moove",
        "sessionId": "2nR_L-I6A8F0K5DVF8srFQ",
        "userName": "moovechallengeuser@mooveconnected.com"
        }
    }
}

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
        "fromDate":"2022-07-1",
        "toDate": "2022-08-1"}
    }
}

get_driving_exceptions_data = {
    "method": "Get",    "params": {
    "typeName": "ExceptionEvent",
    "credentials": {"database": "moove", "sessionId":"2nR_L-I6A8F0K5DVF8srFQ",
            "userName": "moovechallengeuser@mooveconnected.com"        
            },
    "search":{       
        "fromDate":"2022-07-1",            
        "toDate": "2022-08-1"
        }
    }
}

vehicle_data = requests.post(url = API_ENDPOINT, data = json.dumps(get_vehicle_data))
trips_data = requests.post(url = API_ENDPOINT, data = json.dumps(get_trips_data))
driving_exception_data = requests.post(url = API_ENDPOINT, data = json.dumps(get_driving_exceptions_data))
vehicle_data_js = json.loads(vehicle_data.text)
trips_data_js = json.loads(trips_data.text)
driving_exception_data = json.loads(driving_exception_data.text)

vehicle_result_data = vehicle_data_js['result']
trips_result_data = trips_data_js['result']
driving_exception_result_data = driving_exception_data['result']

db_path = di.get_db_path()
conn = di.create_connection(db_path)
db_cursor = conn.cursor()

def insert_data_into_vehicle_table(data_vehicle, table_name):     
    db_cursor.executemany("INSERT INTO "+table_name+" VALUES(?,?)", data_vehicle)
    conn.commit()

def insert_data_into_table(data, table_name):
    db_cursor.executemany("INSERT INTO "+table_name+" VALUES(?,?,?,?,?)", data)
    conn.commit()

data_vehicle = []
data_trips = []
data_except = []

for dict_item in vehicle_result_data:
    license_plate = dict_item['licensePlate']
    device_id = dict_item['id']
    data_vehicle.append((license_plate,device_id))

for dict_item in  trips_result_data:
    id = dict_item['id']
    device_id = dict_item['device']['id']
    start = dict_item['start']
    stop = dict_item['stop']
    distance = dict_item['distance']
    data_trips.append((id,device_id,start,stop,distance))

for dict_item in  driving_exception_result_data:
    id = dict_item['id']
    device_id = dict_item['device']['id']
    active_from = dict_item['activeFrom']
    active_to = dict_item['activeTo']
    rule_id = dict_item['rule']['id']
    data_except.append((id,device_id,active_from,active_to,rule_id))

    
insert_data_into_vehicle_table(data_vehicle, 'vehicle')
insert_data_into_table(data_trips, 'trips')
insert_data_into_table(data_except, 'driving_exception')

di.close_connection(db_path)



