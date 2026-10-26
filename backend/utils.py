def list_to_str(_list):
    return "".join(str(elem) for elem in _list)

def spaced_str(str, min_len):
    return str + ' ' * (min_len - len(str))

def log(msg, do_log=False):
    if do_log:
        print(msg)
