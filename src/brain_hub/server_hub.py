import os, sys
import logging
import yaml
import importlib
from brain_hub.conf import NAME
from brain_hub.exceptions import *
ROOT='/'.join(__file__.split("/")[: -1])
sys.path.append(ROOT + '/server_tools')
RESULT_INIT = {
    'text': lambda **config: "'hello world'",
    'json': lambda **config: "{}",
    'redirect': lambda **config: "'http://%s:%s'".format(**config),
    'template': lambda **config: "''",
    'file': lambda **config: "''",
}
with open(ROOT + '/templates/api_template.py', 'r') as reader:
    API_FILE = reader.read()


def get_default(_dict, key, default=None):
    if _dict.get(key) is None:
        return default
    else:
        return _dict[key]


def check_prefix(config):
    prefix = get_default(config[NAME], 'prefix', '/')
    if not prefix.endswith("/"):
        prefix += '/'
    if prefix[0] != '/':
        prefix = '/' + prefix
    config[NAME]['prefix'] = prefix


def check_config(config, name, default=None, e=None):
    v = get_default(config[NAME], name, default)
    if v is None and e:
        raise e
    else:
        config[NAME][name] = v


def check(config):
    check_config(config, 'port', e=PortMissedException("port has to be declared!"))
    check_prefix(config)
    check_config(config, 'static', 'static')
    check_config(config, 'template', 'template')
    check_config(config, 'domain', '127.0.0.1')
        

def run(config, root):
    check(config)
    print('running application: ', config[NAME]['name'], '%s:%s' % (config[NAME]['domain'], config[NAME]['port']))
    hub = __import__('_' + config[NAME]['hub'])
    sys.path.append(root)
    hub.start(config, root)


def init_api_file(pwd, api, config, sub_config):
    with open('%s%s.py' % (pwd, api), 'w') as writer:
        writer.write("# -*- coding:utf-8 -*-\n")
        for method in sub_config['method']:
            content = API_FILE.format(
                method=method, params=', '.join(sub_config['params'].keys()), 
                return_format=sub_config.get('return', 'text'), 
                result_init=RESULT_INIT[sub_config.get('return', 'text')](**config[NAME])
                )
            writer.write(content) 


def init(config, root, rebuild=False):
    for api in config:
        if api == NAME:
            continue

        paths = api.split("/")
        pwd = root
        if len(paths) > 1:
            pwd = root + '/'.join(paths[: -1]) + '/'

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
    
    root = '/'.join(config_path.split("/")[: -1]) + '/%s/' % config[NAME]['name']
    if mode == 'run':
        run(config, root)
    elif mode == 'init':
        init(config, root, rebuild == '1')


if __name__ == '__main__':
    main()