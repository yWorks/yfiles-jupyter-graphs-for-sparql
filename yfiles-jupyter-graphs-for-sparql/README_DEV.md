# How to build this project

Open a terminal in the yfiles-jupyter-graphs-for-sparql directory and execute the following commands:

Ensure you have build installed:
```bash 
py -m pip install --upgrade pip
py -m pip install --upgrade build
```

Then build the project: 

```bash
py -m build
```

This creates two files in the dist folder,  
- yfiles_jupyter_graphs_for_sparql-1.0.0b0.tar.gz and 
- yfiles_jupyter_graphs_for_sparql-1.0.0b0-py3-none-any.whl

To use the build package install either one of them: 

```bash
pip install dist/yfiles_jupyter_graphs_for_sparql-1.0.0b0.whl
```

Now you're ready to use this in jupyter lab or jupyter notebook.