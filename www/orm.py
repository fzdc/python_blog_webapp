#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio, aiomysql,logging


def log(sql,args=()):
    logging.info('SQL: %s' % sql)

def create_args_string(num):
    L = []
    print(num)
    n =0
    while n < num:
        n = n+1
        L.append('?')
    print(L)
    return ', '.join(L)

class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        #排除Model类本身
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)
        #获取table名称
        tableName = attrs.get('__table__', None) or name
        logging.info('found model:%s(table:%s)' % (name, tableName))
        #获取所有的Field和主键名
        mappings = dict()
        fields = []
        primaryKey = None
        for k,v  in attrs.items():
            if isinstance(v, Field):
                logging.info(' found mappings:%s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    #找到逐渐
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f:'%s' % f, fields))
        attrs['__mappings__'] = mappings  #报错属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey  #主键姓名
        attrs['__fields__'] = fields  #除主键外的属性名
        #构造默认的select, insert, update和delete语句
        attrs['__select__'] = 'select `%s` ,%s from `%s`' % (primaryKey, ','.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s,`%s`) values (%s)' % (tableName,','.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        print(attrs['__insert__'])
        attrs['__update__'] = 'update "%s" set %s where "%s"=?' % (tableName, ','.join(map(lambda f:'"%s"' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from "%s" where "%s"=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        #host=kw.get('host','localhost'),
        host=kw['host'],
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
        logging.warn('rows returned:%s' % len(rs))
        return rs

#定义insert/update/delete函数
async def execute(sql, args):
    log(sql)
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            print(sql,args)
            await cur.execute(sql.replace('?','%s'), args)
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected

#定义Model,所有ORM映射的基类Model
class Model(dict, metaclass=ModelMetaclass):
    def __init__(self,**kw):
        super(Model, self).__init__(**kw)
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)
    def __setattr__(self, key, value):
        self[key] = value
    def getValue(self,key):
        return getattr(self, key, None)
    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s:%s' % (key, str(value)))
                setattr(self, key, value)
        print(value)
        return value
    @classmethod
    async def find_pk(cls, pk, size=1):
        ' find object by primary key.'
        rs = await select('%s where `%s`=?' % (cls.__select__,cls.__primary_key__), [pk], size)
        if len(rs) == 0:
            return None
        print(cls(**rs[0]))
        return cls(**rs[0])
    @classmethod
    async def findAll(cls, *args):
        ' find object by primary key.'
        rs = await select(('%s where 1=1 '+(' and '+ ' and '.join(args) if args else '')) % (cls.__select__), ())
        if len(rs) == 0:
            return None
        print(rs)
        return rs
    @classmethod
    async def findNumber(cls, *args):
        ' find object by primary key.'
        rs = await select(('%s where 1=1 ' + (' and ' + ' and '.join(args) if args else '')) % (cls.__select__), ())
        print(len(rs))
        return len(rs)


    async def save(self):
        print(self.__fields__)
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert record: affected rows: %s' % rows)


#定义Field和其子类
class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

#映射varcahr的StringField
class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)
#映射varcahr的StringField
class BooleanField(Field):
    def __init__(self, name=None, primary_key=False, default=False, ddl=None):
        super().__init__(name, ddl, primary_key, default)
#映射varcahr的StringField
class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl=None):
        super().__init__(name, ddl, primary_key, default)

#映射varcahr的StringField
class TextField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl=None):
        super().__init__(name, ddl, primary_key, default)


