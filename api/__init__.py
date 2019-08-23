
from sanic import Blueprint

from .order import order



api = Blueprint.group(order, url_prefix='/api')




