def get_objs(str, variables):
    out = []
    for name, obj in variables.items():
        if str in name: out.append(obj)
    return out