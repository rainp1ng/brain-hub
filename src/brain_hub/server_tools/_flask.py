import sys, json
from flask import Flask
from flask import request
from flask import render_template, redirect
from flask import make_response
from flask.views import MethodView
from brain_hub.conf import NAME
from brain_hub.exceptions import *
# https://flask.palletsprojects.com/en/1.1.x/quickstart/


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
    "text": lambda res: "'''%s'''" % res,
    "json": lambda res: "json.dumps(%s)" % res,
    "redirect": lambda res: "redirect('''%s''')" % res,
    "template": lambda res: "render_template('''%s''')" % res,
    "file": lambda res: "download(self, '''%s''')" % res,
}


def gen_func(config, root, api_name, method='GET'):
    paths = api_name.split(SLASH)
    if len(paths) > 1:
        path = SLASH.join(paths[: -1])
        sys.path.append(root + path)
    _module = __import__(paths[-1])
    
    def api_func(*argv, **kwargv):
        # 获取传入的参数
        for param in config[PARAMS]:
            default = config[PARAMS][param].get('default')
            if request.method == "POST":
                kwargv[param] = request.form.get(param, default)
            elif request.method == "GET":
                kwargv[param] = request.args.get(param, default)
            
        # 获取header信息
        kwargv['headers'] = request.headers
        kwargv['remote_ip'] = request.remote_addr
        # 获取cookie信息
        kwargv['cookies'] = request.cookies
        # 功能函数
        cookies = {}
        def set_cookie(k, v):
            cookies[k] = v

        kwargv['func'] = {
            'set_cookie': set_cookie,
            'set_secure_cookie': None,
            'get_secure_cookie': None,
            'set_header': None,
        }
        # 执行api逻辑
        if request.method == "GET":
            res = _module.get(**kwargv)
        elif request.method == "POST":
            res = _module.post(**kwargv)

        return eval(RETURN_TYPE[res[0]](res[1]))  # 返回结果

    return api_func


def gen_apis(config, root, app, func=None):
    apis = []
    prefix = config[NAME][PREFIX]
    for i, api in enumerate(config):
        if api == NAME:
            continue

        postfix = prefix + api
        _methods = list(map(lambda m: m.upper(), config[api]['method']))
        class ApiViewIndex(MethodView):
            methods = _methods

        for method in _methods:
            if method == 'GET':
                ApiViewIndex.get = gen_func(config[api], root, api, method=method)
            elif method == 'POST':
                ApiViewIndex.post = gen_func(config[api], root, api, method=method)

        app.add_url_rule(postfix, methods=_methods, view_func=ApiViewIndex.as_view(postfix))

    return apis


def gen_app(config, root):
    app = Flask(config[NAME][PROJECT_NAME], template_folder=root + config[NAME][TEMPLATE], 
        static_folder=root + config[NAME][STATIC], static_url_path="/%s" % config[NAME][STATIC])
    gen_apis(config, root, app)
    return app


def start(config, root):
    app = gen_app(config, root)
    app.run(host=config[NAME][HOST], port=config[NAME][PORT], debug=config[NAME][DEBUG] == 'True')
