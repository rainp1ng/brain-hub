import sys
import logging
from brain_hub.conf import *


def parse_param(configs, param, kwargv, get_param_func):
    errs = None
    try:
        default = configs[PARAMS][param].get('default')
        value = get_param_func(param, default)
        if configs[PARAMS][param].get('err_msg') and not value:
            errs = {'msg': configs[PARAMS][param]['err_msg'], 'code': configs[PARAMS][param].get('err_code', -500)}
        else:
            _format = eval(configs[PARAMS][param].get('format', 'str'))
            kwargv[param] = _format(value)
    except Exception as e:
        # traceback.print_exc()
        logging.exception(sys.exc_info())
        errs = {'msg': 'Parsing param %s err, Please contact admin! Error details: %s. ' % (param, str(e)), 'code': -1024}
    finally:
        return errs


def json_params_set(fkwargv, configs):
    if configs[NAME].get(DEBUG, True):
        fkwargv['ensure_ascii'] = False


def text_params_set(fkwargv, configs):
    pass


def template_params_set(fkwargv, configs):
    pass


def redirect_params_set(fkwargv, configs):
    pass


def file_params_set(fkwargv, configs):
    pass


PARAMS_SET = {
    'json': json_params_set,
    'text': text_params_set,
    'template': template_params_set,
    'redirect': redirect_params_set,
    'file': file_params_set
}
