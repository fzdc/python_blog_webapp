#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
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














