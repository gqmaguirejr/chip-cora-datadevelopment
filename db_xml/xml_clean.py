import xml.etree.ElementTree as ET
import re

# Regex to remove invalid XML characters (XML 1.0 standard)
INVALID_XML_CHAR_RE = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x84\x86-\x9F]"
)

def clean_text(text):
    """Removes invalid XML characters and trims whitespace."""
    if text:
        text = text.strip()  # Remove leading/trailing spaces
        text = INVALID_XML_CHAR_RE.sub("", text)  # Remove invalid characters
    return text

def clean_xml(input_file, output_file):
    """Fixes encoding issues and removes invalid XML characters."""
    # Read file in binary mode to prevent decoding errors
    with open(input_file, "rb") as f:
        raw_data = f.read()

    # Decode with error handling (replace unknown chars with '?')
    text_data = raw_data.decode("utf-8", errors="replace")

    # Remove invalid XML characters
    cleaned_data = INVALID_XML_CHAR_RE.sub("", text_data)

    # Parse cleaned XML
    root = ET.fromstring(cleaned_data)  # Convert back to XML

    # Recursively clean all text elements
    def clean_element(element):
        if element.text:
            element.text = clean_text(element.text)
        if element.tail:
            element.tail = clean_text(element.tail)
        for child in element:
            clean_element(child)

    clean_element(root)

    # Save the cleaned XML file
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)


# Exempel på användning
clean_xml("/home/sarto903/cora_python/db_xml/_SELECT_j_journal_id_AS_old_id_jt_main_title_AS_title_jt_sub_tit_202504240921.xml", "/home/sarto903/git/cora-datadevelopment/db_xml/journal_from_db.xml")
