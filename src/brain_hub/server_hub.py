import os, sys
import logging
import yaml
import importlib
from brain_hub.conf import *
from brain_hub.exceptions import *
ROOT = SLASH.join(__file__.split(SLASH)[: -1])
sys.path.append(ROOT + '/server_tools')
RESULT_INIT = {
    'text': lambda **config: DEFAULT_TEXT_RETURN,
    'json': lambda **config: DEFAULT_JSON_RETURN,
    'redirect': lambda **config: DEFAULT_REDIRECT_RETURN.format(**config),
    'template': lambda **config: DEFAULT_TEMPLATE_RETURN,
    'file': lambda **config: DEFAULT_FILE_RETURN,
}
with open(ROOT + '/templates/api_template.py', 'r') as reader:
    API_FILE = reader.read()


def get_default(_dict, key, default=None):
    if _dict.get(key) is None:
        return default
    else:
        return _dict[key]


def check_prefix(config):
    prefix = get_default(config[NAME], PREFIX, DEFAULT_PREFIX)
    if not prefix.endswith(SLASH):
        prefix += SLASH
    if prefix[0] != SLASH:
        prefix = SLASH + prefix
    config[NAME][PREFIX] = prefix


def check_config(config, name, default=None, e=None):
    v = get_default(config[NAME], name, default)
    if v is None and e:
        raise e
    else:
        config[NAME][name] = v


def check(config):
    check_config(config, PORT, e=PortMissedException("port has to be declared!"))
    check_prefix(config)
    check_config(config, STATIC, STATIC)
    check_config(config, TEMPLATE, TEMPLATE)
    check_config(config, HOST, DEFAULT_HOST)
        

def run(config, root):
    check(config)
    print('running application: ', config[NAME][PROJECT_NAME], '%s:%s' % (config[NAME][HOST], config[NAME][PORT]))
    hub = __import__(UNDERLINE + config[NAME][HUB])
    sys.path.append(root)
    hub.start(config, root)


def init_api_file(pwd, api, config, sub_config):
    with open('%s%s.py' % (pwd, api), 'w') as writer:
        writer.write("# -*- coding:utf-8 -*-" + LINE_FEED)
        for method in sub_config[METHODS]:
            content = API_FILE.format(
                method=method, params=', '.join(sub_config[PARAMS].keys()), 
                return_format=sub_config.get(RETURN, DEFAULT_RETURN), 
                result_init=RESULT_INIT[sub_config.get(RETURN, DEFAULT_RETURN)](**config[NAME])
                )
            writer.write(content) 


def init(config, root, rebuild=False):
    for api in config:
        if api == NAME:
            continue

        paths = api.split(SLASH)
        pwd = root
        if len(paths) > 1:
            pwd = root + SLASH.join(paths[: -1]) + SLASH

        os.system("mkdir -p %s" % pwd)
        init_file = "%s/.%s" % (pwd, paths[-1])
        if not rebuild and os.path.exists(init_file):
            print("api %s was already initialized, skip" % api)
            continue

        init_api_file(pwd, paths[-1], config, config[api])
        os.system("touch %s" % init_file)
        print("api %s init ok" % api)


def main():
    if len(sys.argv) > 2:
        config_path = sys.argv[1]
        mode = sys.argv[2]
        rebuild = sys.argv[3] if len(sys.argv) > 3 else 0
    else:
        print("usage: brainserver <config path> <mode> [rebuild]\n- mode\n\tinit: init api files\n\trun: run server\n- rebuild:\n\t1: rebuild")
        exit(-1)

    with open(config_path) as f: 
        config = yaml.load(f)
    
    root = SLASH.join(config_path.split(SLASH)[: -1]) + '/%s/' % config[NAME][PROJECT_NAME]
    if mode == 'run':
        run(config, root)
    elif mode == 'init':
        init(config, root, rebuild == IS_REBUILD)


if __name__ == '__main__':
    main()
