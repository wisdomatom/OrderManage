
from sanic import Blueprint

from .view import view

order = Blueprint.group(view, url_prefix='/order')