import xml.etree.ElementTree as ET
class  CommonData:

    @staticmethod
    def read_source_xml(filePath_sourceXml):
        sourceFile_xml = ET.parse(filePath_sourceXml)
        root = sourceFile_xml.getroot()
        return root
    
    @staticmethod
    def remove_action_link(element):
        for actionLinks in element.findall('actionLinks'):
            element.remove(actionLinks)

    @staticmethod
    def remove_actionLinks_from_record(record, recordType):
        for clean_record in record.findall(f'.//{recordType}'):
            for validationType in clean_record.findall('.//validationType'):
                CommonData.remove_action_link(validationType)
            for dataDivider in clean_record.findall('.//dataDivider'):
                CommonData.remove_action_link(dataDivider)
            for permissionUnit in clean_record.findall('.//permissionUnit'):
                CommonData.remove_action_link(permissionUnit)
            for type in clean_record.findall('.//type'):
                CommonData.remove_action_link(type)
            for createdBy in clean_record.findall('.//createdBy'):
                CommonData.remove_action_link(createdBy)
            for updatedBy in clean_record.findall('.//updatedBy'):
                CommonData.remove_action_link(updatedBy)
        return clean_record
    
    @staticmethod
    def validateRecord_build(recordType, filePath_validateBase, newRecordToCreate):
        validationOrder_root = CommonData.read_source_xml(filePath_validateBase)
        validationOrder_root.find('.//recordType/linkedRecordId').text = "diva-"+recordType
        validationOrder_root.find('.//validateLinks').text = 'false'
        validationOrder_root.find('.//metadataToValidate').text = 'new'
        record = validationOrder_root.find('.//record')
        record.append(newRecordToCreate)
        return validationOrder_root
    
    @staticmethod
    def recordInfo_build(recordType, data_record, newRecordElement):
        recordInfo = ET.SubElement(newRecordElement, 'recordInfo')
        validationType = ET.SubElement(recordInfo, 'validationType')
        ET.SubElement(validationType, 'linkedRecordType').text = 'validationType'
        ET.SubElement(validationType, 'linkedRecordId').text = 'diva-'+recordType
        dataDivider = ET.SubElement(recordInfo, 'dataDivider')
        ET.SubElement(dataDivider, 'linkedRecordType').text = 'system'
        ET.SubElement(dataDivider, 'linkedRecordId').text = 'divaData'
        oldId_fromSource = data_record.find('.//old_id')
        ET.SubElement(recordInfo, 'oldId').text = oldId_fromSource.text

    @staticmethod
    def recordInfoUnit_build(recordType, unit, data_record, newRecordElement):
        recordInfo = ET.SubElement(newRecordElement, 'recordInfo')
        validationType = ET.SubElement(recordInfo, 'validationType')
        ET.SubElement(validationType, 'linkedRecordType').text = 'validationType'
        ET.SubElement(validationType, 'linkedRecordId').text = 'diva-'+recordType
        dataDivider = ET.SubElement(recordInfo, 'dataDivider')
        ET.SubElement(dataDivider, 'linkedRecordType').text = 'system'
        ET.SubElement(dataDivider, 'linkedRecordId').text = 'divaData'
        if unit is not None:
            permissionUnit = ET.SubElement(recordInfo, 'permissionUnit')
            ET.SubElement(permissionUnit, 'linkedRecordType').text = 'permissionUnit'
            ET.SubElement(permissionUnit, 'linkedRecordId').text= unit
        oldIdFromSource = data_record.find('.//old_id')
        ET.SubElement(recordInfo, 'oldId').text = oldIdFromSource.text
    
    @staticmethod
    def get_oldId(data_record):
        oldId_fromSource = data_record.find('.//old_id')
        # print(oldId_fromSource.text)
        return oldId_fromSource.text

    @staticmethod
    def name_build(data_record, newRecordElement):
        name_fromSource = data_record.find('.//name')
        if name_fromSource is not None and name_fromSource.text:
            name = ET.SubElement(newRecordElement, 'name', type = 'corporate')
            ET.SubElement(name, 'namePart').text = name_fromSource.text

    @staticmethod
    def nameAuthorityVariant_build(data_record, newRecordElement, elementName, language):
        nameLang_fromSource = data_record.find(f'.//name_{language}')
        if nameLang_fromSource is not None and nameLang_fromSource.text:
            name = ET.SubElement(newRecordElement, elementName, lang = language)
            nameType = ET.SubElement(name, 'name', type = 'corporate')
            ET.SubElement(nameType, 'namePart').text = nameLang_fromSource.text

    @staticmethod
    def topicAuthorityVariant_build(data_record, newRecordElement, elementName, language):
        topicLang_fromSource = data_record.find(f'.//topic_{language}')
        topic = ET.SubElement(newRecordElement, elementName, lang = language)
        ET.SubElement(topic, 'topic').text = topicLang_fromSource.text

    @staticmethod
    def titleInfo_build(data_record, newRecordElement):
        title_fromSource = data_record.find(f'.//title')
        if title_fromSource is not None and title_fromSource.text:
            titleInfo = ET.SubElement(newRecordElement, 'titleInfo')
            ET.SubElement(titleInfo, 'title').text = title_fromSource.text
        subTitle_fromSource = data_record.find(f'.//subTitle')
        if subTitle_fromSource is not None and subTitle_fromSource.text:
            ET.SubElement(titleInfo, 'subTitle').text = subTitle_fromSource.text

    @staticmethod
    def identifier_build(data_record, newRecordElement, identifierType, counter):
        identifier_fromSource = data_record.find(f'.//identifier_{identifierType}')
        if identifier_fromSource is not None and identifier_fromSource.text:
            if identifierType in ('pissn', 'eissn'):      
                ET.SubElement(newRecordElement, 'identifier', displayLabel=identifierType, repeatId=str(counter), type = 'issn').text = identifier_fromSource.text
                counter += 1
            else:
                ET.SubElement(newRecordElement, 'identifier', type=identifierType).text = identifier_fromSource.text
        return counter
    
    @staticmethod
    def endDate_build(data_record, newRecordElement, originType):
        date_fromSource = data_record.find('.//end_date')
        if date_fromSource is not None and date_fromSource.text:
            year, month, day = map(str.strip, date_fromSource.text.split('-'))
            if originType == 'originInfo':
                originInfo = ET.SubElement(newRecordElement, originType)
                dateIssued = ET.SubElement(originInfo, 'dateIssued', point = 'end')
                CommonData.endDate_yearMonthDay(year, month, day, dateIssued)
            elif originType == 'organisationInfo':
                organisationInfo = ET.SubElement(newRecordElement, originType)
                endDate = ET.SubElement(organisationInfo, 'endDate')
                CommonData.endDate_yearMonthDay(year, month, day, organisationInfo)
            else:
                endDate = ET.SubElement(newRecordElement, 'endDate')
                CommonData.endDate_yearMonthDay(year, month, day, endDate)

    @staticmethod
    def endDate_yearMonthDay(year, month, day, rootElement):
        ET.SubElement(rootElement, 'year').text = year
        ET.SubElement(rootElement, 'month').text = month
        ET.SubElement(rootElement, 'day').text = day

    @staticmethod
    def location_build(data_record, newRecordElement):
        url_fromSource = data_record.find('.//url')
        if url_fromSource is not None and url_fromSource.text:
            location = ET.SubElement(newRecordElement, 'location')
            ET.SubElement(location, 'url').text = url_fromSource.text