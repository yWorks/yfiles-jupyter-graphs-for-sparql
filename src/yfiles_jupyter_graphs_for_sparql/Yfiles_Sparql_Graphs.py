import inspect
import re
from typing import Union, Dict, Any, Optional

from yfiles_jupyter_graphs import GraphWidget
from rdflib import Graph, URIRef, Literal
from SPARQLWrapper import SPARQLWrapper, POST, DIGEST, RDFXML, JSON

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


def safe_delete_configuration(key: str, configurations: Dict[str, Any]) -> None:
    if key == "*":
        configurations.clear()
    if key in configurations:
        del configurations[key]


class SparqlGraphWidget:

    def __init__(self, limit=50, endpoint=None, pwd=None, login=None, data=None):
        self.graph = None
        self.data = data
        self.limit = limit
        self._subject_configurations = {}
        self._object_configurations = {}
        self._edge_configurations = {}
        self._parent_configurations = set()
        self.widget = GraphWidget()
        self.endpoint = endpoint
        self.login = login
        self.pwd = pwd

        if data:
            self.graph = Graph().parse(data)

    def _fetch_data_from_sparql(self, query):

        sparql = SPARQLWrapper(self.endpoint)
        sparql.setQuery(query)

        if self.login and self.pwd:
            sparql.setHTTPAuth(DIGEST)
            sparql.setCredentials(self.login, self.pwd)
            sparql.setMethod(POST)

        is_select_query = query.strip().upper().startswith("SELECT")

        if is_select_query:
            sparql.setReturnFormat(JSON)
        else:
            sparql.setReturnFormat(RDFXML)

        try:
            results = sparql.query()
            results = results.convert()

            if is_select_query:
                self.graph = None
                return results

            else:
                if isinstance(results, Graph):
                    self.graph = results
                else:
                    raise Exception("Unexpected data type from SPARQL query")

        except Exception as e:
            raise Exception(f"Error executing SPARQL query: {e}")

    def set_data(self, data):
        self.graph = Graph().parse(data)
        self.data = data

    def get_data(self):
        return self.data

    def set_limit(self, limit):
        self.limit = limit

    def get_limit(self):
        return self.limit

    def _limit_query(self, query):
        limit_pattern = re.compile(r"(?i)\bLIMIT\s+(\d+)", re.IGNORECASE)
        match = limit_pattern.search(query)

        if match:
            user_limit = int(match.group(1))
            if user_limit > self.limit:
                query = limit_pattern.sub(f"LIMIT {self.limit}", query)
        else:
            query = query.strip() + f"\nLIMIT {self.limit}"

        return query

    def show_query(self, query):

        query = self._limit_query(query)
        if self.data is None:
            self._fetch_data_from_sparql(query)
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

        def find_element_by_label(array, label):
            i = 0
            for element in array:
                if element['id'] == label:
                    return i
                i += 1
            return None

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
            literal = isinstance(o, Literal)

            p_label = str(p)
            p_extracted_label = extract_label(p, True)

            if s_label not in existing_nodes:
                existing_nodes.append(s_label)
                if literal:
                    node = {'id': s_label, 'properties': {'label': s_extracted_label, 'full_label': s_label}}
                    node['properties'][p_extracted_label] = o_extracted_label
                    nodes.append(node)
                else:
                    nodes.append({'id': s_label, 'properties': {'label': s_extracted_label, 'full_label': s_label}})
                existing_nodes.append(s_label)
            elif literal:
                index = find_element_by_label(nodes, s_label)
                nodes[index]['properties'][p_extracted_label] = o_extracted_label

            if not literal:

                if o_label not in existing_nodes:
                    existing_nodes.append(o_label)
                    nodes.append({'id': o_label, 'properties': {'label': o_extracted_label, 'full_label': o_label}})
                    existing_nodes.append(o_label)

                edges.append({'id': p_extracted_label, 'start': s_label, 'end': o_label,
                              'properties': {'label': p_extracted_label, 'full_label': p_label}})

        widget.nodes = nodes
        widget.edges = edges
        widget.directed = True
        self.__create_group_nodes(widget)
        self.__apply_edge_mappings(widget)
        self.__apply_node_mappings(widget)
        self.__apply_parent_mapping(widget)
        return widget

    def add_predicate_configuration(self, predicate: Union[str, list[str]], **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given relationship `type`(s).

        Args:
            predicate (Union[str, list[str]]): The predicate type(s) for which this configuration should be used. Supports `*` to address all labels.
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
        if isinstance(predicate, list):
            for t in predicate:
                self._edge_configurations[t] = cloned_config
        else:
            self._edge_configurations[predicate] = cloned_config

    def add_subject_configuration(self, predicate: Union[str, list[str]], **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given node `label`(s).

        Args:
            predicate (Union[str, list[str]]): The node predicate type(s) for which this configuration should be used. Supports `*` to address all labels.
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
        if isinstance(predicate, list):
            for label in predicate:
                self._subject_configurations[label] = cloned_config
        else:
            self._subject_configurations[predicate] = cloned_config

    def add_object_configuration(self, predicate: Union[str, list[str]], **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given node `label`(s).

        Args:
            predicate (Union[str, list[str]]): The node predicate type(s) for which this configuration should be used. Supports `*` to address all labels.
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
        if isinstance(predicate, list):
            for label in predicate:
                self._object_configurations[label] = cloned_config
        else:
            self._object_configurations[predicate] = cloned_config

    def __apply_node_mappings(self, widget):
        affected_subjects = {}
        affected_objects = {}
        for predicate in self._object_configurations:
            query = f"""
                            SELECT ?object
                            WHERE {{
                                    ?subject :{predicate} ?object .
                            }}
                            LIMIT {self.limit}
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
                            LIMIT {self.limit}
                        """
            result = self.graph.query(query)
            for row in result:
                affected_subjects[extract_label(row[0], False)] = predicate

        for key in POSSIBLE_NODE_BINDINGS:
            default_mapping = getattr(widget, f"default_node_{key}_mapping")
            setattr(widget, f"_node_{key}_mapping",
                    self.__configuration_mapper_factory('', key, affected_subjects,
                                                        affected_objects, default_mapping))

        setattr(widget, f"_node_parent_mapping",
                self.__configuration_mapper_factory('', 'parent_configuration', affected_subjects, affected_objects,
                                                    lambda node: None))

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
                    binding = configurations[predicate].get(binding_key)
                    if binding and callable(binding):
                        binding = binding(item)
                    # parent_configuration binding may either resolve to a dict or a string
                    if isinstance(binding, dict):
                        group_label = binding.get('text', '')
                    else:
                        group_label = binding
                    result = 'GroupNode' + group_label
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

    def del_object_configuration(self, predicate: Union[str, list[str]]) -> None:
        """
        Deletes the configuration object for the given node object predicate `type`(s).

        Args:
            predicate (Union[str, list[str]]): The node object for the predicate types(s) for which the configuration should be deleted. Supports `*` to address all labels.

        Returns:
            None
        """
        if isinstance(predicate, list):
            for label in predicate:
                safe_delete_configuration(label, self._object_configurations)
        else:
            safe_delete_configuration(predicate, self._object_configurations)

    def del_subject_configuration(self, predicate: Union[str, list[str]]) -> None:
        """
        Deletes the configuration object for the given node subject predicate `type`(s).

        Args:
            predicate (Union[str, list[str]]): The node subject for the predicate types(s) for which the configuration should be deleted. Supports `*` to address all labels.

        Returns:
            None
        """
        if isinstance(predicate, list):
            for label in predicate:
                safe_delete_configuration(label, self._subject_configurations)
        else:
            safe_delete_configuration(predicate, self._subject_configurations)

    def del_predicate_configuration(self, predicate: Union[str, list[str]]) -> None:
        """
        Deletes the configuration object for the given relationship `type`(s).

        Args:
            predicate (Union[str, list[str]]): The relationship type(s) for which the configuration should be deleted. Supports `*` to address all types.

        Returns:
            None
        """
        if isinstance(predicate, list):
            for label in predicate:
                safe_delete_configuration(label, self._edge_configurations)
        else:
            safe_delete_configuration(predicate, self._edge_configurations)

    # noinspection PyUnboundLocalVariable
    def show_schema(self):
        g = self.graph

        if g is None:
            raise Exception("No data was given to infer schema")

        classes = g.query(f"""
            SELECT DISTINCT ?class
            WHERE {{
                ?class rdf:type rdfs:Class .
                }}
            LIMIT {self.limit // 2}
        """)
        properties = g.query(f"""
            SELECT DISTINCT ?property ?domain ?range
            WHERE {{
                ?property rdf:type rdf:Property .        
                
                OPTIONAL {{ ?property rdfs:domain ?domain . }}
                
                OPTIONAL {{ ?property rdfs:range ?range . }}
                
                FILTER (BOUND(?domain) || BOUND(?range))
                }}
            LIMIT {self.limit // 2}
        """)
        connections = g.query(f"""
        SELECT DISTINCT ?source_class ?property ?target_class
        WHERE {{
            {{
                ?s ?property ?o .
                ?s rdf:type ?source_class .
                ?o rdf:type ?target_class .
            }}
            UNION
            {{
                ?property rdf:type rdf:Property .
        
            OPTIONAL {{ ?property rdfs:domain ?source_class . }}
            OPTIONAL {{ ?property rdfs:range ?target_class . }}
            
            FILTER (BOUND(?source_class) && BOUND(?target_class))
            }}
        }}
        """)

        def add_node(label):
            label = extract_label(label, False)
            if label and not any(node['id'] == label for node in nodes):
                nodes.append({'id': label, 'properties': {'label': label}})

        nodes = []
        edges = []
        for cls in classes:
            add_node(cls[0])

        for prop, domain, range_ in properties:
            if domain or range_:
                if domain:
                    add_node(domain)
                    d_label = extract_label(domain, False)
                if range_:
                    add_node(range_)
                    r_label = extract_label(range_, False)

                p_label = extract_label(prop, False)

                if domain and range_:
                    pass  # handled by connections
                elif domain:
                    edges.append({
                        'start': d_label,
                        'end': p_label,
                        'properties': {'label': 'domain'}
                    })
                    add_node(prop)
                elif range_:
                    edges.append({
                        'start': p_label,
                        'end': r_label,
                        'properties': {'label': 'range'}
                    })
                    add_node(prop)

        for source, prop, target in connections:
            s_label = extract_label(source, False)
            t_label = extract_label(target, False)
            add_node(source)
            add_node(target)
            edges.append({
                'start': s_label,
                'end': t_label,
                'properties': {'label': extract_label(prop, True), 'full label': prop}
            })

        if nodes == [] or edges == []:
            raise Exception('no schema data found in the given graph')
        widget = GraphWidget()
        widget.directed = True
        widget.nodes = nodes
        widget.edges = edges
        widget.hierarchic_layout()
        widget.show()

    def add_parent_configuration(self, predicate: Union[str, list[str]], reverse: Optional[bool] = False) -> None:
        """
        Configure specific relationship types to visualize as nested hierarchies. This removes these relationships from
        the graph and instead groups the related nodes (source and target) as parent-child.

        Args:
            predicate (Union[str, list[str]]): The relationship type(s) that should be visualized as node grouping hierarchy instead of the actual relationship.
            reverse (bool): Which node should be considered as parent. By default, the target node is considered as parent which can be reverted with this argument.

        Returns:
            None
        """
        if isinstance(predicate, list):
            for t in predicate:
                self._parent_configurations.add((t, reverse))
        else:
            self._parent_configurations.add((predicate, reverse))

    # noinspection PyShadowingBuiltins
    def del_parent_relationship_configuration(self, type: Union[str, list[str]]) -> None:
        """
        Deletes the relationship configuration for the given `type`(s).

        Args:
            type (Union[str, list[str]]): The relationship type(s) for which the configuration should be deleted.

        Returns:
            None
        """
        if isinstance(type, list):
            self._parent_configurations = {
                rel_type for rel_type in self._parent_configurations if rel_type[0] not in type
            }
        else:
            self._parent_configurations = {
                rel_type for rel_type in self._parent_configurations if rel_type[0] != type
            }

    def __apply_parent_mapping(self, widget: GraphWidget) -> None:
        node_to_parent = {}
        edge_ids_to_remove = set()
        for edge in widget.edges[:]:
            rel_type = edge["properties"]["label"]
            for (parent_type, is_reversed) in self._parent_configurations:
                if rel_type == parent_type:
                    start = edge['start']  # child node id
                    end = edge['end']  # parent node id
                    if is_reversed:
                        node_to_parent[end] = start
                    else:
                        node_to_parent[start] = end
                    edge_ids_to_remove.add(edge['id'])
                    break

        # use list comprehension to filter out the edges to automatically trigger model sync with the frontend
        widget.edges = [edge for edge in widget.edges if edge['id'] not in edge_ids_to_remove]
        current_parent_mapping = widget.get_node_parent_mapping()
        setattr(widget, "_node_parent_mapping",
                lambda index, node: node_to_parent.get(node['id'], current_parent_mapping(index, node)))

    def __create_group_nodes(self, widget: GraphWidget) -> None:
        group_node_properties = set()
        group_node_values = set()
        affected_objects = {}
        affected_subjects = {}
        key = 'parent_configuration'
        for predicate in self._object_configurations:
            if key in self._object_configurations.get(predicate):
                query = f"""
                        SELECT ?object
                        WHERE {{
                            ?subject :{predicate} ?object .
                        }}
                        LIMIT {self.limit}
                """
                result = self.graph.query(query)
                for row in result:
                    affected_objects[extract_label(row[0], False)] = predicate
        for predicate in self._subject_configurations:
            if key in self._subject_configurations.get(predicate):
                query = f"""
                                            SELECT ?subject
                                            WHERE {{
                                                    ?subject :{predicate} ?object .
                                            }}
                                            LIMIT {self.limit}
                                        """
                result = self.graph.query(query)
                for row in result:
                    affected_subjects[extract_label(row[0], False)] = predicate

        for node in widget.nodes:
            label = node['properties']['label']

            group_node = None
            if label in affected_subjects:
                group_node = self._subject_configurations.get(affected_subjects.get(label)).get(key)
            if label in affected_objects:
                group_node = self._object_configurations.get(affected_objects.get(label)).get(key)

            if group_node:
                if callable(group_node):
                    group_node = group_node(node)

                if isinstance(group_node, str):
                    # string or property value
                    if group_node in node["properties"]:
                        group_node_properties.add(str(node["properties"][group_node]))
                    else:
                        group_node_values.add(group_node)
                else:
                    # dictionary with values
                    text = group_node.get('text', '')
                    group_node_values.add(text)
                    configuration = {k: v for k, v in group_node.items() if k != 'text'}
                    if label in affected_objects:
                        self.add_object_configuration(text, **configuration)
                    if label in affected_subjects:
                        self.add_subject_configuration(text, **configuration)

        for group_label in group_node_properties.union(group_node_values):
            node = {'id': 'GroupNode' + group_label, 'properties': {'label': group_label}}
            widget.nodes = [*widget.nodes, node]
