import requests
import json
from collections import OrderedDict
from multiprocessing import Pool
import time
import xml.etree.ElementTree as ET
from secretdata import SecretData
from coradata import CoraData


urlSpecificDomain = 'https://cora.diva-portal.org/diva/rest/record/searchResult/publicOrganisationSearch?searchData={"name":"search","children":[{"name":"include","children":[{"name":"includePart","children":[{"name":"divaOrganisationDomainSearchTerm","value":"polar"}]}]}]}'


def start():
    starttime = time.time()
    json_data = json.loads(search()) # converted json to python objects
    print(f"Antal sökträffar: {json_data['dataList']['totalNo']}")
    workorders = []
    newRecords = []
    createdCoraRecordResponseText = []
    for record in json_data['dataList']['data']:
        recordChildren = record['record']['data']['children'] # listar alla barn till record
        recordInfoChild = CoraData.findChildWithNameInData(recordChildren, 'recordInfo') # hittar recordInfo
        recordInfoChildren = recordInfoChild['children'] # listar alla barn till recordInfo
        validationType = CoraData.getValidationTypeLink(recordInfoChildren)
        domain = CoraData.getFirstAtomicValueWithNameInData(recordInfoChildren, 'domain')
        if domain != "ntnu" and domain != "hhs" and domain != "hkr" and validationType != "rootOrganisation":
            workorder = buildRecordToCreateAndValidate(domain, recordChildren, recordInfoChildren) # skapar workorder och record
            newRecord = workorder["record"] # plockar ut record
            createdCoraRecordResponseText = createRecord(newRecord) # create record, makes a request
            # validateRecord(workorder) # validate, makes a request
            # workorders.append(buildRecordToCreateAndValidate(domain, recordChildren, recordInfoChildren)) # aktiveras för att köra i poolen
            # print(workorder)
            # print(newRecord)
            relationOldNewIds, linksToEarlierId, linksToParentId = storeIdData(recordChildren, createdCoraRecordResponseText)

    print(f"relationOldNewIds: {relationOldNewIds}")
    print(f"linksToEarlierId: {linksToEarlierId}")
    print(f"linksToParentId: {linksToParentId}")

    loopIdLists(relationOldNewIds, linksToEarlierId, linksToParentId)

    """ if __name__ == "__main__":
        with Pool(WORKERS) as pool:
            pool.map(validateRecord, workorders) """
    print(f'Tidsåtgång: {time.time() - starttime}')


system = "preview"
WORKERS = 16
NUMBEROFVALIDATEDRECORDS = 0


def search():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(urlSpecificDomain, headers=headers)
    return(response.text)

def buildRecordToCreateAndValidate(domain, recordChildren, recordInfoChildren):
    recordInfoList = []
    recordBodyList = []
    newAddressList = []
    # recordInfo
    newDomain = checkDomainAndSetNewValue(domain)
    CoraData.appendValueToList(newDomain, {'children': [{'name': "linkedRecordType", 'value': "permissionUnit"}, {'name': "linkedRecordId", 'value': newDomain}], 'name': 'permissionUnit'}, recordInfoList)
    id = CoraData.getFirstAtomicValueWithNameInData(recordInfoChildren, 'id')
    CoraData.appendValueToList(id, {'name': "oldId", 'value': id}, recordInfoList)
    validationType = CoraData.getValidationTypeLink(recordInfoChildren)
    newValidationType = checkValidationTypeLinkAndGetNewValue(validationType)
    CoraData.appendValueToList(newValidationType, {'children': [{'name': "linkedRecordType", 'value': "validationType"}, {'name': "linkedRecordId", 'value': newValidationType}], 'name': 'validationType'}, recordInfoList)
    CoraData.appendValueToList("valueNotNone", {'children': [{'name': "linkedRecordType", 'value': "system"}, {'name': "linkedRecordId", 'value': "divaData"}], 'name': 'dataDivider'}, recordInfoList)
    recordBodyList.append({'children': recordInfoList, 'name': "recordInfo"})
    # parts of record
    namePartSwe = CoraData.getOrganisationNameValueWithNameInData(recordChildren, 'organisationName')
    CoraData.appendValueToList(namePartSwe, {'children': [{'children': [{'name': "namePart", 'value': namePartSwe}], 'name': "name", 'attributes': {'type': "corporate"}}], 'name': "authority", 'attributes': {'lang': "swe"}}, recordBodyList)
    namePartEng = CoraData.getOrganisationNameValueWithNameInData(recordChildren, 'organisationAlternativeName')
    CoraData.appendValueToList(namePartEng, {'children': [{'children': [{'name': "namePart", 'value': namePartEng}], 'name': "name", 'attributes': {'type': "corporate"}}], 'name': "variant", 'attributes': {'lang': "eng"}}, recordBodyList)
    url = CoraData.getFirstAtomicValueWithNameInData(recordChildren, 'URL')
    CoraData.appendValueToList(url, {'children': [{'name': "url", 'value': url}], 'name': "location"}, recordBodyList)
    orgNum = CoraData.getFirstAtomicValueWithNameInData(recordChildren, 'organisationNumber')
    CoraData.appendValueToList(orgNum, {'name': "identifier", 'attributes': {'type': "organisationNumber"}, 'value': orgNum}, recordBodyList)
    orgCode = CoraData.getFirstAtomicValueWithNameInData(recordChildren, 'organisationCode')
    CoraData.appendValueToList(orgCode, {'name': "identifier", 'attributes': {'type': "organisationCode"}, 'value': orgCode}, recordBodyList)
    endDate = CoraData.getFirstAtomicValueWithNameInData(recordChildren, 'closedDate')
    if endDate is not None:
        year, month, day = endDate.split("-")
        CoraData.appendValueToList(endDate, {'children': [{'children': [{'name': "year", 'value': year}, {'name': "month", 'value': month}, {'name': "day", 'value': day}], 'name':"endDate"}] , 'name': "organisationInfo"}, recordBodyList)
    adressChild = CoraData.findChildWithNameInData(recordChildren, 'address')
    if adressChild is not None:
        adressChildren = adressChild['children'] # listar alla barn till address
        postOfficeBox = CoraData.getFirstAtomicValueWithNameInData(adressChildren, 'box')
        CoraData.appendValueToList(postOfficeBox, {"name": "postOfficeBox", "value": postOfficeBox}, newAddressList)
        street = CoraData.getFirstAtomicValueWithNameInData(adressChildren, 'street')
        CoraData.appendValueToList(street, {"name": "street", "value": street}, newAddressList)
        postcode = CoraData.getFirstAtomicValueWithNameInData(adressChildren, 'postcode')
        CoraData.appendValueToList(postcode, {"name": "postcode", "value": postcode}, newAddressList)
        place = CoraData.getFirstAtomicValueWithNameInData(adressChildren, 'city')
        CoraData.appendValueToList(place, {"name": "place", "value": place}, newAddressList)
        country = CoraData.getFirstAtomicValueWithNameInData(adressChildren, 'country')
        newCountry = checkCountryAndSetNewValue(country)
        CoraData.appendValueToList(newCountry, {"name": "country", "value": newCountry}, newAddressList)
    CoraData.appendValueToList(adressChild, {'children': newAddressList, 'name': "address"}, recordBodyList)
    newRecord = {'children': recordBodyList, 'name': "organisation"}
    workorder = createWorkOrder(workorderBase, newRecord)
    return workorder

### KEEP DATA
def storeIdData(recordChildren, createdCoraRecordResponseText):
    coraRecord = json.loads(createdCoraRecordResponseText)
    coraRecordChildren = coraRecord['record']['data']['children']
    coraRecordRecordInfoChild = CoraData.findChildWithNameInData(coraRecordChildren, 'recordInfo')
    coraRecordRecordInfoChildren = coraRecordRecordInfoChild['children'] # borde kuna slås ihop ovan och använda en av befintliga funktionerna istället
    newId = (CoraData.getFirstAtomicValueWithNameInData(coraRecordRecordInfoChildren, 'id'))
    oldId = (CoraData.getFirstAtomicValueWithNameInData(coraRecordRecordInfoChildren, 'oldId'))
    earlierLinkOldId = CoraData.getParentEarlierLinks(recordChildren, 'earlierOrganisation')
    parentLinkOldId = CoraData.getParentEarlierLinks(recordChildren, 'parentOrganisation')
    print(f"earlier: {earlierLinkOldId}")
    print(f"earlier size: {len(earlierLinkOldId)}")
    print(f"parent: {parentLinkOldId}")
    print(f"earlier size: {len(parentLinkOldId)}")
    if len(earlierLinkOldId) > 0:
        linksToEarlierId[newId] = earlierLinkOldId
    if len(parentLinkOldId) > 0:
        linksToParentId[newId] = parentLinkOldId      
    relationOldNewIds[oldId] = newId
    return relationOldNewIds, linksToEarlierId, linksToParentId

# listor
relationOldNewIds = OrderedDict()
linksToEarlierId = OrderedDict()  
linksToParentId = OrderedDict()

### VALIDATE
def openValidationOrderBaseFile():
    validationOrder_baseFile = (r"validationOrder_base.json")
    with open(validationOrder_baseFile, 'r') as openfile:
        validationObject = json.load(openfile)
    return validationObject

def createWorkOrder(workorderBase, newRecord):
    workorderBase['order']['children'][1]['children'][1]['value'] = recordType
    workorderBase['order']['children'][2]['value'] = validateLinks
    workorderBase['order']['children'][3]['value'] = metadataToValidate
    workorderBase["record"] = newRecord
    return workorderBase

workorderBase = openValidationOrderBaseFile() #hämtar filen
recordType = "diva-organisation"
validateLinks = "false" # "true || false"
metadataToValidate = "new" # "new || existing"

def validateRecord(recordToValidate):
    authToken = SecretData.get_authToken(system)
    validate_headers_json = {'Content-Type':'application/vnd.uub.workorder+json', 'Accept':'application/vnd.uub.record+json', 'authToken':authToken}
    validate_url = base_url[system]+"workOrder"
    output = json.dumps(recordToValidate)
    response = requests.post(validate_url, data=output, headers = validate_headers_json)
    print(response.status_code, response.text) # response.text
    text = response.json()
    if text['record']['data']['children'][1]['name'] == "errorMessages":
        print(text['record']['data']['children'][1]['children'])
        with open(f'errorlog.txt', 'a', encoding='utf-8') as log:
            log.write(f"{response.status_code}. {response.text}\n\n")
    elif text['record']['data']['children'][1]['value'] == "true":
        print(text['record']['data']['children'][1]['value'])

# CREATE
def createRecord(recordToCreate):
    authToken = SecretData.get_authToken(system)
    headers_json = {'Content-Type':'application/vnd.uub.record+json', 'Accept':'application/vnd.uub.record+json', 'authToken':authToken}
    create_url = base_url[system]+'diva-organisation/'
    output = json.dumps(recordToCreate)
    response = requests.post(create_url, data=output, headers = headers_json)
    print(response.status_code, response.text) #
    if response.status_code not in (200, 201, 409):
        with open('errorlog.txt', 'a', encoding='utf-8') as log:
            log.write(f'{response.status_code}. {response.text}\n\n')
    return response.text

### UPDATE
def readRecordAsJson(id):
    authToken = SecretData.get_authToken(system)
    headers_json = {'Accept':'application/vnd.uub.record+json', 'authToken':authToken}
    getRecordUrl = base_url[system]+"diva-organisation/"+id
    response = requests.get(getRecordUrl, headers=headers_json)
    return json.loads(response.text)

def loopIdLists(relationOldNewIds, linksToEarlierId, linksToParentId):
    starttime = time.time()
    print(linksToParentId)
    for oldId, newId in relationOldNewIds.items():
        if newId in linksToEarlierId or newId in linksToParentId:
            newRecord = readRecordAsJson(newId)
            cleanedRecord = removeActionLinksFromRecord(newRecord)
            recordChildren = cleanedRecord['children']
            if newId in linksToParentId:
                parentOldId = linksToParentId[newId][0]
                parentNewId = relationOldNewIds[parentOldId]
                recordChildren.append(createParentLink(parentNewId))
            if newId in linksToEarlierId:
                earlierOldIds = linksToEarlierId[newId]
                repeatId = 0
                for earlierOldId in earlierOldIds:
                    earlierNewId = relationOldNewIds[earlierOldId]
                    recordChildren.append(createEarlierLink(earlierNewId, repeatId))
                    repeatId +=1
            print()
            print(newId)
            print(f"updatedRecord: {cleanedRecord}")
            print()
            updateNewRecord(newId, cleanedRecord)

    print(f'Tidsåtgång: {time.time() - starttime}')

def updateNewRecord(id, recordToUpdate):
    authToken = SecretData.get_authToken(system)
    headers_json = {'Content-Type':'application/vnd.uub.record+json', 'Accept':'application/vnd.uub.record+json', 'authToken':authToken}
    recordUrl = base_url[system]+"diva-organisation/"+id
    output = json.dumps(recordToUpdate)
    response = requests.post(recordUrl, data=output, headers = headers_json)
    print(response.status_code, response.text)
    if response.status_code not in (200, 201, 409):
        with open('errorlog.txt', 'a', encoding='utf-8') as log:
            log.write(f'{response.status_code}. {response.text}\n\n')
    return response.text

def createParentLink(id):
    return {'children': [
        {'children': [{'name': "linkedRecordType", 'value': "diva-organisation"}, 
                      {'name': "linkedRecordId", 'value': id}], 'name': "organisation"}],
                        'name': "related", 'attributes': {'type': "parent"}}

def createEarlierLink(id, repeatId):
    repeatId=str(repeatId)
    return {'children': 
            [{'children': 
              [{'name': "linkedRecordType", 'value': "diva-organisation"}, 
               {'name': "linkedRecordId", 'value': id}], 'name': "organisation"}],
                'name': "related", 'repeatId': repeatId, 'attributes': {'type': "earlier"}}


def removeActionLinksFromDataList(dataList): # används inte just nu...
    for recordToClean in dataList['dataList']['data']:
        record = removeActionLinksFromRecord(recordToClean)
    return record

def removeActionLinksFromRecord(recordToClean):
    record = recordToClean['record']['data'] # denna nivå ska returneras?
    recordChildren = recordToClean['record']['data']['children']
    recordInfo = CoraData.findChildWithNameInData(recordChildren, 'recordInfo')
    permissionUnit = CoraData.findChildWithNameInData(recordInfo['children'], 'permissionUnit')
    del permissionUnit['actionLinks']
    validationType = CoraData.findChildWithNameInData(recordInfo['children'], 'validationType')
    del validationType['actionLinks']
    dataDivider = CoraData.findChildWithNameInData(recordInfo['children'], 'dataDivider')
    del dataDivider['actionLinks']
    type = CoraData.findChildWithNameInData(recordInfo['children'], 'type')
    del type['actionLinks']
    createdBy = CoraData.findChildWithNameInData(recordInfo['children'], 'createdBy')
    del createdBy['actionLinks']
    updated = CoraData.findChildWithNameInData(recordInfo['children'], 'updated')
    updatedBy = CoraData.findChildWithNameInData(updated['children'], 'updatedBy')
    del updatedBy['actionLinks']
    return record

# basic url for records
base_url = {
    'preview': 'https://cora.epc.ub.uu.se/diva/rest/record/',
    'dev': 'http://130.238.171.238:38082/diva/rest/record/',
    'pre': 'https://pre.diva-portal.org/rest/record/',
    'mig': 'https://mig.diva-portal.org/rest/record/'
}

def checkValidationTypeLinkAndGetNewValue(validationType): # behöver skippa posten om den har rot.
    if validationType == "subOrganisation":
        newValidationType = "diva-partOfOrganisation"
        return newValidationType
    elif validationType == "topOrganisation":
        newValidationType = "diva-topOrganisation"
        return newValidationType
    else:
        return validationType
    
def checkCountryAndSetNewValue(country):
    if country == "SE":
        newCountry = "sw"
        return newCountry
    elif country == "FI":
        newCountry = "fi"
        return newCountry
    elif country == "DK":
        newCountry = "dk"
        return newCountry

def checkDomainAndSetNewValue(domain): # 6 domains that change name
    if domain == "esh":
        newDomain = "mchs"
        return newDomain
    elif domain == "mdh":
        newDomain = "mdu"
        return newDomain
    elif domain == "hj":
        newDomain = "ju"
        return newDomain
    elif domain == "uniarts":
        newDomain = "skh"
        return newDomain
    elif domain == "sprakochfolkminnen":
        newDomain = "isof"
        return newDomain
    elif domain == "ths":
        newDomain = "ehs"
        return newDomain
    else: 
        return domain

start()