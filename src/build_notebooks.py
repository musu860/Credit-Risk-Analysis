"""Convert the '# %%' cell-marked scripts into .ipynb notebooks (no Jupyter needed)."""
import json, re
def build(src, dst):
    cells = []
    for block in re.split(r"(?m)^# %%", open(src).read())[1:]:
        md = block.startswith(" [markdown]")
        body = block.split("\n", 1)[1].strip("\n") if "\n" in block else ""
        if md:
            body = "\n".join(l[2:] if l.startswith("# ") else l.lstrip("#") for l in body.splitlines())
            cells.append({"cell_type": "markdown", "metadata": {}, "source": body})
        else:
            cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": body})
    nb = {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}}
    json.dump(nb, open(dst, "w"), indent=1)
build("src/01_data_cleaning.py", "notebooks/01_data_cleaning.ipynb")
build("src/03_eda.py", "notebooks/03_eda.ipynb")
print("notebooks built")
