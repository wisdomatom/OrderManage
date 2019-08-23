import sanicdb
import aiomysql
from config import settings


async def db_setup(app,loop):

    # db = sanicdb.SanicDB(
    #     sanic=app,
    #     **settings.mysql_db
    # )

    db = await aiomysql.create_pool(
        loop=loop,
        **settings.mysql_db
    )

    return db


async def setup_mysql(app, loop):
    app.db = await db_setup(app,loop)
    print('db up')




