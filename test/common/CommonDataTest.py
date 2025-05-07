import unittest
from test.TestHelper import TestHelper
from common.CommonData import CommonData

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass
    
    def test_create_link(self):
        name_in_data = "someNameInData"
        record_type = "someType"
        record_id = "someId"
        
        link = CommonData.create_record_link_using_name_type_id(name_in_data, record_type, record_id)
        
        expected_xml = """
                        <someNameInData>
                            <linkedRecordType>someType</linkedRecordType>
                            <linkedRecordId>someId</linkedRecordId>
                        </someNameInData>
                        """
        
        TestHelper.assert_equal_for_xml_and_xml_string(link, expected_xml)
        
    def test_create_record_info(self):
        record_info = CommonData.create_record_info_for_record_type("someRecordType")
        
        expected_xml = """
                        <recordInfo>
                            <validationType>
                                <linkedRecordType>validationType</linkedRecordType>
                                <linkedRecordId>diva-someRecordType</linkedRecordId>
                            </validationType>
                            <dataDivider>
                                <linkedRecordType>system</linkedRecordType>
                                <linkedRecordId>divaData</linkedRecordId>
                            </dataDivider>
                        </recordInfo>
                        """

        TestHelper.assert_equal_for_xml_and_xml_string(record_info, expected_xml)

if __name__ == "__main__":
    unittest.main()