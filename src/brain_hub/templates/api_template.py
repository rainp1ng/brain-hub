

def {method}({params}, *argv, **kwargv):  
    '''
    kwargv 还有 cookies, headers, remote_ip等信息,
    工具通过 func 获取, 含 set_header, set_cookie, set_secure_cookie, get_secure_cookie 等
    '''
    result = {result_init}
    return '{return_format}', result