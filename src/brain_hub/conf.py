import platform


ENCODE = 'utf-8'
PY_HEADER = "# -*- coding:%s -*-" % ENCODE

# project configs
NAME = 'brainhub'
PROJECT_NAME = 'name'
PROCESSES = 'processes'
DEFAULT_PROCESSES = '1'
THREADS = 'threads'
DEFAULT_THREADS = '1'
HOST = 'domain'
DEFAULT_HOST = 'localhost'
PORT = 'port'
PREFIX = 'prefix'
DEFAULT_PREFIX = '/'
POSTFIX = 'postfix'
HUB = 'hub'
DEFAULT_HUB = 'tornado'
LOG = 'log'
DEFAULT_LOG = 'log'
STATIC = 'static'
TEMPLATE = 'template'
DEBUG = 'debug'
INCLUDE = 'include'
DEFAULT_INCLUDE = []

# api configs
INDEX_API_NAME = '__index__'
COMMENT = 'comment'
METHODS = 'method'
PROTOCAL = 'protocal'
VERSION = 'version'
RETURN = 'return'
DEFAULT_RETURN = 'text'
RESULT = 'result'
PARAMS = 'params'
DEFAULT_PARAMS = {}
FORMAT = 'format'
DEFAULT = 'default'
ERR_MSG = 'err_msg'

# api return default values
DEFAULT_TEXT_RETURN = "'hello world'"
DEFAULT_JSON_RETURN = "{}"
DEFAULT_REDIRECT_RETURN = "'http://%s:%s'"
DEFAULT_TEMPLATE_RETURN = "''"
DEFAULT_FILE_RETURN = "''"

# runtime configs
IS_REBUILD = '1'

# constants
SLASH = '/'
LINE_FEED = '\n'
if platform.system() == 'Windows':
    SLASH = '\\'
    LINE_FEED = '\r\n'
UNDERLINE = '_'
TAB = '\t'
DOT = '.'

RESULT_INIT = {
    'text': lambda **config: DEFAULT_TEXT_RETURN,
    'json': lambda **config: DEFAULT_JSON_RETURN,
    'redirect': lambda **config: DEFAULT_REDIRECT_RETURN.format(**config),
    'template': lambda **config: DEFAULT_TEMPLATE_RETURN,
    'file': lambda **config: DEFAULT_FILE_RETURN,
}
