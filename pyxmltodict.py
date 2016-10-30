from six import string_types, iteritems

import os
from collections import OrderedDict

try:
	import libxml2
except ImportError:
	libxml2 = None

try:
	from lxml import etree
except ImportError:
	etree = None

def parse_path(path, omit_namespaces=False):
	if etree:
		return _parse_path_lxml(path, omit_namespaces)
	elif libxml2:
		return _parse_path_libxml2(path, omit_namespaces)

def parse(data, omit_namespaces=False):
	if etree:
		return _parse_lxml(data, omit_namespaces)
	elif libxml2:
		return _parse_libxml2(data, omit_namespaces)

def _parse_path_lxml(path, omit_namespaces=False):
	"""
	Parses the contents of an XML file into a dictionary

	:param string path: Path to XML file
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if etree is None:
		print("Unable to load XML: lxml not installed")
		return False

	if os.path.exists(path):
		with open(path) as fd:
			return _parse_lxml(fd.read(), omit_namespaces)
	return False

def _parse_lxml(data, omit_namespaces=False):
	"""
	Parses a string representation of an XML file into a dictionary

	:param string data: Contents of XML file
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if etree is None:
		print("Unable to load XML: lxml not installed")
		return False

	if data:
		root 		= etree.fromstring(data)
		tmp_results 	= _iter_nodes_lxml(root, OrderedDict(), omit_namespaces)

		root_name 	= _convert_name(root.tag, root.prefix, root.nsmap, omit_namespaces)
		root_results 	= _find_node_data_lxml(root, omit_namespaces)
		tmp_results.update(root_results)

		results = OrderedDict()
		results[root_name] = tmp_results
		return results
	return False

def _iter_nodes_lxml(root, results, omit_namespaces=False):
	"""
	Internal method for iterating through XML nodes

	:param XmlElement root: Node to iterate through
	:param dict results: Parent dictionary holding results
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: Dictionary with appended data
	:rtype: dict
	"""
	for node in root.getchildren():
		child_results	= _find_node_data_lxml(node, omit_namespaces)
		node_results	= _iter_nodes_lxml(node, child_results, omit_namespaces)
		if not isinstance(node.tag, string_types):
			continue
		name = _convert_name(node.tag, node.prefix, node.nsmap, omit_namespaces)
		_add_result_lxml(name, node_results, results)
	return results

def _find_node_data_lxml(node, omit_namespaces=False):
	"""
	Internal method for retriving data from an XML node

	:param XmlElement node:
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: Dictionary holding data from the node
	:rtype: dict
	"""
	data = OrderedDict()
	if node is not None:
		for k, v in iteritems(node.attrib):
			if not isinstance(k, string_types):
				continue
			name 		= _convert_name(k, None, node.nsmap, omit_namespaces)
			data[name] 	= v

		if node.text and node.text.strip():
			if node.attrib:
				data["_value"] = node.text
			else:
				data = node.text
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

def _parse_path_libxml2(path, omit_namespaces=False):
	"""
	Parses the contents of an XML file into a dictionary

	:param string path: Path to XML file
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if libxml2 is None:
		print("Unable to load XML: libxml2 not installed")
		return False

	if os.path.exists(path):
		data = libxml2.parseFile(path)
		return _parse_libxml2(data, omit_namespaces)
	return False

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

def _iter_nodes_libxml2(node, results, omit_namespaces=False):
	"""
	Internal method for iterating through XML nodes

	:param XmlElement node: Node to iterate through
	:param dict results: Parent dictionary holding results
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: Dictionary with appended data
	:rtype: dict
	"""
	while node is not None:
		if node.type == "element":
			child_results	= _find_node_data_libxml2(node, omit_namespaces)
			node_results	= _iter_nodes_libxml2(node.children, child_results, omit_namespaces)

			name = node.name
			if node.ns() and node.ns().name and not omit_namespaces:
				name = "{ns}:{name}".format(ns=node.ns().name, name=node.name)

			if name in results:
				try:
					results[name].append(node_results)
				except AttributeError:
					results[name] = [results[name], node_results]
			else:
				try:
					results[name] = node_results
				except Exception as e:
					raise Exception(name+" "+" "+str(type(results))+": "+str(e))
		node = node.next
	return results

def _find_node_data_libxml2(node, omit_namespaces=False):
	"""
	Internal method for retriving data from an XML node

	:param XmlElement node:
	:param bool omit_namespaces: Whether or not to include namespace data in the keys
	:return: Dictionary holding data from the node
	:rtype: dict
	"""
	data = {}
	if node:
		if node.properties:
			for attrib in node.properties:
				if attrib.type == "attribute":
					name = attrib.name
					if attrib.ns() and not omit_namespaces:
						name = "{ns}:{name}".format(ns=attrib.ns().name, name=attrib.name)
					data[name] = attrib.content
		if node.content:
			if str(node.children) == node.content:
				if node.properties:
					data["_value"] = node.content
				else:
					data = node.content
	return data
