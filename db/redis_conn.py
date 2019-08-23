from sanic_session import Session, AIORedisSessionInterface
import aioredis
from config.settings import redis_config

async def setup_redis(app, loop):

    app.redis = await aioredis.create_redis_pool(loop=loop, **redis_config)

    session = Session()
    session.init_app(app, interface=AIORedisSessionInterface(app.redis))

