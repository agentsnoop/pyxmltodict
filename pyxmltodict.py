try:
	import libxml2
except ImportError:
	libxml2 = None

try:
	import lxml
except ImportError:
	lxml = None
	
def parseXmlFile(xmlFile):
	"""
	Parses the contents of an XML file into a dictionary

	:param string xmlFile: Path to XML file
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if libxml2:
		if os.path.exists(xmlFile):
			xml 	= libxml2.parseFile(xmlFile)
			doc		= libxml2.parseDoc(str(xml))
			root 	= doc.getRootElement()

			emptyDict 	= OrderedDict()
			parsedDict 	= _iterNodes(root, emptyDict)
			return parsedDict
	else:
		print("Unable to load XML: libxml2 not installed")
	return False
	# if lxml:
	# 	if os.path.exists(xmlFile):
	# 		doc 	= lxml.etree.parse(xmlFile)
	# 		root	= doc.getroot()
	#
	# 		emptyDict 	= OrderedDict()
	# 		parsedDict 	= _iterNodes(root, emptyDict)
	# 		return parsedDict
	# else:
	# 	print("Unable to load XML: lxml not installed")
	# return False

def parseXmlString(xmlString):
	"""
	Parses a string representation of an XML file into a dictionary

	:param string xmlString: Contents of XML file
	:return: XML file as OrderedDict
	:rtype: OrderedDict
	"""
	if xmlString:
		doc		= libxml2.parseDoc(str(xmlString))
		root 	= doc.getRootElement()

		emptyDict 	= OrderedDict()
		parsedDict 	= _iterNodes(root, emptyDict)
		return parsedDict
	else:
		return False

def _iterNodes(node, parentDict):
	"""
	Internal method for iterating through XML nodes

	:param XmlElement node: Node to iterate through
	:param dictionary parentDict: Parent dictionary holding results
	:return: Dictionary with appended data
	:rtype: dict
	"""
	while node is not None:
		if node.type == "element":
			childDict 	= _findNodeData(node)
			nodeDict 	= _iterNodes(node.children, childDict)
			if node.name in parentDict.keys():
				try:
					parentDict[node.name].append(nodeDict)
				except Exception:
					newList = [parentDict[node.name], nodeDict]
					parentDict[node.name] = newList
			else:
				parentDict[node.name] = nodeDict
		node = node.next
	return parentDict

def _findNodeData(node):
	"""
	Internal method for retriving data from an XML node

	:param XmlElement node:
	:return: Dictionary holding data from the node
	:rtype: dict
	"""
	nodeDict = {}
	if node and node.properties:
		for attrib in node.properties:
			if attrib.type == "attribute":
				nodeDict[attrib.name] = attrib.content
	return nodeDict