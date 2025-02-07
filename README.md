# yFiles-Jupyter Graphs For SPARQL

Easily visualize a [RDF](https://rdflib.readthedocs.io/en/stable/) query as a graph in a Jupyter Notebook.

This packages provides an easy-to-use interface to
the [yFiles Graphs for Jupyter](https://github.com/yWorks/yfiles-jupyter-graphs) widget to directly visualize queries.

## Installation

```bash
pip install yfiles_jupyter_graphs_for_sparql
```

## Usage

```python
from yfiles_jupyter_graphs_for_sparql import SparqlGraphWidget

g = SparqlGraphWidget(data="https://ld.cultural.jp/sparql")

q = """
    SELECT DISTINCT ?sub ?p ?ob
    WHERE {
        ?sub ?p ?ob .
    }
    """
g.show_query(q)
```

See
[examples](https://github.com/yWorks/yfiles-jupyter-graphs-for-sparql/tree/main/examples)

## Supported Environments

The widget uses yFiles Graphs for Jupyter at its core, and therefore runs in any environment that is supported by it,
see [supported environments](https://github.com/yWorks/yfiles-jupyter-graphs/tree/main?tab=readme-ov-file#supported-environments).

## Documentation

The main class `SparqlGraphWidget` provides the following API:

### Constructor

- `SparqlGraphWidget`: Creates a new class instance with the following arguments

| Argument | Description                                  | Default   |
|----------|----------------------------------------------|-----------|
| `data`   | The data endpoint the queries are sent to    | `None`    |
| `limit`  | The node limit which is added to all queries | `50`      |
| `layout` | Can be used to specify a general default node and edge layout. Available algorithms are: "circular", "hierarchic", "organic", "interactive_organic_layout", "orthogonal", "radial", "tree", "map", "orthogonal_edge_router", "organic_edge_router" | `organic` |


### Methods 

> [!IMPORTANT]  
> If you want to use SELECT query types, ensure you select all three triple components—subject, predicate, and object. Otherwise, a graph cannot be constructed from the selected data.
> For an ex

- `show_query(query)`
    - `query`: The [query](https://neo4j.com/docs/cypher-manual/current/introduction/)

To get an overview of the data structure, you can use the following function. 
The output is constrained by the `limit` property, meaning 
only a partial schema may be displayed depending on the dataset.
- `show_schema()`
  


The graph visualization can be adjusted by adding configurations to each node label or edge type with the following
functions:

- `add_subject_configuration(predicate: Union[str, list[str]], **kwargs: Dict[str, Any])`
    - `predicate`: The predicate of the subject this configuration should be used for.
    - `**kwargs`: Visualization configuration for the given node label. The following arguments are supported:
        - `text`: The text that displayed at the node. By default, the node's label is used.
        - `color`: A convenience color binding for the node (see also `styles` argument).
        - `size`: The size of the node.
        - `styles`: A dictionary that may contain the following attributes `color`, `shape` (one of 'ellipse', '
          hexagon', 'hexagon2', 'octagon', 'pill', 'rectangle', 'round-rectangle' or 'triangle'), `image`.
        - `property`: Allows to specify additional properties on the node, which may be bound by other bindings.
        - `type`: Defines a specific "type" for the node as described
          in [yFiles Graphs for Jupyter](https://yworks.github.io/yfiles-jupyter-graphs/02_graph_widget/#def-default_node_type_mappingindex-node)
          which affects the automatic positioning of nodes (same "type"s are preferred to be placed next to each other).

- `add_object_configuration(predicate:  Union[str, list[str]], **kwargs: Dict[str, Any])`
    - `predicate`: The predicate of the object this configuration should be used for.
    - `**kwargs`: Visualization configuration for the given node label. The following arguments are supported:
        - `text`: The text that displayed at the node. By default, the node's label is used.
        - `color`: A convenience color binding for the node (see also `styles` argument).
        - `size`: The size of the node.
        - `styles`: A dictionary that may contain the following attributes `color`, `shape` (one of 'ellipse', '
          hexagon', 'hexagon2', 'octagon', 'pill', 'rectangle', 'round-rectangle' or 'triangle'), `image`.
        - `property`: Allows to specify additional properties on the node, which may be bound by other bindings.
        - `type`: Defines a specific "type" for the node as described
          in [yFiles Graphs for Jupyter](https://yworks.github.io/yfiles-jupyter-graphs/02_graph_widget/#def-default_node_type_mappingindex-node)
          which affects the automatic positioning of nodes (same "type"s are preferred to be placed next to each other).

- `add_predicate_configuration(type:  Union[str, list[str]], **kwargs: Dict[str, Any])`
    - `type`: The predicate type for which this configuration should be used.
    - `**kwargs`: Visualization configuration for the given predicate type. The following arguments are supported:
        - `text`: The text that displayed at the edge. By default, the predicate's type is used.
        - `color`: The edge's color.
        - `thickness_factor`: The edge's stroke thickness factor. By default, `1`.
        - `property`: Allows to specify additional properties on the edge, which may be bound by other bindings.

To remove a configuration use the following functions: 

- `del_object_configuration(type)`: Deletes configuration for the given object predicate type.
- `del_subject_configuration(type)`: Deletes configuration for the given subject predicatetype.
- `del_edge_configurations(type)`: Deletes configuration for the given predicate type.

## How configuration bindings are resolved

The configuration bindings (see `add_object_configuration, add_subject_configuration` or `add_predicate_configuration`) are resolved as follows:

If the configuration binding is a string, the package first tries to resolve it against the item's properties
and uses the property value if available. If there is no property with the given key, the string value itself is used as
a constant binding.

In case you want to create a constant string value as binding, which also happens to be a property key, use a binding
function with a constant string as return value instead.

If the configuration binding is a function, the return value of the function is used as value for the respective
configuration.

## yFiles Graphs for Jupyter

The graph visualization is provided by [yFiles Graphs for Jupyter](https://github.com/yWorks/yfiles-jupyter-graphs), a
versatile graph visualization widget for Jupyter Notebooks.

It can import and visualize graphs from various popular Python packages
(e.g. [NetworkX](https://github.com/yWorks/yfiles-jupyter-graphs/blob/main/examples/13_networkx_import.ipynb), 
[PyGraphviz](https://github.com/yWorks/yfiles-jupyter-graphs/blob/main/examples/15_graphviz_import.ipynb),
[igraph](https://github.com/yWorks/yfiles-jupyter-graphs/blob/main/examples/17_igraph_import.ipynb)) or just structured
[node and edge lists](https://github.com/yWorks/yfiles-jupyter-graphs/blob/main/examples/01_introduction.ipynb).

And provides a rich set of visualization options to bring your data to life (see
the [example notebooks](https://github.com/yWorks/yfiles-jupyter-graphs/blob/main/examples/00_toc.ipynb)).

### Feature Highlights

<table>
    <tr>
    </tr>
    <tr>
    </tr>
</table>

For a detailed feature guide, check out the main widget [example notebooks](https://colab.research.google.com/github/yWorks/yfiles-jupyter-graphs/blob/main/examples/00_toc.ipynb)

## Code of Conduct

This project and everyone participating in it is governed by
the [Code of Conduct](https://github.com/yWorks/yfiles-jupyter-graphs-for-sparql/blob/main/CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.
Please report unacceptable behavior to [contact@yworks.com](mailto:contact@yworks.com).

## Feedback

This widget is by no means perfect.
If you find something is not working as expected
we are glad to receive an issue report from you.
Please make sure
to [search for existing issues](https://github.com/yWorks/yfiles-jupyter-graphs-for-sparql/search?q=is%3Aissue) first
and check if the issue is not an unsupported feature or known issue.
If you did not find anything related, report a new issue with necessary information.
Please also provide a clear and descriptive title and stick to the issue templates.
See [issues](https://github.com/yWorks/yfiles-jupyter-graphs-for-sparql/issues).

## Dependencies

* [yFiles Graphs for Jupyter](https://github.com/yWorks/yfiles-jupyter-graphs)
* [rdfLib](https://rdflib.readthedocs.io/en/stable/)

## License
See [LICENSE](https://github.com/yWorks/yfiles-jupyter-graphs-for-sparql/blob/main/LICENSE.md) file.
