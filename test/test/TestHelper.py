import unittest as unittest
import xml.etree.ElementTree as ET

class TestHelper():

    @staticmethod        
    def assert_equal_for_xml_and_xml_string(record_info, expected_xml):
        expected_as_xml = ET.fromstring(expected_xml)
        expected_normalized = TestHelper.__normalize_xml_string(expected_as_xml)
        record_info_normalized = TestHelper.__normalize_xml_string(record_info)

        test_case = unittest.TestCase()
        test_case.assertEqual(record_info_normalized, expected_normalized)
    
    @staticmethod    
    def __normalize_xml_string(xml):
        if isinstance(xml, str):
            root = ET.fromstring(xml)
        else:
            root = xml  # already an Element
    
        def canonicalize(elem):
            attribs = ' '.join(f'{k}="{v}"' for k, v in sorted(elem.attrib.items()))
            start_tag = f"<{elem.tag}{(' ' + attribs) if attribs else ''}>"
    
            text = (elem.text or '').strip()
            children = ''.join(canonicalize(child) for child in elem)
            end_tag = f"</{elem.tag}>"
    
            return f"{start_tag}{text}{children}{end_tag}"
    
        return canonicalize(root)
    
if __name__ == "__main__":
    unittest.main()