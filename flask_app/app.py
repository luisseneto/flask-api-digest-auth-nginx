from flask import Flask
from flask import jsonify
from flask import request
import json
from utils.athena_query_response import *
from utils.status_code_error_handling import *
from datetime import date, datetime

server = Flask(__name__)

@server.route('/gettripoptions', methods=['POST'])
def getTripOptions():
    
    """function that returns information about pricing and availability of seats from trips.
    The lambda get this information from the clickbus AWS Athena.
    :param event: Event request,
    :param context:
    :return: Pricing and availability of seats in a specific trip
    """
    event = request.json

    #   Validating if the request json is correctly formatted
    if not validate_request(event):
        response = {
            "trip_options_error": {
                "error_type": "SEGMENT_KEY_NOT_FOUND",
                "error_message": "Segment Keys or sub-keys not found, check the request json."
            }
        }
        return jsonify(response)

    response = {
        "trip_options_result": {
            "trip_options": []
        }
    }

    #   Request query that return information about the trip
    request_query = """
        SELECT 
            f.service_class,
            f.disponiveis AS available_seat_count,
            f.total AS total_seat_count,
            date_format(f.timestamp, '%Y-%m-%dT%H:%i:%s.%f') as formatted_timestamp
        FROM 
            share.future_occupation f
        WHERE 
            f.departure_year = {0} AND 
            f.departure_date = date('{0}-{1}-{2}') AND 
            f.origin_id = {3} AND 
            f.destination_id = {4} AND 
            f.travel_company_id = 46 AND 
            f.departure_hour = '{5}:{6}:{7}';
        """

    #   This arrival query it's necessary because right now we don't have an easy way to return
    #   This query is necessary because for a trip with same departure date, we can have different arrival hours.
    request_query_arrival = """
        SELECT 
            f.timestamp,
            f.arrival_date,
            f.arrival_hour,
            f.service_class,
            f.travel_price
        FROM 
            dl_event_stream.seat_screenshot AS f 
        WHERE
            f.created_year = '{0}' AND
            f.created_month = '{1}' AND
            f.created_day = '{2}' AND
            f.timestamp = '{3}'
        GROUP BY
            f.timestamp,
            f.arrival_date,
            f.arrival_hour,
            f.service_class,
            f.travel_price

        """

    ticketing_trip_id = event['segment_keys'][0]['ticketing_trip_id']
    from_ticketing_stop_time_id = event['segment_keys'][0]['from_ticketing_stop_time_id']
    to_ticketing_stop_time_id = event['segment_keys'][0]['to_ticketing_stop_time_id']

    service_date_year = event['segment_keys'][0]['service_date']['year']
    service_date_month = event['segment_keys'][0]['service_date']['month']
    service_date_day = event['segment_keys'][0]['service_date']['day']

    boarding_time_year = event['segment_keys'][0]['boarding_time']['year']
    boarding_time_month = event['segment_keys'][0]['boarding_time']['month']
    boarding_time_day = event['segment_keys'][0]['boarding_time']['day']
    boarding_time_hours = event['segment_keys'][0]['boarding_time']['hours']
    boarding_time_minutes = event['segment_keys'][0]['boarding_time']['minutes']
    boarding_time_seconds = event['segment_keys'][0]['boarding_time']['seconds']
    boarding_time_nanos = event['segment_keys'][0]['boarding_time']['nanos']
    boarding_time_utc_offset = event['segment_keys'][0]['boarding_time']['utc_offset']

    arrival_time_year = event['segment_keys'][0]['arrival_time']['year']
    arrival_time_month = event['segment_keys'][0]['arrival_time']['month']
    arrival_time_day = event['segment_keys'][0]['arrival_time']['day']
    arrival_time_hours = event['segment_keys'][0]['arrival_time']['hours']
    arrival_time_minutes = event['segment_keys'][0]['arrival_time']['minutes']
    arrival_time_seconds = event['segment_keys'][0]['arrival_time']['seconds']
    arrival_time_nanos = event['segment_keys'][0]['arrival_time']['nanos']
    arrival_time_utc_offset = event['segment_keys'][0]['arrival_time']['utc_offset']

    #   Creating an arrival date timestamp
    request_arrival_date = datetime(arrival_time_year, arrival_time_month, arrival_time_day, arrival_time_hours,
                                    arrival_time_minutes)

    results, res, state = api_query_response(request_query.format(service_date_year,
                                                                  leading_zero(service_date_month),
                                                                  leading_zero(service_date_day),
                                                                  from_ticketing_stop_time_id,
                                                                  to_ticketing_stop_time_id,
                                                                  leading_zero(boarding_time_hours),
                                                                  leading_zero(boarding_time_minutes),
                                                                  leading_zero(boarding_time_seconds)))
    #   Verify if the trip exists
    if results.empty:
        response = {
            "trip_options_error": {
                "error_type": "SEGMENT_KEY_NOT_FOUND",
                "error_message": "No matching segments found, no departures at {0}:{1}".format(
                    leading_zero(boarding_time_hours),
                    leading_zero(boarding_time_minutes))
            }
        }
        return jsonify(response)

    # Returning every info about seats and prices from a different service class in the same trip
    for sc, ts, asc, tsc in zip(results['service_class'], results['formatted_timestamp'],
                                results['available_seat_count'], results['total_seat_count']):
        timestamp = remove_zeros(ts)
        timestamp_year = datetime.strptime(timestamp[0:10], '%Y-%m-%d').year
        timestamp_month = leading_zero(datetime.strptime(timestamp[0:10], '%Y-%m-%d').month)
        timestamp_day = leading_zero(datetime.strptime(timestamp[0:10], '%Y-%m-%d').day)

        arrival_results, _, _ = api_query_response(request_query_arrival.format(timestamp_year,
                                                                                timestamp_month,
                                                                                timestamp_day,
                                                                                timestamp))

        sc_arrival_date = datetime.strptime(arrival_results.arrival_date[0] + ' ' + arrival_results.arrival_hour[0],
                                            '%Y-%m-%d %H:%M:%S')
        # TO-DO - Verificar melhor como a dinamica para duas viagens com mesmas datas de partida e chegada
        if sc_arrival_date != request_arrival_date:
            continue

        opt_response = {
            "segments": [],
            "lowest_standard_fare": {},
            "availability": {}
        }

        segment = event['segment_keys'][0]

        opt_response['segments'].append({'segment_keys': segment, 'service_class': {'type': sc}})

        opt_response['lowest_standard_fare']['total_amount'] = {}
        opt_response['lowest_standard_fare']['total_amount']['units'] = 0
        opt_response['lowest_standard_fare']['total_amount']['nanos'] = 0
        opt_response['lowest_standard_fare']['total_amount']['currency_code'] = 'BRL'

        opt_response['lowest_standard_fare']['line_items'] = []
        opt_response['lowest_standard_fare']['line_items'].append({
            'line_item_type': 'BASE_FARE',
            'amount': {
                'units': int(arrival_results['travel_price'][0].split('.')[0]),
                'nanos': int(arrival_results['travel_price'][0].split('.')[1]),
                'currency_code': 'BRL'
            }
        })
        opt_response['lowest_standard_fare']['line_items'].append({
            'line_item_type': 'SERVICE_CHARGE',
            'amount': {
                'units': 0,
                'nanos': 0,
                'currency_code': 'BRL'
            }
        })

        opt_response['availability']['available_seat_count'] = asc
        opt_response['availability']['total_seat_count'] = tsc

        response['trip_options_result']['trip_options'].append(opt_response)

    return jsonify(response)
