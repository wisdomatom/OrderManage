import json
import traceback

import sanicdb, aiomysql
from pymysql import IntegrityError
from sanic import request
from aioredis.commands import Redis
from sanic import Blueprint
from sanic import response
from sanic.views import HTTPMethodView
from api.order.filter import *

view = Blueprint('view', url_prefix='')


def logined(func):
    async def wraper(request: request.Request, *args, **kwargs):
        res = {'state_code': -1, 'error_msg': 'login first'}
        api_key = request.headers.get('api-key','unknown')
        print(api_key,type(api_key))
        sql = 'SELECT eatery_id from eatery WHERE api_key = %s'
        async with request.app.db.acquire() as conn:  # type: aiomysql.connection.Connection
            async with conn.cursor() as cur:  # type: aiomysql.cursors.Cursor
                await cur.execute(sql,api_key)
                ret = await cur.fetchall()
                if ret:
                    rel = await func(request, *args, **kwargs)
                else:
                    return response.json(res)
        return rel
    return wraper


@view.route('/put',methods=['GET','PUT','POST'], name='order_put', strict_slashes=False)
@logined
@params(order_put_filter)
async def handler(request: request.Request):
    res = {'state_code': -1, 'error_msg': ''}
    try:
        data = request.json
        order_detail = data.pop('order_detail')
        order_fields = ','.join(data.keys())
        order_put = 'insert into orders ({}) value({})'.format(order_fields, ','.join(['%s'] * len(data)))

        detail_put = ''
        redis_conn = request.app.redis # type: Redis
        #sql_conn = request.app.db # type: sanicdb.SanicDB

        # sql = 'select * from dishimg limit 1000,10'
        mysql_error = ''
        async with request.app.db.acquire() as conn: # type: aiomysql.connection.Connection
            async with conn.cursor() as cur: # type: aiomysql.cursors.Cursor
                try:
                    await conn.begin()
                    await cur.execute(order_put, tuple(data.values()))
                    await conn.commit()
                    # sql_res = await cur.fetchall()
                    if order_detail:
                        detail_fields = ','.join(order_detail[0].keys())
                        order_detail_values = [tuple(dic.values()) for dic in order_detail]
                        order_id = cur.lastrowid
                        detail_put = 'insert into order_detail (order_id, {}) values ({}, {})'.format(
                            detail_fields, order_id, ','.join(['%s'] * len(order_detail[0])))
                        await cur.executemany(detail_put, order_detail_values)
                        await conn.commit()
                    res.update({'state_code': 0, 'error_msg':'ok',})
                except IntegrityError as e:
                    await conn.rollback()
                    mysql_error = 'order_id 重复插入'
                    res.update({'state_code': -3, 'error_msg': mysql_error})
                except Exception as e:
                    await conn.rollback()
                    mysql_error = traceback.format_exc()
                    res.update({'error_msg': mysql_error})
    except Exception as e:
        json_parse_error = traceback.format_exc()
        res.update({'error_msg': json_parse_error})

    # redis_res = await redis_conn.delete('hello','test_set')
    return response.json(res)


def order_query(query_condition):
    sql = 'select * from orders left join order_detail on orders.id = order_detail.order_id {}'

    condition = 'limit 0,1'
    parms = ()
    for key, value in query_condition.items():
        if key == 'order_id':
            condition = 'where orders.order_id in ({})'.format(','.join(['%s'] * len(value)))
            parms = value
        elif key == 'date_time_range':
            condition = 'where create_ts >= %s and create_ts <= %s'
            parms = (value[0], value[1])
        break
    query_sql = sql.format(condition)
    return query_sql, parms


@view.route('/get', methods=['GET'], name='order_get', strict_slashes=False)
@logined
@params(order_get_filter)
async def handler(request: request.Request):
    res = {'state_code': -1, 'error_msg': ''}
    try:
        data = request.json
        sql, parms = order_query(data)
        async with request.app.db.acquire() as conn:  # type: aiomysql.connection.Connection
            async with conn.cursor(aiomysql.cursors.DictCursor) as cur:  # type: aiomysql.cursors.Cursor
                await cur.execute(sql, parms)
                ret = await cur.fetchall()
                res.update({'state_code': 0, 'error_msg': 'ok', 'data': ret})
    except Exception as e:
        error = traceback.format_exc()
        res.update({'error_msg': str(error)})
    return response.json(res)


@view.route('/refund_update', methods=['PUT',"POST"], name='refund_order_update', strict_slashes=False)
@logined
@params(refund_order_update_filter)
async def handler(request: request.Request):
    res = {'state_code': -1, 'error_msg': ''}
    try:
        data = request.json  # type: json
        refund_food_uuid_list = data.get('refund_food_uuid_list')  # type: list
        order_update = 'UPDATE orders SET total_price = {}, refund_price = {}, is_refund = {} WHERE order_id = {}'\
            .format(data.get('total_price'), data.get('refund_price'), data.get('is_refund'), data.get('order_id'))
        async with request.app.db.acquire() as conn:  # type: aiomysql.connection.Connection
            async with conn.cursor() as cur:  # type: aiomysql.cursors.Cursor
                try:
                    await conn.begin()
                    await cur.execute(order_update)
                    await conn.commit()
                    if refund_food_uuid_list:
                        update_order = 'UPDATE order_detail o1 INNER JOIN orders o2 ON o1.order_id = o2.id SET ' \
                                       'o1.is_refund = 1 WHERE o2.order_id = {} AND o1.food_uuid = %s AND o1.is_refund = 0 limt 1'\
                            .format(data.get('order_id'))
                        for food_uuid in refund_food_uuid_list:
                            await cur.execute(update_order,food_uuid)
                        await conn.commit()
                    res.update({'state_code': 0, 'error_msg': 'ok'})
                except Exception as e:
                    await conn.rollback()
                    res.update({'error_msg': traceback.format_exc()})
    except Exception as e:
        res.update({'error_msg': traceback.format_exc()})
    return response.json(res)
