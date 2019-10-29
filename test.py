import pyxmltodict

data = pyxmltodict.parse_path("test.xml")
print(data.keys())