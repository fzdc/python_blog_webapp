#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio, os, json, time
from datetime import datetime
from aiohttp import web

routes = web.RouteTableDef()


@routes.get('/')
async def index(request):
    await asyncio.sleep(2)
    return web.json_response({
        'name': 'index'
    })


@routes.get('/about')
async def about(request):
    await asyncio.sleep(0.5)
    return web.Response(body="<h1>about us</h1>",content_type='text/html')


def init():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app,port=8005)
init()


async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host','localhost'),
        port=kw.get('post',3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','utf8'),
        autocommit=kw.get('autocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop
    )

#定义select函数
async def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?','%s'), args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned:%s' % len(s))
        return rs

#定义insert/update/delete函数
async def execute(sql, args):
    log(sql)
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?','%s'), args)
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected
		
		




