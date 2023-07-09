def get_objs(str, variables, verbose=False):
    out = []
    for name, obj in variables.items():
        if str in name:
            if verbose: print("get_objs():", name)
            out.append(obj)
    return out


def format_coord(x, y, data_plot, data_aux=[], sep="\n"):
    try:
        tol = abs(0.5 * data_plot.rio.resolution()[0])
        # TODO: refine prefactor for resolution
        val = data_plot.sel(x=x, y=y, method="nearest", tolerance=tol).values

        per_d = []
        for d_ in data_aux:
            name = d_.name
            val_ = d_.sel(x=x, y=y, method="nearest", tolerance=tol).values
            per_d.append(f"{name}: {val_:.2f}")
        return f"({x:.2f}, {y:.2f}){sep}{val:.3}\n" + "\n".join(per_d)

    except Exception as e:
        if "not all values found in index" in str(e):
            return f"({x:.2f}, {y:.2f})\nOut of bounds"
        else:
            raise e
