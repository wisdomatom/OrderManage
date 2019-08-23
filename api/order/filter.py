import json
import time
from sanic import request, response


def params(filter_map):
    def deco(func):
        async def execute(*args, **kwargs):
            res = {'state_code': 0, 'error_msg': 'ok'}
            request = args[0]  # type: request.Request
            try:
                request_json = request.json
            except Exception as e:
                res.update({'state_code': -1, 'error_msg': 'json decode error'})
                return response.json(res)
            if not request_json:
                res.update({'state_code': -2, 'error_msg': 'argument error'})
                return response.json(res)
            for field, value in filter_map.items():
                if field == 'response_filter':
                    continue
                if value.get('verify') == 'add':
                    request.json.update({field: value.get('get_value')()})
                elif value.get('verify') == 'deep':
                    for field_d, value_d in value.get('deep_field').items():
                        if value_d.get('verify') == 'verify':
                            if value_d.get('necessary'):
                                for d_field in request_json.get(field):
                                    if field_d not in d_field:
                                        res.update({'state_code': -1, 'error_msg': '\'{}\' field is needed'.format(field_d)})
                                        return response.json(res)
                elif value.get('verify') == 'verify':
                    if value.get('necessary') and (field not in request_json):
                        res.update({'state_code': -1, 'error_msg': '\'{}\' field is needed'.format(field)})
                        return response.json(res)
                    if not request_json.get(field):
                        pass
                    elif isinstance(request_json.get(field), value.get('type')):
                        continue
                    else:
                        res.update({'state_code': -1, 'error_msg': 'invalid field: {}:{}'.format(field,request_json.get(field))})
                        return response.json(res)

            resp = await func(*args, **kwargs)
            response_new = resp
            if json.loads(resp.body.decode()).get('state_code') == 0:
                response_filter = filter_map.get('response_filter')
                if response_filter:
                    response_new = response_filter(resp)
            return response_new

        return execute

    return deco


def order_get_response(res: response.HTTPResponse):
    orders = {}
    body = json.loads(res.body.decode())
    data = body.get('data')
    for order in data:
        order.pop('order_detail.order_id')
        order_id = order.get('order_id')
        detail = {
            'food_uuid': order.pop('food_uuid'),
            'food_name': order.pop('food_name'),
            'food_price': order.pop('food_price'),
            'calorie': order.pop('calorie'),
            'food_type': order.pop('food_type'),
            'is_refund': order.pop('order_detail.is_refund')
        }
        if order_id in orders:
            orders.get(order_id).get('order_detail').append(detail)
        else:
            order.update({'order_detail': [detail]})
            orders.update({order_id: order})
    data_new = [order for order_id, order in orders.items()]
    body.update({'data': data_new})
    res.body = json.dumps(body).encode()
    return res


order_put_filter = {
    'insert_ts': {'verify': 'add', 'get_value': lambda: int(time.time())},
    'date_time': {'verify': 'verify', 'type': (str,), 'necessary': True},
    'order_id': {'verify': 'verify', 'type': (str,), 'necessary': True},
    'total_price': {'verify': 'verify', 'type': (int, float), 'necessary': True},
    'create_ts': {'verify': 'verify', 'type': (int,), 'necessary': True},
    'pay_ts': {'verify': 'verify', 'type': (int,), 'necessary': True},
    'buyer': {'verify': 'verify', 'type': (str,), 'necessary': True},
    'meal': {'verify': 'verify', 'type': (int,), 'necessary': True},
    'manual': {'verify': 'verify', 'type': (int,), 'necessary': True},
    'discount': {'verify': 'verify', 'type': (int,),'necessary': True},
    'pay_way': {'verify': 'verify', 'type': (int,), 'necessary': True},
    'canteen_id': {'verify': 'verify', 'type': (int,), 'necessary': True},
    'machine_id': {'verify': 'verify', 'type': (int,), 'necessary': True},
    'mode': {'verify': 'verify', 'type': (str,), 'necessary': True},
    'meal_img': {'verify': 'verify', 'type': (str,), 'necessary': True},
    'refund_price': {'verify': 'verify', 'type': (int, float), 'necessary': True},
    'is_refund': {'verify': 'verify', 'type': (int,), 'necessary': True},
    'order_detail': {'verify': 'deep', 'type': (list,), 'necessary': True,
                     'deep_field': {
                         'food_uuid': {'verify': 'verify', 'type': (str,), 'necessary': True},
                         'food_name': {'verify': 'verify', 'type': (str,), 'necessary': True},
                         'food_price': {'verify': 'verify', 'type': (str,), 'necessary': True},
                         'calorie': {'verify': 'verify', 'type': (str,), 'necessary': True},
                         'food_type': {'verify': 'verify', 'type': (str,), 'necessary': True},
                         'is_refund': {'verify': 'verify', 'type': (str,), 'necessary': True}
                     }, },
    'response_filter': None
}

order_get_filter = {
    'order_id': {'verify': 'verify', 'type': (list,), 'necessary': False},
    'date_time_range': {'verify': 'verify', 'type': (list,), 'necessary': False},
    'response_filter': order_get_response
}

refund_order_update_filter = {
    'order_id': {'verify': 'verify', 'type': (str,), 'necessary': True},
    'total_price': {'verify': 'verify', 'type': (int, float), 'necessary': True},
    'refund_price': {'verify': 'verify', 'type': (int, float), 'necessary': True},
    'is_refund': {'verify': 'verify', 'type': (int,), 'necessary': True},
    'refund_food_uuid_list': {'verify': 'verify', 'type': (list,), 'necessary': False},
}
