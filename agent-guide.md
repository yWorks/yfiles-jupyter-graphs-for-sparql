# yFiles Jupyter Graphs for SPARQL Agent Guide

Reference for coding agents working with `yfiles-jupyter-graphs-for-sparql` (v2.x).

## Purpose

This package is a SPARQL adapter around [`yfiles-jupyter-graphs`](https://github.com/yWorks/yfiles-jupyter-graphs).
`SparqlGraphWidget` executes a query through a `SPARQLWrapper` instance, converts the result into the node and
edge data expected by `GraphWidget`, applies SPARQL-specific mappings, and renders the resulting Jupyter widget.

The package is not a general SPARQL result-table viewer. It is designed to visualize RDF triples.

## Install

```bash
pip install yfiles_jupyter_graphs_for_sparql SPARQLWrapper
```

The package requires `yfiles_jupyter_graphs~=2.0`. `SPARQLWrapper` is needed by the public query API but is not
listed as a package dependency, so applications should install it explicitly.

**Google Colab:** enable the custom widget manager before displaying the widget:

```python
try:
    import google.colab
    from google.colab import output
    output.enable_custom_widget_manager()
except:
    pass
```

## Core import pattern

```python
from SPARQLWrapper import JSON, SPARQLWrapper
from yfiles_jupyter_graphs_for_sparql import SparqlGraphWidget
```

## Minimal working example

For a `SELECT` query, use JSON and select variables whose names start with `s`, `p`, and `o`:

```python
wrapper = SPARQLWrapper("https://dbpedia.org/sparql")
wrapper.setReturnFormat(JSON)

widget = SparqlGraphWidget(wrapper=wrapper, limit=10)
widget.show_query("""
    SELECT ?s ?p ?o
    WHERE { ?s ?p ?o }
    LIMIT 10
""")
```

`show_query()` displays the widget itself; an additional `display()` call is normally not required.

`CONSTRUCT` and `DESCRIBE` queries can return an RDF graph. The examples use XML for this path:

```python
from SPARQLWrapper import XML

wrapper.setReturnFormat(XML)
widget.show_query("""
    CONSTRUCT { ?s ?p ?o }
    WHERE { ?s ?p ?o }
    LIMIT 10
""")
```

## `SparqlGraphWidget` constructor

| Argument | Type | Notes | Default |
|---|---|---|---|
| `wrapper` | `SPARQLWrapper`-compatible object | Connector used to execute queries. | `None` |
| `limit` | `int` | Maximum result count applied to queries. | `50` |
| `layout` | `str` | Default graph layout passed to the underlying widget. | `"organic"` |

Supported layout strings are `circular`, `circular_straight_line`, `hierarchical`, `organic`,
`interactive_organic`, `orthogonal`, `radial`, `tree`, `map`, `orthogonal_edge_router`, and
`organic_edge_router`.

The constructor values are mutable properties:

```python
widget.limit = 100
widget.layout = "hierarchical"
widget.wrapper = SPARQLWrapper("https://dbpedia.org/sparql")
```

The older `get_limit`, `set_limit`, `get_layout`, `set_layout`, `get_wrapper`, and `set_wrapper` methods are
deprecated. Prefer direct property access.

## Query behavior

### `show_query(query, layout=None)`

`show_query` requires a configured wrapper. The optional `layout` overrides the widget's default for that render
only.

The query limit is enforced before execution:

- if there is no numeric `LIMIT`, `LIMIT <widget.limit>` is appended;
- if the query limit is greater than `widget.limit`, it is reduced;
- a smaller existing limit is preserved.

For JSON `SELECT` results, each row is converted by taking the first binding whose variable name starts with
`s`, `p`, and `o`. Select all three triple components. For example, `?sub ?predicate ?object` works because the
variable names start with the required letters. A result that does not provide a complete subject-predicate-object
triple cannot produce a meaningful graph.

For `CONSTRUCT` and `DESCRIBE`, the converted RDF graph is iterated as `(subject, predicate, object)` triples.

### `show_schema()`

`show_schema()` runs schema-oriented queries for classes, properties, domains, ranges, and connections, then renders
the result using a hierarchical layout. It requires a wrapper. The method temporarily switches a non-JSON wrapper
to JSON and restores its previous return format; the Getting Started notebook demonstrates the XML setup used for
this method.

## RDF-to-graph conversion

The adapter creates dictionaries consumed by `GraphWidget`:

- URI subjects and URI objects become nodes with `id` and `properties`.
- URI nodes receive `properties["label"]` containing the fragment or final path component, and
  `properties["full_label"]` containing the original term.
- URI objects create directed edges. The edge label is the extracted predicate name and
  `properties["full_label"]` retains the complete predicate URI.
- RDF literals are stored as properties on the subject under the extracted predicate name. Literals do not become
  separate object nodes or edges.

URI label extraction uses the text after `#`, otherwise the final non-empty `/`-separated component. Non-URI
terms retain their string representation.

## Data-driven configuration

Configurations are stored on the `SparqlGraphWidget` instance and must be added before `show_query`.
Predicate arguments accept either one string or a list of strings. Matching is based on the predicate text for
subject/object configurations and on the extracted edge label for predicate configurations.

### Node configurations

```python
widget.add_subject_configuration("director", color="#2F6BFF", text="label")
widget.add_object_configuration("starring", color="purple", size=(60, 60))
```

`add_subject_configuration(predicate, **kwargs)` applies to subjects in triples whose predicate matches.
`add_object_configuration(predicate, **kwargs)` applies to objects in matching triples.

Node configuration bindings may include `text`, `color`, `size`, `styles`, `property`, `type`, `heat`,
`coordinate`, `scale_factor`, `position`, and `layout`. `text` is translated to the core widget's `label` mapping.
The `styles` dictionary supports the core widget's node style attributes, including `color`, `shape`, and `image`.

### Edge configurations

```python
widget.add_predicate_configuration(
    ["director", "producer"],
    color="orange",
    thickness_factor=2,
    text=lambda edge: edge["properties"]["label"].title(),
)
widget.add_predicate_configuration("*", color="#999999")
```

`add_predicate_configuration(predicate, **kwargs)` supports `text`, `color`, `thickness_factor`, `property`,
`styles`, and `heat`. The `*` key is the fallback for all predicate labels without a more specific configuration.

### Binding resolution

For all configuration values:

1. A callable is invoked with the graph item dictionary and its return value is used.
2. A non-dictionary string is first looked up in `item["properties"]`.
3. If no property with that name exists, the string is used as a constant.
4. Other values are used directly.

This means a string that happens to be both a property name and a desired constant resolves to the property. Use a
callable such as `lambda item: "label"` when a constant string must be forced.

### Removing configurations

```python
widget.del_subject_configuration("director")
widget.del_object_configuration(["starring", "producer"])
widget.del_predicate_configuration("director")
```

Each deletion method accepts a string or list; `"*"` clears the corresponding configuration dictionary.
The implemented edge deletion method is `del_predicate_configuration`.

## Grouping and nesting

```python
widget.add_parent_configuration("director")
widget.add_parent_configuration("starring", reverse=True)
widget.show_query(query, layout="hierarchical")
```

`add_parent_configuration(predicate, reverse=False)` converts matching relationships into parent-child nesting and
removes those edges from the displayed graph. By default, the target is the parent; `reverse=True` makes the source
the parent. A list of predicates is accepted. Remove these rules with `del_parent_predicate_configuration`.

Subject and object configurations also support `parent_configuration` for creating group nodes based on a property,
a constant, or a dictionary such as `{"text": "People", "color": "#9F4499"}`. See
`examples/configurations_example.ipynb` for the complete grouping example.

## Delegated core-widget features

The rendered object is an instance of `yfiles_jupyter_graphs.GraphWidget`, available as `widget.widget` after a
query render. The core widget supplies the toolbar, selection, search, neighborhood, overview, labels, styles, and
additional mapping APIs. Consult the [core widget agent guide](https://github.com/yWorks/yfiles-jupyter-graphs/blob/main/agent-guide.md)
for those features.

When a new query is rendered, this adapter creates a new `GraphWidget` and reapplies its stored SPARQL mappings.
Changes made directly to `widget.widget` should therefore be treated as render-specific unless they are also
represented by an adapter configuration.

## Implementation caveats

- The JSON `SELECT` path stores the raw triple rows for applying adapter mappings. The graph-returning
  `CONSTRUCT`/`DESCRIBE` path does not currently populate that internal result cache, so wrapper-level mappings
  should be tested carefully with those query types.
- `show_schema()` is demonstrated with an XML/non-JSON wrapper return format. Keep this setup when working around
  the current JSON return-format restoration path.
- The adapter uses extracted predicate labels for edge configuration matching, while subject/object matching checks
  the predicate text. Prefer concise local predicate names such as `director`, as used in the examples.

