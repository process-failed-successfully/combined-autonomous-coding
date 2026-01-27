import unittest
from shared.schema_parser import SchemaParser

class TestSchemaParser(unittest.TestCase):
    def setUp(self):
        self.parser = SchemaParser()

    def test_parse_simple_table(self):
        schema = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        );
        """
        result = self.parser.parse(schema)
        self.assertEqual(len(result['tables']), 1)
        table = result['tables'][0]
        self.assertEqual(table['name'], 'users')
        self.assertEqual(len(table['columns']), 3)
        self.assertEqual(table['columns'][0]['name'], 'id')
        self.assertEqual(table['columns'][0]['type'], 'INTEGER')

    def test_parse_with_foreign_key_inline(self):
        schema = """
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title TEXT
        );
        """
        result = self.parser.parse(schema)
        table = result['tables'][0]
        self.assertEqual(len(table['fks']), 1)
        fk = table['fks'][0]
        self.assertEqual(fk['from_col'], 'user_id')
        self.assertEqual(fk['to_table'], 'users')
        self.assertEqual(fk['to_col'], 'id')

    def test_parse_with_foreign_key_constraint(self):
        schema = """
        CREATE TABLE comments (
            id INTEGER,
            post_id INTEGER,
            body TEXT,
            FOREIGN KEY (post_id) REFERENCES posts(id)
        );
        """
        result = self.parser.parse(schema)
        table = result['tables'][0]
        self.assertEqual(len(table['fks']), 1)
        fk = table['fks'][0]
        self.assertEqual(fk['from_col'], 'post_id')
        self.assertEqual(fk['to_table'], 'posts')
        self.assertEqual(fk['to_col'], 'id')

    def test_generate_mermaid(self):
        schema = {
            'tables': [
                {
                    'name': 'users',
                    'columns': [{'name': 'id', 'type': 'INTEGER'}],
                    'fks': []
                },
                {
                    'name': 'posts',
                    'columns': [{'name': 'id', 'type': 'INTEGER'}, {'name': 'user_id', 'type': 'INTEGER'}],
                    'fks': [{'from_col': 'user_id', 'to_table': 'users', 'to_col': 'id'}]
                }
            ]
        }
        mermaid = self.parser.generate_mermaid(schema)
        self.assertIn("erDiagram", mermaid)
        self.assertIn("users {", mermaid)
        self.assertIn("posts }|..|| users : \"user_id->id\"", mermaid)

if __name__ == '__main__':
    unittest.main()
