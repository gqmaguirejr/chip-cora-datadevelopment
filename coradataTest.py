import unittest
from coradata import CoraData

class TestCoraData(unittest.TestCase):

    def test_findChildWithNameInData(self):
        children = [
            {'name': 'child1', 'value': 'value1'},
            {'name': 'child2', 'value': 'value2'},
            {'name': 'child3', 'value': 'value3'}
        ]
        self.assertEqual(CoraData.findChildWithNameInData(children, 'child2'), {'name': 'child2', 'value': 'value2'})
        self.assertIsNone(CoraData.findChildWithNameInData(children, 'child4'))

    def test_getValueWithNameInData(self):
        child = {'name': 'child1', 'value': 'value1'}
        self.assertEqual(CoraData.getValueWithNameInData(child), 'value1')
        self.assertIsNone(CoraData.getValueWithNameInData(None))

    def test_getFirstAtomicValueWithNameInData(self):
        children = [
            {'name': 'child1', 'value': 'value1'},
            {'name': 'child2', 'value': 'value2'},
        ]
        self.assertEqual(CoraData.getFirstAtomicValueWithNameInData(children, 'child2'), 'value2')
        self.assertIsNone(CoraData.getFirstAtomicValueWithNameInData(children, 'child3'))

    def test_appendValueToList(self):
        test_list = []
        CoraData.appendValueToList('value1', 'element1', test_list)
        self.assertEqual(test_list, ['element1'])
        CoraData.appendValueToList(None, 'element2', test_list)
        self.assertEqual(test_list, ['element1'])

    def test_getOrganisationNameValueWithNameInData(self):
        children = [
            {'name': 'org1', 'children': [{'name': 'name', 'value': 'OrgName1'}]},
            {'name': 'org2', 'children': [{'name': 'name', 'value': 'OrgName2'}]}
        ]
        self.assertEqual(CoraData.getOrganisationNameValueWithNameInData(children, 'org2'), 'OrgName2')

    def test_getLinkedRecordIdWithNameInData(self):
        children = [
            {'name': 'link1', 'children': [{'name': 'linkedRecordId', 'value': 'ID1'}]},
            {'name': 'link2', 'children': [{'name': 'linkedRecordId', 'value': 'ID2'}]}
        ]
        self.assertEqual(CoraData.getLinkedRecordIdWithNameInData(children, 'link2'), 'ID2')

    def test_getValidationTypeLink(self):
        recordInfoChildren = [
            {'name': 'type', 'children': [{'name': 'linkedRecordId', 'value': 'TypeID'}]}
        ]
        self.assertEqual(CoraData.getValidationTypeLink(recordInfoChildren), 'TypeID')

    def test_getParentEarlierLinks(self):
        recordChildren = [
            {'name': 'orgLink', 'children': [{'name': 'organisationLink', 'children': [{'name': 'linkedRecordId', 'value': 'OrgID1'}]}]},
            {'name': 'orgLink', 'children': [{'name': 'organisationLink', 'children': [{'name': 'linkedRecordId', 'value': 'OrgID2'}]}]},
            {'name': 'otherLink', 'children': [{'name': 'organisationLink', 'children': [{'name': 'linkedRecordId', 'value': 'OrgID3'}]}]}
        ]
        self.assertEqual(CoraData.getParentEarlierLinks(recordChildren, 'orgLink'), ['OrgID1', 'OrgID2'])

if __name__ == '__main__':
    unittest.main()
