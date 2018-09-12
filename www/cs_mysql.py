#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import orm, asyncio
from models import User, Blog, Comment

async def test(loop):
    await orm.create_pool(loop,host='192.168.71.139',user='root',
                               password='root',db='web')
    u = User(name='Test1',email='test1@example.com',passwd='123456',image='about:blank')
    #await u.save()
    #await User.find_pk('001535898162283ca6bee8f1c044eceb01e97bd9436e297000')
    a = '''passwd = '%s'
    ''' % '123456'
    await User.findAll(a)
    #await User.findNumber(a)



loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
#loop.close()