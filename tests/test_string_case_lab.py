import unittest
from shared.string_case_lab import StringCaseManager

class TestStringCaseLab(unittest.TestCase):
    def setUp(self):
        self.manager = StringCaseManager()

    def test_to_camel(self):
        self.assertEqual(self.manager.to_camel("hello_world"), "helloWorld")
        self.assertEqual(self.manager.to_camel("hello-world"), "helloWorld")
        self.assertEqual(self.manager.to_camel("hello world"), "helloWorld")
        self.assertEqual(self.manager.to_camel("HelloWorld"), "helloWorld")
        self.assertEqual(self.manager.to_camel("XMLHttp"), "xmlHttp")
        self.assertEqual(self.manager.to_camel(""), "")

    def test_to_snake(self):
        self.assertEqual(self.manager.to_snake("helloWorld"), "hello_world")
        self.assertEqual(self.manager.to_snake("hello-world"), "hello_world")
        self.assertEqual(self.manager.to_snake("hello world"), "hello_world")
        self.assertEqual(self.manager.to_snake("HelloWorld"), "hello_world")
        self.assertEqual(self.manager.to_snake("XMLHttp"), "xml_http")

    def test_to_kebab(self):
        self.assertEqual(self.manager.to_kebab("helloWorld"), "hello-world")
        self.assertEqual(self.manager.to_kebab("hello_world"), "hello-world")
        self.assertEqual(self.manager.to_kebab("hello world"), "hello-world")
        self.assertEqual(self.manager.to_kebab("HelloWorld"), "hello-world")
        self.assertEqual(self.manager.to_kebab("XMLHttp"), "xml-http")

    def test_to_pascal(self):
        self.assertEqual(self.manager.to_pascal("hello_world"), "HelloWorld")
        self.assertEqual(self.manager.to_pascal("hello-world"), "HelloWorld")
        self.assertEqual(self.manager.to_pascal("hello world"), "HelloWorld")
        self.assertEqual(self.manager.to_pascal("helloWorld"), "HelloWorld")
        self.assertEqual(self.manager.to_pascal("xml_http"), "XmlHttp")

    def test_to_constant(self):
        self.assertEqual(self.manager.to_constant("helloWorld"), "HELLO_WORLD")
        self.assertEqual(self.manager.to_constant("hello-world"), "HELLO_WORLD")
        self.assertEqual(self.manager.to_constant("hello world"), "HELLO_WORLD")
        self.assertEqual(self.manager.to_constant("HelloWorld"), "HELLO_WORLD")
        self.assertEqual(self.manager.to_constant("XMLHttp"), "XML_HTTP")

    def test_to_dot(self):
        self.assertEqual(self.manager.to_dot("helloWorld"), "hello.world")
        self.assertEqual(self.manager.to_dot("hello_world"), "hello.world")
        self.assertEqual(self.manager.to_dot("hello-world"), "hello.world")
        self.assertEqual(self.manager.to_dot("hello world"), "hello.world")
        self.assertEqual(self.manager.to_dot("HelloWorld"), "hello.world")
        self.assertEqual(self.manager.to_dot("XMLHttp"), "xml.http")

    def test_to_path(self):
        self.assertEqual(self.manager.to_path("helloWorld"), "hello/world")
        self.assertEqual(self.manager.to_path("hello_world"), "hello/world")
        self.assertEqual(self.manager.to_path("hello-world"), "hello/world")
        self.assertEqual(self.manager.to_path("hello world"), "hello/world")
        self.assertEqual(self.manager.to_path("HelloWorld"), "hello/world")
        self.assertEqual(self.manager.to_path("XMLHttp"), "xml/http")

if __name__ == "__main__":
    unittest.main()
