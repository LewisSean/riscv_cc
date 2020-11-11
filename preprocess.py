from subprocess import check_output

def preprocess_cmd(filename, gcc_path='gcc', cpp_args=''):
    """

    :param filename:  c source file
    :param gcc_path:  default 使用 win32 的 gcc 批处理指令
    :param cpp_args: gcc 参数  -E
    :return:  str 预处理之后的代码
    """
    path_list = [gcc_path]
    # print(cpp_args)
    if isinstance(cpp_args, list):
        path_list += cpp_args
    elif cpp_args != '':
        path_list += [cpp_args]
    path_list += [filename]

    try:

        text = check_output(path_list, universal_newlines=True)
    except OSError as e:
        raise RuntimeError("Unable to invoke 'gcc'.  " +
                           'Make sure its PATH was passed correctly\n' +
                           ('Original error: %s' % e))

    # print(text)
    return text


if __name__ == '__main__':
    preprocess_cmd(r'C:/users/Sean/Desktop/pycparser-master/examples/c_files/year.c',
                   'gcc',
                   ['-E', r'C:/users/Sean/Desktop/pycparser-master/utils/fake_libc_include'])
