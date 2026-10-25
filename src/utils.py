def list_to_str(_list): #make this an overload of List?
    combined_str = ""
    for str_ in [str(elem) for elem in _list]:
        combined_str += str_
    if combined_str is None:
        raise ValueError("idiot")
    return combined_str

def spaced_str(str, min_len):
    return str + ' ' * (min_len - len(str))

def log(msg, do_log=False):
    if do_log:
        print(msg)
