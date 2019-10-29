import sys, json
from flask import Flask
from flask import request
from flask import render_template, redirect
from flask import make_response
from flask.views import MethodView
from brain_hub.conf import *
from brain_hub.utils import *
from brain_hub.exceptions import *
# https://flask.palletsprojects.com/en/1.1.x/quickstart/


def download(self, filename, buf_size=2000):
    print('i download file handler : ',filename)
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
    "text": lambda res: "'''%s'''" % res,
    "json": lambda res: "json.dumps(%s)" % res,
    "redirect": lambda res, **kwargv: "redirect('''%s''', **kwargv)" % res,
    "template": lambda res, **kwargv: "render_template('''%s''', **kwargv)" % res,
    "file": lambda res, **kwargv: "download(self, '''%s''', **kwargv)" % res,
}


def parse_param(configs, param, kwargv):
    errs = None
    try:
        default = configs[PARAMS][param].get('default')
        if request.method == "POST":
            value = request.form.get(param, default)
        elif request.method == "GET":
            value = request.args.get(param, default)

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


def set_kwargv_req_info(kwargv):
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


def gen_func(configs, root, api_name, method='GET'):
    _module = append_api_path(root, api_name)
    
    def api_func(*argv, **kwargv):
        # 获取传入的参数
        errs = None
        for param in configs.get(PARAMS, {}):
            errs = parse_param(configs, param, kwargv)
            if errs:
                break

        if errs:
            return eval(RETURN_TYPE['json'](errs))  # 参数有误，返回报错
        else:
            set_kwargv_req_info(kwargv)
            # 执行api逻辑
            res = ('text', 'Error request!')
            if request.method == "GET":
                res = _module.get(**kwargv)
            elif request.method == "POST":
                res = _module.post(**kwargv)

            if len(res) > 2:
                fkwargv = res[2]
            else:
                fkwargv = {}
            return eval(RETURN_TYPE[res[0]](res[1], **fkwargv))  # 返回结果

    return api_func


def gen_apis(configs, root, app):
    apis = []
    prefix = configs[NAME][PREFIX]
    for i, api in enumerate(configs):
        if api == NAME:
            continue

        postfix = prefix + api
        _methods = list(map(lambda m: m.upper(), configs[api]['method']))

        class ApiViewIndex(MethodView):
            methods = _methods

        for method in _methods:
            if method == 'GET':
                ApiViewIndex.get = gen_func(configs[api], root, api, method=method)
            elif method == 'POST':
                ApiViewIndex.post = gen_func(configs[api], root, api, method=method)

        app.add_url_rule(postfix, methods=_methods, view_func=ApiViewIndex.as_view(postfix))

    return apis


def gen_app(configs, root):
    app = Flask(configs[NAME][PROJECT_NAME], template_folder=root + configs[NAME][TEMPLATE],
                static_folder=root + configs[NAME][STATIC], static_url_path="/%s" % configs[NAME][STATIC])
    gen_apis(configs, root, app)
    return app


def start(configs, root):
    '''
    web程序入口
    :param configs:
    :param root:
    :return:
    '''
    app = gen_app(configs, root)
    processes = configs[NAME][PROCESSES]
    threads = configs[NAME][THREADS]
    if processes:
        app.run(host=configs[NAME][HOST], port=configs[NAME][PORT], debug=configs[NAME][DEBUG] == 'True', processes=processes)
    elif threads > 1:
        app.run(host=configs[NAME][HOST], port=configs[NAME][PORT], debug=configs[NAME][DEBUG] == 'True', threaded=True)
    else:
        app.run(host=configs[NAME][HOST], port=configs[NAME][PORT], debug=configs[NAME][DEBUG] == 'True')
