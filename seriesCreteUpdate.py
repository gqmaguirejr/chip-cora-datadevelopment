import requests
import xml.etree.ElementTree as ET
import time
from collections import OrderedDict
from multiprocessing import Pool
from commondata import CommonData
from secretdata import SecretData

unit = 'norden'
system = 'preview'
recordType = 'diva-series'


def start():
    starttime = time.time()
    dataList = CommonData.read_source_xml(filePath_source_xml)
    for dataRecord in dataList.findall('.//DATA_RECORD'):
        buildedRecord = build_record(dataRecord)
        # validate_record(dataRecord)
        createdCoraRecord = create_new_record(buildedRecord)
        relationOldNewIds,linksToPrecedingIds, linksToHostIds = store_ids(dataRecord, createdCoraRecord)


        print(f"relation: {relationOldNewIds}")
        print(f"pre: {linksToPrecedingIds}")
        print(f"host: {linksToHostIds}")

    loop_id_lists(relationOldNewIds, linksToPrecedingIds, linksToHostIds)

    print(f'Tidsåtgång: {time.time() - starttime}')

def store_ids(dataRecord, createdCoraRecord):
    createdRecords = ET.fromstring(createdCoraRecord)
    createdRecords.findall('.//recordInfo')
    createdId = createdRecords.find('.//recordInfo/id')
    createdOldId = createdRecords.find('.//recordInfo/oldId')
    relationOldNewIds[createdOldId.text] = createdId.text
    precedingIds = dataRecord.find('.//relative_id_preceding')
    if precedingIds is not None and precedingIds.text:
        precedingIdsAsList = map(str.strip, precedingIds.text.split(','))
        linksToPrecedingIds[createdId.text] = precedingIdsAsList
    hostIds = dataRecord.find('.//relative_id_host')
    if hostIds is not None and hostIds.text:
        linksToHostIds[createdId.text] = hostIds.text
    return relationOldNewIds, linksToPrecedingIds, linksToHostIds

def loop_id_lists(relationOldNewIds, linksToPrecedingIds, linksToHostIds):
    starttime = time.time()
    for oldId, newId in relationOldNewIds.items():
        if newId in linksToPrecedingIds or newId in linksToHostIds:
            repeatId = 0
            newRecord = read_record_as_xml(newId)
            cleanedRecord = CommonData.remove_actionLinks_from_record(newRecord, recordType)
            if newId in linksToHostIds:
                parentOldId = linksToHostIds[newId]
                parentNewId = relationOldNewIds[parentOldId]
                related_subject_build(recordType, cleanedRecord, 'host', repeatId, parentNewId)
                repeatId +=1
            if newId in linksToPrecedingIds:
                earlierOldIds = linksToPrecedingIds[newId]
                for earlierOldId in earlierOldIds: 
                    earlierNewId = relationOldNewIds[earlierOldId]
                    related_subject_build(recordType, cleanedRecord, 'preceding', repeatId, earlierNewId)
                    repeatId +=1
            update_new_record(newId, cleanedRecord)
            print()
            print(newId, earlierOldId)
            
    print(f'Tidsåtgång: {time.time() - starttime}')

def related_subject_build(recordType, cleanedRecord, relatedType, counter, value): 
    related = ET.SubElement(cleanedRecord, 'related', repeatId=str(counter), type = relatedType)
    related_series = ET.SubElement(related, 'series')
    ET.SubElement(related_series, 'linkedRecordType').text = recordType
    ET.SubElement(related_series, 'linkedRecordId').text = value

def read_record_as_xml(id):
    authToken = SecretData.get_authToken(system)
    headersXml = {'Content-Type':'application/vnd.uub.record+xml', 'Accept':'application/vnd.uub.record+xml', 'authToken':authToken}
    getRecordUrl = base_url[system]+"diva-series/"+id
    response = requests.get(getRecordUrl, headers=headersXml)
    return ET.fromstring(response.text)

def update_new_record(id, recordToUpdate):
    authToken = SecretData.get_authToken(system)
    headersXml = {'Content-Type':'application/vnd.uub.record+xml', 'Accept':'application/vnd.uub.record+xml', 'authToken':authToken}
    recordUrl = base_url[system]+"diva-series/"+id
    output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"+ET.tostring(recordToUpdate).decode("UTF-8")
    response = requests.post(recordUrl, data=output, headers = headersXml)
    print(response.status_code, response.text)
    if response.status_code not in (200, 201, 409):
        with open('errorlog.txt', 'a', encoding='utf-8') as log:
            log.write(f'{response.status_code}. {response.text}\n\n')
    return response.text

def validate_record(dataRecord):
    authToken = SecretData.get_authToken(system)
    validate_headers_xml = {'Content-Type':'application/vnd.uub.workorder+xml', 'Accept':'application/vnd.uub.record+xml','authToken':authToken}
    validate_url = 'https://cora.epc.ub.uu.se/diva/rest/record/workOrder'
    new_record_toCreate = build_record(dataRecord)
    record_toValidate = build_validate_record(recordType, filePath_validateBase, new_record_toCreate)
    output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"+ET.tostring(record_toValidate).decode("UTF-8")
    response = requests.post(validate_url, data=output, headers = validate_headers_xml)
    print(response.status_code, response.text)
    if '<valid>true</valid>' not in response.text:
        with open(f'errorlog.txt', 'a', encoding='utf-8') as log:
            log.write(f"{response.status_code}. {response.text}\n\n")

def build_validate_record(recordType, filePath_validateBase, new_record_toCreate):
    validationOrder_baseFile = ET.parse(filePath_validateBase)
    validationOrder_root = validationOrder_baseFile.getroot()
    validationOrder_root.find('.//recordType/linkedRecordId').text = recordType
    validationOrder_root.find('.//validateLinks').text = 'false'
    validationOrder_root.find('.//metadataToValidate').text = 'new'
    record = validationOrder_root.find('.//record')
    record.append(new_record_toCreate)
    return validationOrder_root

def build_record(dataRecord):
    seriesRoot = ET.Element('series')
    recordInfo_build(seriesRoot, dataRecord)
    titleInfo_build(seriesRoot, dataRecord)
    titleInfo_alternative_build(seriesRoot, dataRecord, 'alternative')
    endDate_build(seriesRoot, dataRecord)
    location_build(seriesRoot, dataRecord)
    note_build(seriesRoot, dataRecord)
    counter = 0
    counter = identifier_build(seriesRoot, dataRecord, 'pissn', counter)
    counter = identifier_build(seriesRoot, dataRecord, 'eissn', counter)
    counter = genre_build(seriesRoot, dataRecord, publicationMap, counter)
    orgLink_build(seriesRoot, dataRecord)
    return seriesRoot

def orgLink_build(seriesRoot, dataRecord):
    orgOldIdFromSource = dataRecord.find('.//organisation_id')
    if orgOldIdFromSource is not None and orgOldIdFromSource.text:
        orgOldId = orgOldIdFromSource.text
        recordFromSearch = search_query_org_oldId(orgOldId)
        dataList = ET.fromstring(recordFromSearch)
        idToLink = dataList.find('.//recordInfo/id')
        if idToLink is not None and idToLink.text:
            relatedOrganisation = ET.SubElement(seriesRoot, 'organisation')
            ET.SubElement(relatedOrganisation, 'linkedRecordType').text = 'diva-organisation'
            ET.SubElement(relatedOrganisation, 'linkedRecordId').text = idToLink.text

def search_query_org_oldId(orgOldId):
    authToken = SecretData.get_authToken(system)
    search_headers_xml = {'Accept':'application/vnd.uub.recordList+xml','authToken':authToken}
    oldId_search_query = 'searchData={"name":"organisationSearch","children":[{"name":"include","children":[{"name":"includePart","children":[{"name":"genericIdSearchTerm","value":"'+orgOldId+'"}]}]}]}'
    search_url = base_url[system]+"searchResult/diva-organisationSearch?"+oldId_search_query
    response = requests.get(search_url, headers=search_headers_xml)
    return response.text

def genre_build(seriesRoot, dataRecord, publicationMap, counter):
    genreFromSource = dataRecord.find('.//publication_type_id')
    if genreFromSource is not None and genreFromSource.text:
        genre_value = publicationMap[genreFromSource.text]
        ET.SubElement(seriesRoot, 'genre', repeatId=str(counter), type = 'outputType').text = genre_value
        counter += 1
    return counter

def identifier_build(seriesRoot, dataRecord, identifierType, counter):
    identifierFromSource = dataRecord.find(f'.//{identifierType}')
    if identifierFromSource is not None and identifierFromSource.text:
        ET.SubElement(seriesRoot, 'identifier', displayLabel=identifierType, repeatId=str(counter), type = 'issn' ).text = identifierFromSource.text
        counter += 1
    return counter

def note_build(seriesRoot, dataRecord):
    note_fromSource = dataRecord.find('.//external_note')
    if note_fromSource is not None and note_fromSource.text:
        ET.SubElement(seriesRoot, 'note', type='external').text = note_fromSource.text

def location_build(seriesRoot, dataRecord):
    url_fromSource = dataRecord.find('.//url')
    if url_fromSource is not None and url_fromSource.text:
        location = ET.SubElement(seriesRoot, 'location')
        ET.SubElement(location, 'url').text = url_fromSource.text

def endDate_build(seriesRoot, dataRecord):
    dateFromSource = dataRecord.find('.//end_date')
    if dateFromSource is not None and dateFromSource.text:
        year, month, day = map(str.strip, dateFromSource.text.split('-'))
        originInfo = ET.SubElement(seriesRoot, 'originInfo')
        dateIssued = ET.SubElement(originInfo, 'dateIssued', point = 'end')
        ET.SubElement(dateIssued, 'year').text = year
        ET.SubElement(dateIssued, 'month').text = month
        ET.SubElement(dateIssued, 'day').text = day

def titleInfo_alternative_build(seriesRoot, dataRecord, titleType):
    titleFromSource = dataRecord.find('.//alternative_title')
    if titleFromSource is not None and titleFromSource.text:
        titleInfo = ET.SubElement(seriesRoot, 'titleInfo', type = titleType)
        ET.SubElement(titleInfo, 'title').text = titleFromSource.text
    subTitleFromSource = dataRecord.find('.//alterantive_sub_title')
    if subTitleFromSource is not None and subTitleFromSource.text:
        ET.SubElement(titleInfo, 'subTitle').text = subTitleFromSource.text

def titleInfo_build(seriesRoot, dataRecord):
    titleFromSource = dataRecord.find('.//main_title')
    if titleFromSource is not None and titleFromSource.text:
        titleInfo = ET.SubElement(seriesRoot, 'titleInfo')
        ET.SubElement(titleInfo, 'title').text = titleFromSource.text
    subTitleFromSource = dataRecord.find('.//sub_title')
    if subTitleFromSource is not None and subTitleFromSource.text:
        ET.SubElement(titleInfo, 'subTitle').text = subTitleFromSource.text

def recordInfo_build(seriesRoot, dataRecord):
    recordInfo = ET.SubElement(seriesRoot, 'recordInfo')
    # ET.SubElement(recordInfo, 'recordContentSource').text = unit
    validationType = ET.SubElement(recordInfo, 'validationType')
    ET.SubElement(validationType, 'linkedRecordType').text = 'validationType'
    ET.SubElement(validationType, 'linkedRecordId').text = recordType
    dataDivider = ET.SubElement(recordInfo, 'dataDivider')
    ET.SubElement(dataDivider, 'linkedRecordType').text = 'system'
    ET.SubElement(dataDivider, 'linkedRecordId').text = 'divaData'
    permissionUnit = ET.SubElement(recordInfo, 'permissionUnit')
    ET.SubElement(permissionUnit, 'linkedRecordType').text = 'permissionUnit'
    ET.SubElement(permissionUnit, 'linkedRecordId').text= unit
    oldIdFromSource = dataRecord.find('.//old_id')
    ET.SubElement(recordInfo, 'oldId').text = oldIdFromSource.text

def create_new_record(recordToCreate):
    authToken = SecretData.get_authToken(system)
    headersXml = {'Content-Type':'application/vnd.uub.record+xml', 'Accept':'application/vnd.uub.record+xml', 'authToken':authToken}
    urlCreate = base_url[system]+recordType
    output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"+ET.tostring(recordToCreate).decode("UTF-8")
    response = requests.post(urlCreate, data=output, headers = headersXml)
    print(response.status_code, response.text)
    if response.status_code not in (200, 201, 409):
        with open('errorlog.txt', 'a', encoding='utf-8') as log:
            log.write(f'{response.status_code}. {response.text}\n\n')
    return response.text

# listor
relationOldNewIds = OrderedDict()
linksToPrecedingIds = OrderedDict()  
linksToHostIds = OrderedDict()

# filer
filePath_validateBase = (r'validationOrder_base.xml')
filePath_source_xml = (r"db_xml\series_"+unit+"_db.xml")

# basic url for records
base_url = {
    'preview': 'https://cora.epc.ub.uu.se/diva/rest/record/',
    'dev': 'http://130.238.171.238:38082/diva/rest/record/',
    'pre': 'https://pre.diva-portal.org/rest/record/',
    'mig': 'https://mig.diva-portal.org/rest/record/'
}

publicationMap = {
    '50': 'publication_journal-article',
    '51': 'publication_review-article',
    '52': 'publication_book-review',
    '53': 'publication_doctoral-thesis-compilation', 
    '54': 'publication_doctoral-thesis-monograph',
    '55': 'publication_licentiate-thesis-compilation',
    '56': 'publication_licentiate-thesis-monograph',
    '57': 'publication_book',
    '58': 'publication_book-chapter',
    '59': 'conference_paper', 
    '60': 'conference_proceeding',
    '61': 'intellectual-property_patent',
    '62': 'publication_report', 
    '63': 'publication_edited-book',
    '64': 'publicationPreprintItem',
    '65': 'diva_degree-project',
    '66': 'publication_other',
    '67': 'diva_dissertation',
    '71': 'artistic-work_original-creative-work'
}

start()