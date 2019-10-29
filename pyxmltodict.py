from __future__ import unicode_literals

import os
from collections import OrderedDict

from six import string_types, iteritems

try:
	import libxml2
except ImportError:
	libxml2 = None

try:
	from lxml import etree as ET
except ImportError:
	ET = None

def parse_path(path, dict_constructor=OrderedDict, omit_namespaces=False):
	if not os.path.exists(path):
		return False

	if ET:
		return _parse_lxml_fork(path, dict_constructor, omit_namespaces)
	elif libxml2:
		data = libxml2.parseFile(path)
		return _parse_libxml2(data, dict_constructor, omit_namespaces)

def parse(data, dict_constructor=OrderedDict, omit_namespaces=False):
	if not data:
		return False

	if ET:
		tree = ET.fromstring(data)
		return _parse_lxml(tree, dict_constructor, omit_namespaces)
	elif libxml2:
		return _parse_libxml2(data, dict_constructor, omit_namespaces)

def _parse_path_lxml(path, omit_namespaces=False):
	"""
	Parses the contents of an XML file into a dictionary

	:param string path: Path to XML file
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if ET is None:
		print("Unable to load XML: lxml not installed")
		return False

	if os.path.exists(path):
		with open(path) as fd:
			return _parse_lxml(fd.read(), omit_namespaces)
	return False

def _parse_lxml(root, dict_constructor, omit_namespaces=False):
	"""
	Parses a string representation of an XML file into a dictionary

	:param string data: Contents of XML file
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if ET is None:
		print("Unable to load XML: lxml not installed")
		return False

	tmp_results = _iter_elements_lxml(root, dict_constructor(), dict_constructor, omit_namespaces)

	name = _convert_name(root.tag, root.prefix, root.nsmap, omit_namespaces)
	root_results = _get_element_data_lxml(root, dict_constructor, omit_namespaces)
	if root_results:
		tmp_results.update(root_results)

	results = dict_constructor()
	results[name] = tmp_results
	return results

def _iter_elements_lxml(root, results, dict_constructor, omit_namespaces=False):
	"""
	Internal method for iterating through XML nodes

	:param XmlElement root: Node to iterate through
	:param dict results: Parent dictionary holding results
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: Dictionary with appended data
	:rtype: dict
	"""
	for element in root.getchildren():
		element_data	= _get_element_data_lxml(element, dict_constructor, omit_namespaces)
		element_results	= _iter_elements_lxml(element, element_data, dict_constructor, omit_namespaces)
		if not isinstance(element.tag, string_types):
			continue

		if results is None:
			results = dict_constructor()

		name = _convert_name(element.tag, element.prefix, element.nsmap, omit_namespaces)
		_insert_data(name, element_results, results)
		element.clear()
		del element

	root.clear()
	del root
	return results

def _get_element_data_lxml(element, dict_constructor, omit_namespaces=False):
	"""
	Internal method for retriving data from an XML node

	:param XmlElement node:
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: Dictionary holding data from the node
	:rtype: dict
	"""
	if element is None:
		return

	data = None
	for k, v in iteritems(element.attrib):
		if not isinstance(k, string_types):
			continue
		name = _convert_name(k, None, element.nsmap, omit_namespaces)
		if data is None:
			data = dict_constructor()
		data[name] = v

	if element.text and element.text.strip():
		if element.attrib:
			if data is None:
				data = dict_constructor()
			data["_value"] = element.text
		else:
			data = element.text
	return data

def _add_result_lxml(name, node_result, results):
	if name in results:
		try:
			results[name].append(node_result)
		except AttributeError:
			results[name] = [results[name], node_result]
	else:
		try:
			results[name] = node_result
		except Exception as e:
			print("{name} {type_}: {error}".format(name=name, type_=type(results), error=str(e)))
	return results

def _convert_name(name, ns=None, nsmap=None, omit_namespaces=False):
	if "{" in name:
		if not omit_namespaces:
			ns_href = name[1:name.find("}")]
			if ns is None and nsmap:
				for k, v in iteritems(nsmap):
					if v == ns_href:
						ns = k
						break
			name = name.replace("{{{href}}}".format(href=ns_href), "")
			if ns:
				name = "{ns}:{name}".format(ns=ns, name=name)
		else:
			name = name[name.find("}")+1:]
	return name

def _parse_libxml2(data, dict_constructor, omit_namespaces=False):
	"""
	Parses the contents of an XML file into a dictionary

	:param string path: Path to XML file
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if libxml2 is None:
		Logger.error("Unable to load XML: libxml2 not installed")
		return False

	doc	= libxml2.parseDoc(str(data))
	return _iter_elements_libxml2(doc.getRootElement(), dict_constructor(), dict_constructor, omit_namespaces)

def _parse_libxml2(data, omit_namespaces=False):
	"""
	Parses a string representation of an XML file into a dictionary

	:param string data: Contents of XML file
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if libxml2 is None:
		print("Unable to load XML: libxml2 not installed")
		return False

	if data:
		doc	= libxml2.parseDoc(str(data))
		data 	= _iter_nodes_libxml2(doc.getRootElement(), OrderedDict(), omit_namespaces)
		return data
	return False

def _iter_elements_libxml2(element, results, dict_constructor, omit_namespaces=False):
	"""
	Internal method for iterating through XML nodes

	:param XmlElement node: Node to iterate through
	:param dict results: Parent dictionary holding results
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: Dictionary with appended data
	:rtype: dict
	"""
	while element is not None:
		if element.type == "element":
			element_data	= _get_element_data_libxml2(element, dict_constructor, omit_namespaces)
			element_results	= _iter_elements_libxml2(element.children, element_data, dict_constructor, omit_namespaces)

			name = element.name
			if element.ns() and element.ns().name and not omit_namespaces:
				name = "{ns}:{name}".format(ns=element.ns().name, name=element.name)

			if results is None:
				results = dict_constructor()

			_insert_data(name, element_results, results)
		element = element.next
	return results

def _get_element_data_libxml2(element, dict_constructor, omit_namespaces=False):
	"""
	Internal method for retriving data from an XML node

	:param XmlElement node:
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: Dictionary holding data from the node
	:rtype: dict
	"""
	if element is None:
		return

	data = None
	if element.properties:
		for attrib in element.properties:
			if attrib.type == "attribute":
				if data is None:
					data = dict_constructor()
				name = attrib.name
				if attrib.ns() and not omit_namespaces:
					name = "{ns}:{name}".format(ns=attrib.ns().name, name=attrib.name)
				data[name] = attrib.content
	if element.content:
		if str(element.children) == element.content:
			if element.properties:
				if data is None:
					data = dict_constructor()
				data["_value"] = element.content
			else:
				data = element.content
	return data

def _insert_data(name, data, parent):
	if isinstance(parent, dict):
		if name not in parent:
			parent[name] = data
		else:
			if isinstance(parent[name], list):
				parent[name].append(data)
			else:
				parent[name] = [parent[name], data]
	elif isinstance(parent, list):
		parent.append(data)
	return parent

##################################################

def _parse_lxml_fork(data, dict_constructor, omit_namespaces=False):
	"""
	Parses a string representation of an XML file into a dictionary

	:param ElementTree data: Contents of XML file
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if ET is None:
		Logger.error("Unable to load XML: lxml not installed")
		return False

	root	 			= dict_constructor()
	levels 				= []
	created_indices 	= []
	elem_index 			= 0
	last_parent 		= (None, -1)

	_name = ""
	context = ET.iterparse(data, events=("start", "end"))
	for event, element in context:
		if event == "start":
			# Construct parent first
			if len(levels) > 0:
				(parent_name, parent_data, parent_index) = levels[-1]

				if parent_index not in created_indices:
					created_indices.append(parent_index)
					grandparent, __ = _find_parent(last_parent, levels[:-1], root, dict_constructor)
					if parent_data is None:
						parent_data = dict_constructor()
					_insert_data(parent_name, parent_data, grandparent)

			name = _convert_name(element.tag, element.prefix, element.nsmap, omit_namespaces)
			data = _get_element_data_lxml(element, dict_constructor, omit_namespaces)
			levels.append((name, data, elem_index))
			elem_index += 1

		elif event == "end":
			(name, data, index) = levels.pop()

			# Check to see if the text field was missed before
			element_data = _get_element_data_lxml(element, dict_constructor, omit_namespaces)
			if element_data is not None:
				if isinstance(data, dict):
					if isinstance(element_data, dict):
						data.update(element_data)
					else:
						data["_value"] = element_data
				else:
					data = element_data

			if index not in created_indices:
				parent, last_parent = _find_parent(last_parent, levels, root, dict_constructor)
				if data is not None:
					_insert_data(name, data, parent)
			else:
				created_indices.remove(index)

		element.clear()

	return root

def _find_parent(last_parent, levels, root, dict_constructor):
	if len(levels) > 0 and levels[-1][2] == last_parent[1]:
		return last_parent[0], last_parent

	parent_index = 0
	parent = root
	for name, __, index in levels:
		if isinstance(parent, list):
			parent = parent[-1]

		if name not in parent:
			parent[name] = dict_constructor()
		parent = parent[name]
		parent_index = index

	if isinstance(parent, list):
		parent = parent[-1]
	return parent, (parent, parent_index)