import unittest
from research import summarize


class PapersTest(unittest.TestCase):
    def test_duplicate_and_missing_identity(self):
        paper = {'source': 'MED', 'id': '123', 'title': 'Trial',
                 'pubTypeList': {'pubType': ['Randomized Controlled Trial']}}
        result = summarize([paper, paper, {'title': 'No identifier'}])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['url'], 'https://europepmc.org/article/MED/123')
        self.assertIn('unreviewed', result[0]['status'])

    def test_sparse_record(self):
        result = summarize([{'source': 'PMC', 'id': 'PMC123'}])[0]
        self.assertEqual(result['abstract'], '')
        self.assertEqual(result['publication_types'], [])
