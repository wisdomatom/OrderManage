import sanicdb
from sanic import Sanic, Blueprint
from api import api
from db.db_conn import setup_mysql
from db.redis_conn import setup_redis
from sanic_cors import CORS, cross_origin
from sanic.log import *
import logging


logging.basicConfig(filename="access.log")


app = Sanic('Order', strict_slashes=False, configure_logging=LOGGING_CONFIG_DEFAULTS)

CORS(app)
# cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

bp_group = Blueprint.group(api, url_prefix='/order_manage')
app.blueprint(bp_group)

app.register_listener(setup_mysql, 'before_server_start')
app.register_listener(setup_redis, 'before_server_start')


# @app.middleware('request')
# async def halt_request(request):
#     return text('I halted the request')
#
#
# @app.middleware('response')
# async def halt_response(request, response):
#     return text('I halted the response')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8686, debug=True, access_log=True, workers=1)