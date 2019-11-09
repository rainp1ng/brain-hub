import logging
import sys, json
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
from brain_hub.conf import *
from brain_hub.utils import *
from brain_hub.exceptions import *
from brain_hub.server_tools.common import *
import traceback


def download(self, filename, buf_size=2000):
    logging.info('i download file handler : ', filename)
    # Content-Type这里我写的时候是固定的了，也可以根据实际情况传值进来
    self.set_header('Content-Type', 'application/octet-stream')
    self.set_header('Content-Disposition', 'attachment; filename=' + filename)
    # 读取的模式需要根据实际情况进行修改
    with open(filename, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            self.write(data)
    # 记得要finish
    self.finish()


RETURN_TYPE = {
    "text": lambda res: "self.write('''%s''')" % res,
    "json": lambda res: "self.write(json.dumps(%s, **fkwargv))" % res,
    "redirect": lambda res: "self.redirect('''%s''', **fkwargv)" % res,
    "template": lambda res: "self.render('''%s''', **fkwargv)" % res,
    "file": lambda res: "download(self, '''%s'', **fkwargv)" % res,
}


def set_kwargv_req_info(self, kwargv):
    # 获取header信息
    kwargv['headers'] = self.request.headers
    kwargv['remote_ip'] = self.request.remote_ip 
    kwargv['files'] = self.request.files
    # 获取cookie信息
    kwargv['cookies'] = self.cookies
    kwargv['func'] = {
        'set_cookie': self.set_cookie,
        'set_secure_cookie': self.set_secure_cookie,
        'get_secure_cookie': self.get_secure_cookie,
        'set_header': self.set_header,
    }
   


def gen_func(configs, root, api_name, method='get'):
    api_configs = configs[api_name]
    _module = append_api_path(root, api_name)
    
    def pfunc(self, *argv, **kwargv):
        # 获取传入的参数
        errs = None
        fkwargv = {}
        for param in api_configs.get(PARAMS, {}):
            errs = parse_param(api_configs, param, kwargv, self.get_argument)
            if errs:
                break
        
        if errs:
            PARAMS_SET['json'](fkwargv, configs)
            exec(RETURN_TYPE['json'](errs))  # 参数有误，返回报错
        else:
            set_kwargv_req_info(self, kwargv)
            # 执行api逻辑
            res = getattr(_module, method)(*argv, **kwargv)
            if len(res) > 2:
                fkwargv = res[2]
            PARAMS_SET[res[0]](fkwargv, configs)
            exec(RETURN_TYPE[res[0]](res[1]))  # 返回结果

    return pfunc


def gen_api(configs, root, api_name, api_postfix):
    class APIRequestHandler(tornado.web.RequestHandler):
        pass

    for method in configs[api_name][METHODS]:
        func = gen_func(configs, root, api_name, method)
        if method == 'get':
            APIRequestHandler.get = func
        elif method == 'post':
            APIRequestHandler.post = func

    return api_postfix, APIRequestHandler


def gen_apis(configs, root):
    apis = []
    prefix = configs[NAME][PREFIX]
    for api in configs:
        if api == NAME:
            continue

        # print(prefix, api)
        postfix = prefix + api    
        apis.append(gen_api(configs, root, api, postfix))
    
    return apis


def gen_app(configs, root, apis):
    settings = {
        "template_path": root + configs[NAME][TEMPLATE],
        "static_path": root + configs[NAME][STATIC],
        # static文件设置别名
        "static_url_prefix": "/%s/" % configs[NAME][STATIC]
    }
    return tornado.web.Application(apis, **settings)


def start(configs, root):
    '''
    web程序入口
    :param configs:
    :param root:
    :return:
    '''
    apis = gen_apis(configs, root)
    app = gen_app(configs, root, apis)
    # app.listen(config[NAME][PORT], address=config[NAME][HOST])
    server = HTTPServer(app)
    server.bind(configs[NAME][PORT], configs[NAME][HOST])
    server.start(configs[NAME][PROCESSES])
    tornado.ioloop.IOLoop.current().start()
