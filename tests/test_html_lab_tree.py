import unittest
from shared.html_lab import HTMLLabManager, HTMLNode

class TestHTMLTreeBuilder(unittest.TestCase):
    def setUp(self):
        self.manager = HTMLLabManager()

    def test_basic_tree(self):
        html = "<div><p>Hello</p></div>"
        root = self.manager.tree(html)

        # Root is a dummy node "root"
        self.assertEqual(root.tag, "root")
        self.assertEqual(len(root.children), 1)

        div = root.children[0]
        self.assertEqual(div.tag, "div")
        self.assertEqual(len(div.children), 1)

        p = div.children[0]
        self.assertEqual(p.tag, "p")
        self.assertEqual(p.text, "Hello")

    def test_attributes(self):
        html = '<a href="https://example.com" class="link">Click</a>'
        root = self.manager.tree(html)
        a = root.children[0]

        self.assertEqual(a.tag, "a")
        self.assertEqual(a.attrs["href"], "https://example.com")
        self.assertEqual(a.attrs["class"], "link")
        self.assertEqual(a.text, "Click")

    def test_nested_structure(self):
        html = """
        <ul>
            <li>Item 1</li>
            <li>Item 2 <b>Bold</b></li>
        </ul>
        """
        root = self.manager.tree(html)
        ul = root.children[0]
        self.assertEqual(ul.tag, "ul")
        self.assertEqual(len(ul.children), 2)

        li1 = ul.children[0]
        self.assertEqual(li1.tag, "li")
        self.assertEqual(li1.text, "Item 1")

        li2 = ul.children[1]
        self.assertEqual(li2.tag, "li")
        # Text "Item 2 " is directly in li2, "Bold" is in <b>
        self.assertIn("Item 2", li2.text)
        self.assertEqual(len(li2.children), 1)
        self.assertEqual(li2.children[0].tag, "b")
        self.assertEqual(li2.children[0].text, "Bold")

    def test_void_elements(self):
        html = "<div><img src='img.png'><br><p>Text</p></div>"
        root = self.manager.tree(html)
        div = root.children[0]

        # div should have 3 children: img, br, p
        self.assertEqual(len(div.children), 3)
        self.assertEqual(div.children[0].tag, "img")
        self.assertEqual(div.children[1].tag, "br")
        self.assertEqual(div.children[2].tag, "p")

    def test_mismatched_tags(self):
        # Missing closing p tag
        html = "<div><p>Hello</div>"
        root = self.manager.tree(html)
        div = root.children[0]

        # p should be child of div
        self.assertEqual(len(div.children), 1)
        p = div.children[0]
        self.assertEqual(p.tag, "p")
        self.assertEqual(p.text, "Hello")

        # Since p was never closed, it implicitly closes when div closes or when parent changes.
        # Our simple parser walks up the stack.
        # When </div> is encountered, current is <p>. It doesn't match </div>.
        # It goes to parent <div>. It matches. So current becomes root.
        # Effectively <p> is considered closed.

if __name__ == '__main__':
    unittest.main()
