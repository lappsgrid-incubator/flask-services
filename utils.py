
def get_vars(request, var_names):
    return [get_var(request, var_name) for var_name in var_names]


def get_var(request, var_name):
    if request.method == 'GET':
        return request.args.get(var_name)
    elif request.method == 'POST':
        return request.form.get(var_name)
