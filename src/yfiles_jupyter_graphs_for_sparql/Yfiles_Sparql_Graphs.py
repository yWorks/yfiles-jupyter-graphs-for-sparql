import inspect
from typing import Union, Dict, Any

from yfiles_jupyter_graphs import GraphWidget
from rdflib import Graph, URIRef

DEFAULT_DATA = "http://www.w3.org/People/Berners-Lee/card"
POSSIBLE_NODE_BINDINGS = {'coordinate', 'color', 'size', 'type', 'styles', 'scale_factor', 'position',
                          'layout', 'property', 'label'}
POSSIBLE_EDGE_BINDINGS = {'color', 'thickness_factor', 'property', 'label'}


def extract_label(term, edge):
    """
        Extracts labels from the URI Links
    """
    if isinstance(term, URIRef) or edge:
        return term.split('/')[-1].split('#')[-1]
    else:
        return str(term)


class SparqlGraphWidget:
    def __init__(self, data=DEFAULT_DATA, login=None, pwd=None):

        graph = Graph().parse(data, format="turtle")
        self.endpoint = data
        if login and pwd:
            self.login = login
            self.pwd = pwd

        self.graph = graph
        self._subject_configurations = {}
        self._object_configurations = {}
        self._edge_configurations = {}
        self._parent_configurations = set()
        self.widget = GraphWidget()

    def set_endpoint(self, endpoint):

        self.endpoint = endpoint

    def get_endpoint(self):

        return self.endpoint

    def set_credentials(self, login, pwd):

        self.login = login
        self.pwd = pwd

    def get_credentials(self):

        return self.login, self.pwd

    def show_query(self, query):

        res = self.graph.query(query)
        try:
            widget = self._create_graph(res)
            self.widget = widget
        except TypeError:
            raise Exception('This widget can only visualize Select, Describe and Construct queries')

        widget.show()

    def update_graph(self, updated_query):

        self.graph.update(updated_query)

    def _create_graph(self, triples):

        existing_nodes = []  # store created node labels in here
        nodes = []
        edges = []
        widget = GraphWidget()
        for row in triples:
            s = row[0]
            p = row[1]
            o = row[2]

            s_label = str(s)
            s_extracted_label = extract_label(s, False)

            o_label = str(o)
            o_extracted_label = extract_label(o, False)

            p_label = str(p)
            p_extracted_label = extract_label(p, True)

            if s_label not in existing_nodes:
                existing_nodes.append(s_label)
                nodes.append({'id': s_label, 'properties': {'label': s_extracted_label, 'full_label': s_label}})
            if o_label not in existing_nodes:
                existing_nodes.append(o_label)
                nodes.append({'id': o_label, 'properties': {'label': o_extracted_label, 'full_label': o_label}})

            edges.append({'start': s_label, 'end': o_label,
                          'properties': {'label': p_extracted_label, 'full_label': p_label}})

        widget.nodes = nodes
        widget.edges = edges
        widget.directed = True
        self.__apply_edge_mappings(widget)
        self.__apply_node_mappings(widget)
        return widget

    # noinspection PyShadowingBuiltins
    def add_predicate_configuration(self, type: Union[str, list[str]], **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given relationship `type`(s).

        Args:
            type (Union[str, list[str]]): The relationship type(s) for which this configuration should be used. Supports `*` to address all labels.
            **kwargs (Dict): Visualization configuration for the given node label. The following arguments are supported:

                - `text` (Union[str, Callable]): The text to be displayed on the node.  By default, the relationship's type is used.
                - `color` (Union[str, Callable]): The relationship's color.
                - `thickness_factor` (Union[str, Callable]): The relationship's stroke thickness factor. By default, 1.
                - `property` (Union[Dict, Callable]): Allows to specify additional properties on the relationship, which may be bound by other bindings.

        Returns:
            None
        """
        # this wrapper uses "text" as text binding in the graph
        # in contrast to "label" which is used in yfiles-jupyter-graphs
        text_binding = kwargs.pop("text", None)
        config = kwargs
        if text_binding is not None:
            config["label"] = text_binding

        cloned_config = {key: value for key, value in config.items()}
        if isinstance(type, list):
            for t in type:
                self._edge_configurations[t] = cloned_config
        else:
            self._edge_configurations[type] = cloned_config

    def add_subject_configuration(self, labels: Union[str, list[str]], **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given node `label`(s).

        Args:
            labels (Union[str, list[str]]): The node label(s) for which this configuration should be used. Supports `*` to address all labels.
            **kwargs (Dict[str, Any]): Visualization configuration for the given node label. The following arguments are supported:

                - `text` (Union[str, Callable]): The text to be displayed on the node. By default, the node's label is used.
                - `color` (Union[str, Callable]): A convenience color binding for the node (see also styles kwarg).
                - `size` (Union[str, Callable]): The size of the node.
                - `styles` (Union[Dict, Callable]): A dictionary that may contain the following attributes color, shape (one of 'ellipse', ' hexagon', 'hexagon2', 'octagon', 'pill', 'rectangle', 'round-rectangle' or 'triangle'), image.
                - `property` (Union[Dict, Callable]): Allows to specify additional properties on the node, which may be bound by other bindings.
                - `type` (Union[Dict, Callable]): Defines a specific "type" for the node which affects the automatic positioning of nodes (same "type"s are preferred to be placed next to each other).
                - `parent_configuration` (Union[str, Callable]): Configure grouping for this node label.

        Returns:
            None
        """
        # this wrapper uses "text" as text binding in the graph
        # in contrast to "label" which is used in yfiles-jupyter-graphs
        text_binding = kwargs.pop("text", None)
        config = kwargs
        if text_binding is not None:
            config["label"] = text_binding

        cloned_config = {key: value for key, value in config.items()}
        if isinstance(labels, list):
            for label in labels:
                self._subject_configurations[label] = cloned_config
        else:
            self._subject_configurations[labels] = cloned_config

    def add_object_configuration(self, labels: Union[str, list[str]], **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given node `label`(s).

        Args:
            labels (Union[str, list[str]]): The node label(s) for which this configuration should be used. Supports `*` to address all labels.
            **kwargs (Dict[str, Any]): Visualization configuration for the given node label. The following arguments are supported:

                - `text` (Union[str, Callable]): The text to be displayed on the node. By default, the node's label is used.
                - `color` (Union[str, Callable]): A convenience color binding for the node (see also styles kwarg).
                - `size` (Union[str, Callable]): The size of the node.
                - `styles` (Union[Dict, Callable]): A dictionary that may contain the following attributes color, shape (one of 'ellipse', ' hexagon', 'hexagon2', 'octagon', 'pill', 'rectangle', 'round-rectangle' or 'triangle'), image.
                - `property` (Union[Dict, Callable]): Allows to specify additional properties on the node, which may be bound by other bindings.
                - `type` (Union[Dict, Callable]): Defines a specific "type" for the node which affects the automatic positioning of nodes (same "type"s are preferred to be placed next to each other).
                - `parent_configuration` (Union[str, Callable]): Configure grouping for this node label.

        Returns:
            None
        """
        # this wrapper uses "text" as text binding in the graph
        # in contrast to "label" which is used in yfiles-jupyter-graphs
        text_binding = kwargs.pop("text", None)
        config = kwargs
        if text_binding is not None:
            config["label"] = text_binding

        cloned_config = {key: value for key, value in config.items()}
        if isinstance(labels, list):
            for label in labels:
                self._object_configurations[label] = cloned_config
        else:
            self._object_configurations[labels] = cloned_config

    def __apply_node_mappings(self, widget):
        affected_subjects = {}
        affected_objects = {}
        for predicate in self._object_configurations:
            query = f"""
                            SELECT ?object
                            WHERE {{
                                    ?subject :{predicate} ?object .
                            }}
                        """
            result = self.graph.query(query)
            for row in result:
                affected_objects[extract_label(row[0], False)] = predicate
        for predicate in self._subject_configurations:
            query = f"""
                            SELECT ?subject
                            WHERE {{
                                    ?subject :{predicate} ?object .
                            }}
                        """
            result = self.graph.query(query)
            for row in result:
                affected_subjects[extract_label(row[0], False)] = predicate

        for key in POSSIBLE_NODE_BINDINGS:
            default_mapping = getattr(widget, f"default_node_{key}_mapping")
            setattr(widget, f"_node_{key}_mapping",
                    self.__configuration_mapper_factory('', key, affected_subjects,
                                                        affected_objects, default_mapping))

    def __apply_edge_mappings(self, widget):
        edge_predicates = []
        for predicate in self._edge_configurations:
            edge_predicates.append(predicate)

        for key in POSSIBLE_EDGE_BINDINGS:
            default_mapping = getattr(widget, f"default_edge_{key}_mapping")
            setattr(widget, f"_edge_{key}_mapping",
                    self.__configuration_mapper_factory(edge_predicates, key, {}, {},
                                                        default_mapping))

    def __configuration_mapper_factory(self, edge_predicate: [str], binding_key: str, affected_subjects: Dict[str, str],
                                       affected_objects: Dict[str, str], default_mapping):
        def mapping(index, item: Dict):
            configurations = {}
            predicate = ''
            label = item["properties"]["label"]
            if label in affected_objects:
                configurations = self._object_configurations
                predicate = affected_objects[label]
            elif label in affected_subjects:
                configurations = self._subject_configurations
                predicate = affected_subjects[label]
            elif label in edge_predicate:
                configurations = self._edge_configurations
                predicate = label

            if predicate in configurations and binding_key in configurations[predicate]:  # or '*' in configurations
                if binding_key == 'parent_configuration':
                    result = None           # TODO parent, heat config
                # result = 'GroupNode' + group_label
                # mapping
                elif callable(configurations.get(predicate)[binding_key]):
                    result = configurations.get(predicate)[binding_key](item)
                # property name
                elif (not isinstance(configurations.get(predicate)[binding_key], dict) and
                      configurations.get(predicate)[binding_key] in item["properties"]):
                    result = item["properties"][configurations.get(predicate).get(binding_key)]
                # constant value
                else:
                    result = configurations.get(predicate).get(binding_key)

                return result

            # call default mapping
            # some default mappings do not support "index" as first parameter
            parameters = inspect.signature(default_mapping).parameters
            if len(parameters) > 1 and parameters[list(parameters)[0]].annotation == int:
                return default_mapping(index, item)
            else:
                return default_mapping(item)

        return mapping
