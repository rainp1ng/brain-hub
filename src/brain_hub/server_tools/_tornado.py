import sys, json
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
from brain_hub.conf import *
from brain_hub.exceptions import *


def download(self, filename):
    print('i download file handler : ',filename)
    # Content-Type这里我写的时候是固定的了，也可以根据实际情况传值进来
    self.set_header ('Content-Type', 'application/octet-stream')
    self.set_header ('Content-Disposition', 'attachment; filename=' + filename)
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
    "json": lambda res: "self.write(json.dumps(res))" % res,
    "redirect": lambda res: "self.redirect('''%s''')" % res,
    "template": lambda res: "self.render('''%s''')" % res,
    "file": lambda res: "download(self, '''%s''')" % res,
}


def gen_func(config, root, api_name, method='get'):
    paths = api_name.split(SLASH)
    if len(paths) > 1:
        path = SLASH.join(paths[: -1])
        sys.path.append(root + path)
    _module = __import__(paths[-1])
    
    def pfunc(self, *argv, **kwargv):
        # 获取传入的参数
        for param in config[PARAMS]:
            default = config[PARAMS][param].get('default')
            kwargv[param] = self.get_argument(param, default)
        
        # 获取header信息
        kwargv['headers'] = self.request.headers
        kwargv['remote_ip'] = self.request.remote_ip 
        # 获取cookie信息
        kwargv['cookies'] = self.cookies
        kwargv['func'] = {
            'set_cookie': self.set_cookie,
            'set_secure_cookie': self.set_secure_cookie,
            'get_secure_cookie': self.get_secure_cookie,
            'set_header': self.set_header,
        }
        # 执行api逻辑
        res = getattr(_module, method)(*argv, **kwargv)
        # print('res:', res)
        exec(RETURN_TYPE[res[0]](res[1]))  # 返回结果

    return pfunc


def gen_api(config, root, api_name, api_postfix):
    class APIRequestHandler(tornado.web.RequestHandler):
        pass

    for method in config[METHODS]:
        func = gen_func(config, root, api_name, method)
        if method == 'get':
            APIRequestHandler.get = func
        elif method == 'post':
            APIRequestHandler.post = func

    return (api_postfix, APIRequestHandler)


def gen_apis(config, root):
    apis = []
    prefix = config[NAME][PREFIX]
    for api in config:
        if api == NAME:
            continue

        # print(prefix, api)
        postfix = prefix + api    
        apis.append(gen_api(config[api], root, api, postfix))
    
    return apis


def gen_app(config, root, apis):
    settings={
        "template_path": root + config[NAME][TEMPLATE],
        "static_path": root + config[NAME][STATIC],
        # static文件设置别名
        "static_url_prefix": "/%s/" % config[NAME][STATIC],
    }
    return tornado.web.Application(apis, **settings)


def start(config, root):
    apis = gen_apis(config, root)
    app = gen_app(config, root, apis)
    # app.listen(config[NAME][PORT], address=config[NAME][HOST])
    server = HTTPServer(application)
    server.bind(config[NAME][PORT], config[NAME][HOST])
    server.start(config[NAME][PROCESSES])
    tornado.ioloop.IOLoop.current().start()
