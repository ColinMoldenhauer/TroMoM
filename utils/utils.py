def get_objs(str, variables, verbose=False):
    out = []
    for name, obj in variables.items():
        if str in name:
            if verbose: print("get_objs():", name)
            out.append(obj)
    return out


def format_coord(x, y, data_plot, data_aux=[], threshs_aux=[], sep="\n"):
    try:
        tol = abs(0.5 * data_plot.rio.resolution()[0])
        # TODO: refine prefactor for resolution
        val = data_plot.sel(x=x, y=y, method="nearest", tolerance=tol).values

        per_d = []
        for i, d_ in enumerate(data_aux):
            name = d_.name
            val_ = d_.sel(x=x, y=y, method="nearest", tolerance=tol).values
            per_d_ = f"{name}: {val_:.2f}"

            # find risk rating per layer
            if threshs_aux:
                for risk_level_, threshs_per_level_ in enumerate(threshs_aux[i][::-1], 1):  # 5 lists of lists
                    cat = ""
                    for risk_interval_ in threshs_per_level_:
                        lower, upper = risk_interval_
                        # increase risk level per pixel if value in interval and not NaN
                        if (val_ > lower) and (val_ <= upper):
                            cat = f" -> {risk_level_}"
                            break               # skip other intervals of current level if found
                    if cat != "": break   # skip other risk levels if found
                # if cat == "": cat = " -> no risk level found"
            else:
                cat = ""

            per_d_ += cat
            per_d.append(per_d_)
        return f"({x:.2f}, {y:.2f}){sep}{val:.3}\n" + "\n".join(per_d)

    except Exception as e:
        if "not all values found in index" in str(e):
            return f"({x:.2f}, {y:.2f})\nOut of bounds"
        else:
            raise e
