import os
import re
import sys
import time
import yaml
import logging
from brain_hub.conf import *
from brain_hub.exceptions import *
from brain_hub.templates.api_template import API_TEMPLATE


ROOT = SLASH.join(__file__.split(SLASH)[: -1])
sys.path.append(ROOT + '%sserver_tools' % SLASH)


def get_default(_dict, key, default=None):
    if _dict.get(key) is None:
        return default
    else:
        return _dict[key]


def check_prefix(configs):
    prefix = get_default(configs[NAME], PREFIX, DEFAULT_PREFIX)
    if prefix.endswith('/'):
        prefix = prefix[: -1]
    if len(prefix) > 0 and prefix[0] != '/':
        prefix = '/' + prefix
    configs[NAME][PREFIX] = prefix


def check_config(configs, name, default=None, _type=str, e=None):
    v = get_default(configs[NAME], name, default)
    if v is None and e:
        raise e
    else:
        configs[NAME][name] = _type(v)


def check(configs):
    check_config(configs, PORT, e=PortMissedException("port has to be declared!"))
    check_prefix(configs)
    check_config(configs, STATIC, STATIC)
    check_config(configs, TEMPLATE, TEMPLATE)
    check_config(configs, HOST, DEFAULT_HOST)
    check_config(configs, PROCESSES, DEFAULT_PROCESSES, int)
    check_config(configs, THREADS, DEFAULT_THREADS, int)
    logging.debug('config: %s ' % configs)


def run(configs, root):
    check(configs)
    logging.info('running application: %s %s' % (configs[NAME][PROJECT_NAME], '%s:%s' % (configs[NAME][HOST], configs[NAME][PORT])))
    hub = __import__(UNDERLINE + configs[NAME][HUB])
    sys.path.append(root)
    hub.start(configs, root)


def new_file(writer, configs, sub_config):
    writer.write(PY_HEADER + LINE_FEED)
    for method in sub_config[METHODS]:
        content = API_TEMPLATE.format(
            method=method, params=''.join([p + ', ' for p in sub_config.get(PARAMS, DEFAULT_PARAMS).keys()]),
            return_format=sub_config.get(RETURN, DEFAULT_RETURN), 
            result_init=RESULT_INIT[sub_config.get(RETURN, DEFAULT_RETURN)](**configs[NAME])
            )
        writer.write(content) 


def update_file(writer, configs, sub_config, old_content):
    new_content = ''
    for method in sub_config[METHODS]:
        origin = 'def {method}\([^\)]+\):'.format(method=method)
        new = 'def {method}({params}*argv, **kwargv):'.format(
            method=method, 
            params=''.join([p + ', ' for p in sub_config.get(PARAMS, DEFAULT_PARAMS).keys()])
        )
        new_content = re.sub(origin, new, old_content)
    writer.write(new_content)
        

def init_api_file(pwd, api, configs, sub_config, update=False):
    print('%s api %s' % ('update' if update else 'init', api))
    file_paths = api.split('/')
    _file = file_paths[-1]
    if _file == '':
        _file = INDEX_API_NAME
    file_pwd = '%s%s%s' % (pwd, SLASH.join(file_paths[: -1]), SLASH)
    if not os.path.exists(file_pwd):
        os.mkdir(file_pwd)

    api_file = '%s%s.py' % (file_pwd, _file)
    if update:
        with open(api_file, 'r', encoding=ENCODE) as reader:
            content = reader.read()
        with open(api_file, 'w', encoding=ENCODE) as writer:
            update_file(writer, configs, sub_config, content)
    else:
        with open(api_file, 'w', encoding=ENCODE) as writer:
            new_file(writer, configs, sub_config)


def init(configs, root, rebuild=False):
    check(configs)
    for api in configs:
        if api == NAME:
            continue

        paths = api.split('/')
        pwd = root
        if len(paths) > 1:
            pwd = root + SLASH.join(paths[: -1]) + SLASH

        if not os.path.exists(pwd):
            os.mkdir(pwd)
        init_file = "%s%s.%s" % (pwd, SLASH, paths[-1] if paths[-1] != '' else INDEX_API_NAME)
        update = False
        if not rebuild and os.path.exists(init_file):
            # print("api %s was already initialized (%s), skip" % (api, init_file))
            # continue
            update = True

        init_api_file(pwd, paths[-1], configs, configs[api], update)
        os.system("touch %s" % init_file)
        print("api %s init ok" % api)


def main():
    if len(sys.argv) > 2:
        mode = sys.argv[1]
        config_path = sys.argv[2]
        rebuild = sys.argv[3] if len(sys.argv) > 3 else 0

        with open(config_path, encoding=ENCODE) as f:
            configs = yaml.load(f, Loader=yaml.FullLoader)

        logs_path = configs[NAME].get(LOG, DEFAULT_LOG)
        for api_file in configs[NAME].get(INCLUDE, DEFAULT_INCLUDE):
            with open(api_file, encoding=ENCODE) as f:
                api_config = yaml.load(f, Loader=yaml.FullLoader) 
                # print(api_file, api_config)
                if api_config:
                    configs = dict(configs, **api_config)

        os.system("mkdir -p %s" % logs_path)
        logging.basicConfig(
            filename= logs_path + '/%s_%s.log' % (configs[NAME][PROJECT_NAME], time.strftime('%Y-%m-%d')),
            filemode="a",
            format="[%(asctime)s]%(name)s-%(levelname)s:%(message)s",
            level=logging.DEBUG if configs[NAME].get(DEBUG, True) else logging.INFO
        ) 

        config_pwd = SLASH.join(config_path.split(SLASH)[: -2])
        if config_pwd == '':
            config_pwd = '.'
        root = config_pwd + '%s%s%s' % (SLASH, configs[NAME][PROJECT_NAME], SLASH)
        if mode == 'run':
            run(configs, root)
        elif mode == 'init':
            init(configs, root, rebuild == IS_REBUILD)
    else:
        print("usage: brainserver <config path> <mode> [rebuild]\n- mode\n\tinit: init api files\n\trun: run server\n- rebuild:\n\t1: rebuild")
        exit(-1)


if __name__ == '__main__':
    main()
