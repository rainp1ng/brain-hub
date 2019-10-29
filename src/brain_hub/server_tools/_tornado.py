import sys, json
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
from brain_hub.conf import *
from brain_hub.utils import *
from brain_hub.exceptions import *
import traceback


def download(self, filename, buf_size=2000):
    print('i download file handler : ', filename)
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
    "text": lambda res, **kwargv: "self.write('''%s''')" % res,
    "json": lambda res, **kwargv: "self.write(json.dumps(%s))" % res,
    "redirect": lambda res, **kwargv: "self.redirect('''%s''', **kwargv)" % res,
    "template": lambda res, **kwargv: "self.render('''%s''', **kwargv)" % res,
    "file": lambda res, **kwargv: "download(self, '''%s'', **kwargv)" % res,
}


def parse_param(self, configs, param, kwargv):
    errs = None
    try:
        default = configs[PARAMS][param].get('default')
        value = self.get_argument(param, default)
        if configs[PARAMS][param].get('err_msg') and not value:
            errs = {'msg': configs[PARAMS][param]['err_msg'], 'code': configs[PARAMS][param].get('err_code', -500)}
        else:
            _format = eval(configs[PARAMS][param].get('format', 'str'))
            kwargv[param] = _format(value)
    except Exception as e:
        traceback.print_exc()
        errs = {'msg': 'Parsing param %s err, Please contact admin! Error details: %s. ' % (param, str(e)), 'code': -1024}
    finally:
        return errs


def set_kwargv_req_info(self, kwargv):
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
   


def gen_func(configs, root, api_name, method='get'):
    _module = append_api_path(root, api_name)
    
    def pfunc(self, *argv, **kwargv):
        # 获取传入的参数
        errs = None
        for param in configs.get(PARAMS, {}):
            errs = parse_param(self, configs, param, kwargv)
            if errs:
                break
        
        if errs:
            exec(RETURN_TYPE['json'](errs))  # 参数有误，返回报错
        else:
            set_kwargv_req_info(self, kwargv)
            # 执行api逻辑
            res = getattr(_module, method)(*argv, **kwargv)
            if len(res) > 2:
                fkwargv = res[2]
            else:
                fkwargv = {}
            exec(RETURN_TYPE[res[0]](res[1], **fkwargv))  # 返回结果

    return pfunc


def gen_api(configs, root, api_name, api_postfix):
    class APIRequestHandler(tornado.web.RequestHandler):
        pass

    for method in configs[METHODS]:
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
        apis.append(gen_api(configs[api], root, api, postfix))
    
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
