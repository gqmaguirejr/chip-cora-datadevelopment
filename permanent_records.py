import xml.etree.ElementTree as ET
import requests

# skapar en av varje posttyp enligt lista.
# diva-output
# diva-publisher
# diva-journal
# diva-funder
# diva-publisher
# diva-person
# diva-series
# diva-subject
# diva-course
# diva-project
# diva-programme
# diva-partOfOrganisation
# diva-topOrganisation
# diva-localGenericMarkup

# hämta authToken

def get_authToken():
    #getAuthTokenUrl = 'https://cora.epc.ub.uu.se/diva/login/rest/apptoken' #<-- behöver ändra miljö manuellt just nu!
    getAuthTokenUrl = 'http://130.238.171.238:38182/login/rest/apptoken' 
    appToken = 'divaAdmin@cora.epc.ub.uu.se\nAPPTOKEN_HERE'
    json_headers = {'Content-Type':'application/vnd.uub.login', 'Accept':'application/vnd.uub.authentication+json'}
    response = requests.post(getAuthTokenUrl, data=appToken, headers=json_headers)
    response_json = response.json()
    authToken = response_json['authentication']['data']['children'][0]['value']
    return(authToken)

authToken = get_authToken()
#authToken = "19159f7c-9082-4fa5-8393-f2d4d958aeee"

xml_headers = {'Content-Type':'application/vnd.uub.record+xml', 'Accept':'application/vnd.uub.record+xml', 'authToken':authToken}
xml_validateHeaders = {'Content-Type':'application/vnd.uub.workorder+xml', 'Accept':'application/vnd.uub.record+xml','authToken':authToken}

# basic url for record
basic_urls = {
    "preview": 'https://cora.epc.ub.uu.se/diva/rest/record/',
    "pre": 'https://pre.diva-portal.org/rest/record/',
    "dev": 'http://130.238.171.238:38082/diva/rest/record/',
}

# record id och URL endpoints
RECORDID_ENDPOINT = {
    "output": "diva-output",
    "publisher": "diva-publisher",
    "journal": "diva-journal",
    "funder": "diva-funder",
    "publisher": "diva-publisher",
    "person": "diva-person",
    "series": "diva-series",
    "subject": "diva-subject",
    "course": "diva-course",
    "project": "diva-project",
    "programme": "diva-programme",
    "topOrganisation": "diva-topOrganisation",
    "partOfOrganisation": "diva-partOfOrganisation",
    "localGenericMarkup": "diva-localGenericMarkup",
}

# create recordInfo-part
def recordInfo(id, root, record_type):
    recordInfo = ET.SubElement(root, "recordInfo")
    excluded_types = ["output", "publisher", "funder", "subject", "series", "topOrganisation", "partOfOrganisation"]
    if record_type not in excluded_types:
        ET.SubElement(recordInfo, "id").text = id
    if record_type != "publisher" and record_type != "journal" and record_type != "funder":
        ET.SubElement(recordInfo, "recordContentSource").text = "uu"
    if record_type == "output":
        ET.SubElement(recordInfo, "genre", type = "outputType").text = "publication_report"
    validationType = ET.SubElement(recordInfo, "validationType")
    ET.SubElement(validationType, "linkedRecordType").text = "validationType"
    ET.SubElement(validationType, "linkedRecordId").text = RECORDID_ENDPOINT[record_type] #record_type
    dataDivider = ET.SubElement(recordInfo, "dataDivider")
    ET.SubElement(dataDivider, "linkedRecordType").text = "system"
    ET.SubElement(dataDivider, "linkedRecordId").text = "divaPreview" # <-- divaData för vanliga poster, divaPreview för beständiga poster på Preview!

# create output
def output(root):
    artisticWork = ET.SubElement(root, "artisticWork", type="outputType") 
    artisticWork.text = "true"  
    language = ET.SubElement(root, "language", repeatId="0")
    ET.SubElement(language, "languageTerm", authority="iso639-2b", type="code").text = "swe"
    ET.SubElement(root, "note", type="publicationStatus").text = "accepted"  
    ET.SubElement(root, "genre", type="contentType").text = "ref"
    ET.SubElement(root, "genre", type="reviewed").text = "refereed"
    ET.SubElement(root, "typeOfResource").text = "movingImage"
    titleInfo = ET.SubElement(root, "titleInfo", lang="swe")
    ET.SubElement(titleInfo, "title").text = "Huvudtitel"
    ET.SubElement(titleInfo, "subTitle").text = "Undertitel"
    titleInfo_alt = ET.SubElement(root, "titleInfo", lang="swe", repeatId="1", type="alternative")
    ET.SubElement(titleInfo_alt, "title").text = "Alternativ titel"
    ET.SubElement(titleInfo_alt, "subTitle").text = "Alternativ undertitel"
    name_personal = ET.SubElement(root, "name", repeatId="2", type="personal")
    person = ET.SubElement(name_personal, "person")
    ET.SubElement(person, "linkedRecordType").text = "diva-person"
    ET.SubElement(person, "linkedRecordId").text = "444"
    name_corporate = ET.SubElement(root, "name", repeatId="3", type="corporate")
    organisation = ET.SubElement(name_corporate, "organisation")
    ET.SubElement(organisation, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(organisation, "linkedRecordId").text = "diva-organisation:1530219071900116" 
    ET.SubElement(root, "note", type="creatorCount").text = "1"
    ET.SubElement(root, "abstract", lang="swe", repeatId="4").text = "Abstract här"
    subject = ET.SubElement(root, "subject", lang="swe", repeatId="5")
    ET.SubElement(subject, "topic").text = "nyckelord"
    ET.SubElement(root, "classification", authority="ssif", repeatId="6").text = "10102"
    subject_diva = ET.SubElement(root, "subject", authority="diva")  
    topic_diva = ET.SubElement(subject_diva, "topic", repeatId="7")  
    ET.SubElement(topic_diva, "linkedRecordType").text = "diva-subject" 
    ET.SubElement(topic_diva, "linkedRecordId").text = "diva-subject:1437069069944102" 
    subject_sdg = ET.SubElement(root, "subject", authority="sdg")
    ET.SubElement(subject_sdg, "topic", repeatId="8").text = "sdg3"
    originInfo = ET.SubElement(root, "originInfo") 
    dateIssued = ET.SubElement(originInfo, "dateIssued") 
    ET.SubElement(dateIssued, "year").text = "2023" 
    ET.SubElement(dateIssued, "month").text = "12" 
    ET.SubElement(dateIssued, "day").text = "02" 
    copyrightDate = ET.SubElement(originInfo, "copyrightDate") 
    ET.SubElement(copyrightDate, "year").text = "2021" 
    ET.SubElement(copyrightDate, "month").text = "12" 
    ET.SubElement(copyrightDate, "day").text = "01" 
    dateOther = ET.SubElement(originInfo, "dateOther", type="online") 
    ET.SubElement(dateOther, "year").text = "2023" 
    ET.SubElement(dateOther, "month").text = "12" 
    ET.SubElement(dateOther, "day").text = "03" 
    agent = ET.SubElement(originInfo, "agent") 
    publisher = ET.SubElement(agent, "publisher", repeatId="9") 
    ET.SubElement(publisher, "linkedRecordType").text = "diva-publisher" 
    ET.SubElement(publisher, "linkedRecordId").text = "diva-publisher:1437068056503025" 
    role = ET.SubElement(agent, "role") 
    ET.SubElement(role, "roleTerm").text = "pbl" 
    place = ET.SubElement(originInfo, "place", repeatId="10") 
    ET.SubElement(place, "placeTerm").text = "Uppsala" 
    ET.SubElement(originInfo, "edition").text = "2" 
    ET.SubElement(root, "note", type="external").text = "Extern anteckning om resursen (synlig publikt)" 
    location = ET.SubElement(root, "location", repeatId="11") 
    ET.SubElement(location, "url").text = "url.se" 
    ET.SubElement(location, "displayLabel").text = "En länktext" 
    ET.SubElement(root, "identifier", type="doi").text = "10.1000/182" 
    ET.SubElement(root, "identifier", repeatId="12", type="localId").text = "Valfritt lokalt ID här" 
    ET.SubElement(root, "identifier", type="archiveNumber").text = "345435" 
    ET.SubElement(root, "identifier", type="patentNumber").text = "234324" 
    ET.SubElement(root, "identifier", type="pmid").text = "10097079" 
    ET.SubElement(root, "identifier", type="wos").text = "56565675" 
    ET.SubElement(root, "identifier", type="scopus").text = "2-s2.0-12" 
    ET.SubElement(root, "identifier", type="openAlex").text = "Open Alex ID" 
    ET.SubElement(root, "identifier", type="se-libr").text = "1234ABcd" 
    ET.SubElement(root, "identifier", type="isrn").text = "4567867687" 
    ET.SubElement(root, "identifier", displayLabel="print", repeatId="13", type="isbn").text = "3880531013" 
    ET.SubElement(root, "identifier", displayLabel="print", repeatId="14", type="ismn").text = "9790060115615"
    ET.SubElement(root, "extent").text = "355 sidor"
    physicalDescription = ET.SubElement(root, "physicalDescription")
    ET.SubElement(physicalDescription, "extent").text = "350 sidor" 
    dateOther_patent = ET.SubElement(root, "dateOther", type="patent") 
    ET.SubElement(dateOther_patent, "year").text = "2022" 
    ET.SubElement(dateOther_patent, "month").text = "12" 
    ET.SubElement(dateOther_patent, "day").text = "04" 
    ET.SubElement(root, "imprint").text = "Uppsala" 
    academicSemester = ET.SubElement(root, "academicSemester") 
    ET.SubElement(academicSemester, "year").text = "2023" 
    ET.SubElement(academicSemester, "semester").text = "ht" 
    studentDegree = ET.SubElement(root, "studentDegree") 
    ET.SubElement(studentDegree, "degreeLevel").text = "M2" 
    ET.SubElement(studentDegree, "universityPoints").text = "10" 
    course = ET.SubElement(studentDegree, "course") 
    ET.SubElement(course, "linkedRecordType").text = "diva-course" 
    ET.SubElement(course, "linkedRecordId").text = "444" 
    programme = ET.SubElement(studentDegree, "programme") 
    ET.SubElement(programme, "linkedRecordType").text = "diva-programme" 
    ET.SubElement(programme, "linkedRecordId").text = "444" 
    relatedItem_conference = ET.SubElement(root, "relatedItem", type="conference") 
    titleInfo_conference = ET.SubElement(relatedItem_conference, "titleInfo", lang="swe") 
    ET.SubElement(titleInfo_conference, "title").text = "Huvudtitel för konferens" 
    ET.SubElement(titleInfo_conference, "subTitle").text = "Undertitel för konferens" 
    relatedItem_series = ET.SubElement(root, "relatedItem", repeatId="15", type="series") 
    series = ET.SubElement(relatedItem_series, "series") 
    ET.SubElement(series, "linkedRecordType").text = "diva-series" 
    ET.SubElement(series, "linkedRecordId").text = "diva-series:1437068740596935"
    relatedItem_journal = ET.SubElement(root, "relatedItem", type="journal") 
    journal = ET.SubElement(relatedItem_journal, "journal") 
    ET.SubElement(journal, "linkedRecordType").text = "diva-journal" 
    ET.SubElement(journal, "linkedRecordId").text = "444" 
    relatedItem_book = ET.SubElement(root, "relatedItem", type="book") 
    titleInfo_book = ET.SubElement(relatedItem_book, "titleInfo", lang="swe") 
    ET.SubElement(titleInfo_book, "title").text = "Huvudtitel för bok" 
    ET.SubElement(titleInfo_book, "subTitle").text = "Undertitel för bok" 
    ET.SubElement(relatedItem_book, "note", type="statementOfResponsibility").text = "Redaktör för bok" 
    originInfo_book = ET.SubElement(relatedItem_book, "originInfo") 
    dateIssued_book = ET.SubElement(originInfo_book, "dateIssued") 
    ET.SubElement(dateIssued_book, "year").text = "2021" 
    ET.SubElement(dateIssued_book, "month").text = "12" 
    ET.SubElement(dateIssued_book, "day").text = "03" 
    copyrightDate_book = ET.SubElement(originInfo_book, "copyrightDate") 
    ET.SubElement(copyrightDate_book, "year").text = "2021" 
    ET.SubElement(copyrightDate_book, "month").text = "11" 
    ET.SubElement(copyrightDate_book, "day").text = "05" 
    dateOther_book = ET.SubElement(originInfo_book, "dateOther", type="online") 
    ET.SubElement(dateOther_book, "year").text = "2021" 
    ET.SubElement(dateOther_book, "month").text = "10" 
    ET.SubElement(dateOther_book, "day").text = "04" 
    agent_book = ET.SubElement(originInfo_book, "agent") 
    publisher_book = ET.SubElement(agent_book, "publisher", repeatId="16") 
    ET.SubElement(publisher_book, "linkedRecordType").text = "diva-publisher" 
    ET.SubElement(publisher_book, "linkedRecordId").text = "diva-publisher:1437068056503025" 
    role_book = ET.SubElement(agent_book, "role") 
    ET.SubElement(role_book, "roleTerm").text = "pbl" 
    place_book = ET.SubElement(originInfo_book, "place", repeatId="17") 
    ET.SubElement(place_book, "placeTerm").text = "Uppsala" 
    ET.SubElement(originInfo_book, "edition").text = "2" 
    ET.SubElement(relatedItem_book, "identifier", displayLabel="print", repeatId="18", type="isbn").text = "3880531013" 
    part_book = ET.SubElement(relatedItem_book, "part") 
    extent_book = ET.SubElement(part_book, "extent") 
    ET.SubElement(extent_book, "start").text = "1" 
    ET.SubElement(extent_book, "end").text = "350" 
    relatedItem_series_book = ET.SubElement(relatedItem_book, "relatedItem", repeatId="19", type="series") 
    series_book = ET.SubElement(relatedItem_series_book, "series") 
    ET.SubElement(series_book, "linkedRecordType").text = "diva-series" 
    ET.SubElement(series_book, "linkedRecordId").text = "diva-series:1437068740596935" 
    relatedItem_conferencePublication = ET.SubElement(root, "relatedItem", type="conferencePublication") 
    titleInfo_conferencePublication = ET.SubElement(relatedItem_conferencePublication, "titleInfo", lang="swe") 
    ET.SubElement(titleInfo_conferencePublication, "title").text = "Huvudtitel för proceeding" 
    ET.SubElement(titleInfo_conferencePublication, "subTitle").text = "Undertitel för proceeding" 
    ET.SubElement(relatedItem_conferencePublication, "note", type="statementOfResponsibility").text = "Redaktör för proceeding" 
    originInfo_conferencePublication = ET.SubElement(relatedItem_conferencePublication, "originInfo") 
    dateIssued_conferencePublication = ET.SubElement(originInfo_conferencePublication, "dateIssued") 
    ET.SubElement(dateIssued_conferencePublication, "year").text = "2022" 
    ET.SubElement(dateIssued_conferencePublication, "month").text = "12" 
    ET.SubElement(dateIssued_conferencePublication, "day").text = "04" 
    copyrightDate_conferencePublication = ET.SubElement(originInfo_conferencePublication, "copyrightDate") 
    ET.SubElement(copyrightDate_conferencePublication, "year").text = "2022" 
    ET.SubElement(copyrightDate_conferencePublication, "month").text = "10" 
    ET.SubElement(copyrightDate_conferencePublication, "day").text = "01" 
    dateOther_conferencePublication = ET.SubElement(originInfo_conferencePublication, "dateOther", type="online") 
    ET.SubElement(dateOther_conferencePublication, "year").text = "2021" 
    ET.SubElement(dateOther_conferencePublication, "month").text = "10" 
    ET.SubElement(dateOther_conferencePublication, "day").text = "02" 
    agent_conferencePublication = ET.SubElement(originInfo_conferencePublication, "agent") 
    publisher_conferencePublication = ET.SubElement(agent_conferencePublication, "publisher", repeatId="20") 
    ET.SubElement(publisher_conferencePublication, "linkedRecordType").text = "diva-publisher" 
    ET.SubElement(publisher_conferencePublication, "linkedRecordId").text = "diva-publisher:1437068056503025" 
    role_conferencePublication = ET.SubElement(agent_conferencePublication, "role") 
    ET.SubElement(role_conferencePublication, "roleTerm").text = "pbl" 
    place_conferencePublication = ET.SubElement(originInfo_conferencePublication, "place", repeatId="21") 
    ET.SubElement(place_conferencePublication, "placeTerm").text = "Uppsala" 
    ET.SubElement(originInfo_conferencePublication, "edition").text = "3" 
    ET.SubElement(relatedItem_conferencePublication, "identifier", displayLabel="online", repeatId="22", type="isbn").text = "3880531015" 
    part_conferencePublication = ET.SubElement(relatedItem_conferencePublication, "part") 
    extent_conferencePublication = ET.SubElement(part_conferencePublication, "extent") 
    ET.SubElement(extent_conferencePublication, "start").text = "1" 
    ET.SubElement(extent_conferencePublication, "end").text = "350"
    relatedItem_series_conferencePublication = ET.SubElement(relatedItem_conferencePublication, "relatedItem", repeatId="23", type="series") 
    series_conferencePublication = ET.SubElement(relatedItem_series_conferencePublication, "series") 
    ET.SubElement(series_conferencePublication, "linkedRecordType").text = "diva-series" 
    ET.SubElement(series_conferencePublication, "linkedRecordId").text = "diva-series:1437068740596935" 
    relatedItem_funder = ET.SubElement(root, "relatedItem", repeatId="24", type="funder") 
    funder = ET.SubElement(relatedItem_funder, "funder") 
    ET.SubElement(funder, "linkedRecordType").text = "diva-funder" 
    ET.SubElement(funder, "linkedRecordId").text = "diva-funder:1437067710216461" 
    relatedItem_initiative = ET.SubElement(root, "relatedItem", type="initiative") 
    ET.SubElement(relatedItem_initiative, "initiative", repeatId="25").text = "diabetes" 
    relatedItem_project = ET.SubElement(root, "relatedItem", type="project") 
    project = ET.SubElement(relatedItem_project, "project") 
    ET.SubElement(project, "linkedRecordType").text = "diva-project" 
    ET.SubElement(project, "linkedRecordId").text = "444" 
    relatedItem_researchData = ET.SubElement(root, "relatedItem", repeatId="26", type="researchData") 
    titleInfo_researchData = ET.SubElement(relatedItem_researchData, "titleInfo", lang="swe") 
    ET.SubElement(titleInfo_researchData, "title").text = "Huvudtitel forskningsdata" 
    ET.SubElement(titleInfo_researchData, "subTitle").text = "Undertitel forskningsdata" 
    ET.SubElement(relatedItem_researchData, "identifier", type="doi").text = "10.1000/182" 
    location_researchData = ET.SubElement(relatedItem_researchData, "location", repeatId="27") 
    ET.SubElement(location_researchData, "url").text = "url.se" 
    ET.SubElement(location_researchData, "displayLabel").text = "En länktext"
    related = ET.SubElement(root, "related", repeatId="28", type="constituent")
    output = ET.SubElement(related, "output", repeatId="29")
    ET.SubElement(output, "linkedRecordType").text = "diva-output"
    ET.SubElement(output, "linkedRecordId").text = "diva-output:1523950164148129"
    degree_granting_institution = ET.SubElement(root, "degreeGrantingInstitution", type="corporate")
    organisation = ET.SubElement(degree_granting_institution, "organisation")
    ET.SubElement(organisation, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(organisation, "linkedRecordId").text = "diva-organisation:1530219071900116"
    role = ET.SubElement(degree_granting_institution, "role")
    ET.SubElement(role, "roleTerm").text = "dgg"
    relatedItem_defence = ET.SubElement(root, "relatedItem", type="defence") 
    dateOther_defence = ET.SubElement(relatedItem_defence, "dateOther", type="defence") 
    ET.SubElement(dateOther_defence, "year").text = "1988" 
    ET.SubElement(dateOther_defence, "month").text = "11" 
    ET.SubElement(dateOther_defence, "day").text = "01" 
    ET.SubElement(dateOther_defence, "hh").text = "10" 
    ET.SubElement(dateOther_defence, "mm").text = "30" 
    ET.SubElement(relatedItem_defence, "location").text = "En plats för disputationen" 
    ET.SubElement(relatedItem_defence, "address").text = "Doktorsgatan 5" 
    place_defence = ET.SubElement(relatedItem_defence, "place") 
    ET.SubElement(place_defence, "placeTerm").text = "Uppsala" 
    language_defence = ET.SubElement(relatedItem_defence, "language") 
    ET.SubElement(language_defence, "languageTerm", authority="iso639-2b", type="code").text = "swe" 
    ET.SubElement(root, "accessCondition", authority="kb.se").text = "gratis" 
    localGenericMarkup = ET.SubElement(root, "localGenericMarkup", repeatId="30") 
    ET.SubElement(localGenericMarkup, "linkedRecordType").text = "diva-localGenericMarkup" 
    ET.SubElement(localGenericMarkup, "linkedRecordId").text = "444" 
    admin = ET.SubElement(root, "admin") 
    ET.SubElement(admin, "reviewed").text = "true" 
    adminInfo = ET.SubElement(root, "adminInfo") 
    ET.SubElement(adminInfo, "visibility").text = "published" 
    location_orderLink = ET.SubElement(root, "location", displayLabel="orderLink") 
    ET.SubElement(location_orderLink, "url").text = "url.se" 
    ET.SubElement(location_orderLink, "displayLabel").text = "En länktext" 

# create publisher
def publisher(root):
    name = ET.SubElement(root, "name", type="corporate")
    ET.SubElement(name, "namePart").text = "Förlagets namn"

# create journal
def journal(root):
    titleInfo = ET.SubElement(root, "titleInfo")
    ET.SubElement(titleInfo, "title").text = "Huvudtitel"
    ET.SubElement(titleInfo, "subTitle").text = "Undertitel"
    ET.SubElement(root, "identifier", displayLabel = "eissn", repeatId = "0", type = "issn").text = "1234-1234"
    ET.SubElement(root, "identifier", displayLabel = "pissn", repeatId = "1", type = "issn").text = "5678-5678"
    location = ET.SubElement(root, "location")
    ET.SubElement(location, "url").text = "url.se"
    ET.SubElement(location, "displayLabel").text = "En länktext"
    originInfo = ET.SubElement(root, "originInfo")
    dateIssued = ET.SubElement(originInfo, "dateIssued", point="start")
    ET.SubElement(dateIssued, "year").text = "2002"
    ET.SubElement(dateIssued, "month").text = "05"
    ET.SubElement(dateIssued, "day").text = "01"  
    dateIssued = ET.SubElement(originInfo, "dateIssued", point="end")
    ET.SubElement(dateIssued, "year").text = "2024"
    ET.SubElement(dateIssued, "month").text = "10"
    ET.SubElement(dateIssued, "day").text = "31" 

# create funder
def funder(root):
    authority = ET.SubElement(root, "authority", lang = "swe")
    name = ET.SubElement(authority, "name", type = "corporate")
    ET.SubElement(name, "namePart").text = "Vetenskapsrådet"
    variant = ET.SubElement(root, "variant", lang = "eng")
    name = ET.SubElement(variant, "name", type = "corporate")
    ET.SubElement(name, "namePart").text = "Swedish Research Council"
    organisationInfo = ET.SubElement(root, "organisationInfo")
    startDate = ET.SubElement(organisationInfo, "startDate")
    ET.SubElement(startDate, "year").text = "2002"
    ET.SubElement(startDate, "month").text = "05"
    ET.SubElement(startDate, "day").text = "01"  
    endDate = ET.SubElement(organisationInfo, "endDate")
    ET.SubElement(endDate, "year").text = "2024"
    ET.SubElement(endDate, "month").text = "10"
    ET.SubElement(endDate, "day").text = "31"
    ET.SubElement(root, "identifier", type = "organisationNumber").text = "34534534345345-9"
    ET.SubElement(root, "identifier", type = "doi").text = "10.1109/5.771073"
    ET.SubElement(root, "identifier", type = "ror").text = "048a87296"
    
# create person
def person(root):
    authority = ET.SubElement(root, "authority")
    name = ET.SubElement(authority, "name", type = "personal")
    ET.SubElement(name, "namePart", type = "given").text = "Anders"
    ET.SubElement(name, "namePart", type = "family").text = "Andersson (och posten har en länk)"
    ET.SubElement(name, "namePart", type = "termsOfAddress").text = "Jubeldoktor"
    variant = ET.SubElement(root, "variant")
    name = ET.SubElement(variant, "name", repeatId = "0", type = "personal")
    ET.SubElement(name, "namePart", type = "given").text = "Alternativt förnamn"
    ET.SubElement(name, "namePart", type = "family").text = "Alternativt efternamn"
    personInfo = ET.SubElement(root, "personInfo")
    birthDate = ET.SubElement(personInfo, "birthDate")
    ET.SubElement(birthDate, "year").text = "1912"
    ET.SubElement(birthDate, "month").text = "08"
    ET.SubElement(birthDate, "day").text = "30"  
    deathDate = ET.SubElement(personInfo, "deathDate")
    ET.SubElement(deathDate, "year").text = "1912"
    ET.SubElement(deathDate, "month").text = "08"
    ET.SubElement(deathDate, "day").text = "30" 
    ET.SubElement(root, "email", repeatId = "6").text = "epost@mail.com"
    ET.SubElement(root, "note", lang = "swe", repeatId = "6", type = "biographical").text = "Detta var en fantastisk person."
    location = ET.SubElement(root, "location", repeatId = "7")
    ET.SubElement(location, "url").text = "url.se"
    ET.SubElement(location, "displayLabel").text = "En länktext till urlen"
    ET.SubElement(root, "identifier", repeatId = "3", type = "orcid").text = "0000-0001-5109-3700"
    ET.SubElement(root, "identifier", repeatId = "4", type = "localId").text = "Valfritt lokalt ID här"
    ET.SubElement(root, "identifier", repeatId = "6", type = "se-libr").text = "10432900"
    ET.SubElement(root, "identifier", repeatId = "7", type = "viaf").text = "12349429" 
    affiliation = ET.SubElement(root, "affiliation", repeatId = "8")
    organisation = ET.SubElement(affiliation, "organisation")
    ET.SubElement(organisation, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(organisation, "linkedRecordId").text = "diva-organisation:1530219071900116"
    startDate = ET.SubElement(affiliation, "startDate")
    ET.SubElement(startDate, "year").text = "2022"     
    ET.SubElement(startDate, "month").text = "12"
    ET.SubElement(startDate, "day").text = "03"
    endDate= ET.SubElement(affiliation, "endDate")
    ET.SubElement(endDate, "year").text = "2023"  
    ET.SubElement(endDate, "month").text = "11"
    ET.SubElement(endDate, "day").text = "04"

# create specific part for series
def series(root):
    titleInfo = ET.SubElement(root, "titleInfo")
    ET.SubElement(titleInfo, "title").text = "Huvudtitel (och posten har länkar)"
    ET.SubElement(titleInfo, "subTitle").text = "Undertitel"
    ET.SubElement(root, "identifier", displayLabel="pissn", repeatId="3", type="issn").text = "4567-9999"
    originInfo = ET.SubElement(root, "originInfo")
    dateIssued_start = ET.SubElement(originInfo, "dateIssued", point="start")
    ET.SubElement(dateIssued_start, "year").text = "2002"
    ET.SubElement(dateIssued_start, "month").text = "05"
    ET.SubElement(dateIssued_start, "day").text = "01"  
    dateIssued_end = ET.SubElement(originInfo, "dateIssued", point="end")
    ET.SubElement(dateIssued_end, "year").text = "2024"
    ET.SubElement(dateIssued_end, "month").text = "10"
    ET.SubElement(dateIssued_end, "day").text = "31"
    location = ET.SubElement(root, "location")
    ET.SubElement(location, "url").text = "enurl.se"
    ET.SubElement(location, "displayLabel").text = "En länktext"
    ET.SubElement(root, "note", type="external" ).text = "En extern anteckning (synlig publikt)"
    ET.SubElement(root, "genre", repeatId = "1", type = "outputType").text = "publication_report"
    organisation = ET.SubElement(root, "organisation")
    ET.SubElement(organisation, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(organisation, "linkedRecordId").text = "diva-organisation:1530219071900116"
    titleInfo_alt = ET.SubElement(root, "titleInfo", type="alternative")
    ET.SubElement(titleInfo_alt, "title").text = "Alternativ titel"
    ET.SubElement(titleInfo_alt, "subTitle").text = "Alternativ undertitel"
    ET.SubElement(root, "identifier", displayLabel="eissn", repeatId="0", type="issn").text = "1234-5678"
    related = ET.SubElement(root, "related", repeatId="2", type="preceding")
    series = ET.SubElement(related, "series")
    ET.SubElement(series, "linkedRecordType").text = "diva-series"
    ET.SubElement(series, "linkedRecordId").text = "diva-series:1437068740596935"
   
# create subject
def subject(root):
    authority = ET.SubElement(root, "authority", lang = "swe")
    topic = ET.SubElement(authority, "topic").text =  "Biblioteks- och informationsvetenskap (och posten har en länk)"
    variant = ET.SubElement(root, "variant", lang = "eng")
    topic = ET.SubElement(variant, "topic").text =  "Alternativt namn (engelska)"
    startDate = ET.SubElement(root, "startDate")
    ET.SubElement(startDate, "year").text = "2024"
    ET.SubElement(startDate, "month").text = "08"
    ET.SubElement(startDate, "day").text = "08"  
    endDate = ET.SubElement(root, "endDate")
    ET.SubElement(endDate, "year").text = "2024"
    ET.SubElement(endDate, "month").text = "08"
    ET.SubElement(endDate, "day").text = "08"
    ET.SubElement(root, "identifier", type = "localId").text = "Valfritt lokalt ID här"
    related = ET.SubElement(root, "related", repeatId = "0", type = "earlier")
    topic = ET.SubElement(related, "topic")
    ET.SubElement(topic, "linkedRecordType").text = "diva-subject"
    ET.SubElement(topic, "linkedRecordId").text = "diva-subject:1437069069944102"

# create course
def course(root):
    authority = ET.SubElement(root, "authority", lang = "swe")
    ET.SubElement(authority, "topic").text =  "Egyptologi (och posten har en länk)"
    variant = ET.SubElement(root, "variant", lang = "eng")
    ET.SubElement(variant, "topic").text =  "Alternativt namn (engelska)"
    startDate = ET.SubElement(root, "startDate")
    ET.SubElement(startDate, "year").text = "2023"
    ET.SubElement(startDate, "month").text = "12"
    ET.SubElement(startDate, "day").text = "08"  
    endDate = ET.SubElement(root, "endDate")
    ET.SubElement(endDate, "year").text = "2024"
    ET.SubElement(endDate, "month").text = "11"
    ET.SubElement(endDate, "day").text = "02"
    ET.SubElement(root, "identifier", type = "localId").text = "Valfritt lokalt ID här"
    related = ET.SubElement(root, "related", repeatId = "0", type = "earlier")
    course = ET.SubElement(related, "course")
    ET.SubElement(course, "linkedRecordType").text = "diva-course"
    ET.SubElement(course, "linkedRecordId").text = "444"

# create project
def project(root):
    titleInfo = ET.SubElement(root, "titleInfo", lang="swe")
    ET.SubElement(titleInfo, "title").text = "Huvudtitel här (och posten har länkar)"
    ET.SubElement(titleInfo, "subTitle").text = "Undertitel här"
    name = ET.SubElement(root, "name", repeatId="0", type="personal")
    role = ET.SubElement(name, "role")
    ET.SubElement(role, "roleTerm").text = "principalInvestigator"
    affiliation = ET.SubElement(name, "affiliation", repeatId="0")
    organisation = ET.SubElement(affiliation, "organisation")
    ET.SubElement(organisation, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(organisation, "linkedRecordId").text = "diva-organisation:1530219071900116"
    person = ET.SubElement(name, "person")
    ET.SubElement(person, "linkedRecordType").text = "diva-person"
    ET.SubElement(person, "linkedRecordId").text = "444"
    ET.SubElement(root, "identifier", type="project").text = "Projekt-ID här"
    name = ET.SubElement(root, "name", type="corporate")
    ET.SubElement(name, "namePart").text = "Organisationens namn"
    role = ET.SubElement(name, "role")
    ET.SubElement(role, "roleTerm").text = "pdr"
    organisation = ET.SubElement(name, "organisation")
    ET.SubElement(organisation, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(organisation, "linkedRecordId").text = "diva-organisation:1530219071900116"
    ET.SubElement(name, "identifier", type="ror").text = "048a87296"
    ET.SubElement(root, "abstract", lang="swe", repeatId="1").text = "Abstract-text ska stå här"
    subject = ET.SubElement(root, "subject", lang="swe", repeatId="2")
    ET.SubElement(subject, "topic").text = "nyckelord"
    subject = ET.SubElement(root, "subject", authority="diva")
    topic = ET.SubElement(subject, "topic", repeatId="0")
    ET.SubElement(topic, "linkedRecordType").text = "diva-subject"
    ET.SubElement(topic, "linkedRecordId").text = "diva-subject:1437069069944102"
    ET.SubElement(root, "classification", authority="ssif", repeatId="3").text = "10205"
    subject = ET.SubElement(root, "subject", authority="sdg")
    ET.SubElement(subject, "topic", repeatId="0").text = "sdg16"
    location = ET.SubElement(root, "location", repeatId="4")
    ET.SubElement(location, "url").text = "www.dn.se"
    ET.SubElement(location, "displayLabel").text = "Länktext ska stå här"
    ET.SubElement(root, "identifier", type="localId").text = "Valfritt lokalt ID här" 
    ET.SubElement(root, "identifier", type="raid").text = "RAID här"
    ET.SubElement(root, "identifier", type="reference").text = "EU referens-ID här"
    ET.SubElement(root, "note", type="external").text = "En anteckning här som syns publikt"
    startDate = ET.SubElement(root, "startDate")
    ET.SubElement(startDate, "year").text = "2022"
    ET.SubElement(startDate, "month").text = "12"
    ET.SubElement(startDate, "day").text = "21"
    endDate = ET.SubElement(root, "endDate")
    ET.SubElement(endDate, "year").text = "2024"
    ET.SubElement(endDate, "month").text = "11"
    ET.SubElement(endDate, "day").text = "12"
    relatedItem = ET.SubElement(root, "relatedItem", repeatId ="5", type ="funder")
    funder = ET.SubElement(relatedItem, "funder")
    ET.SubElement(funder, "linkedRecordType").text = "diva-funder"
    ET.SubElement(funder, "linkedRecordId").text = "diva-funder:1437067710216461"
    ET.SubElement(root, "fundingAmount", currency="sek").text = "45670"
    relatedItem = ET.SubElement(root, "relatedItem", repeatId="6", type="output")
    output = ET.SubElement(relatedItem, "output")
    ET.SubElement(output, "linkedRecordType").text = "diva-output"
    ET.SubElement(output, "linkedRecordId").text = "diva-output:1523950164148129"
    titleInfo = ET.SubElement(root, "titleInfo", lang="swe", type="alternative")
    ET.SubElement(titleInfo, "title").text = "Alternativ titel här"
    ET.SubElement(titleInfo, "subTitle").text = "Alternativ undertitel här"
    ET.SubElement(root, "typeOfAward").text = "projectGrant"
    admin = ET.SubElement(root, "admin")
    ET.SubElement(admin, "reviewed").text = "true"

# create programme
def programme(root):
    authority = ET.SubElement(root, "authority", lang = "swe")
    ET.SubElement(authority, "topic").text =  "Kandidatprogram musiker (och posten har en länk)"
    variant = ET.SubElement(root, "variant", lang = "eng")
    ET.SubElement(variant, "topic").text =  "Alternativt namn (engelska)"
    startDate = ET.SubElement(root, "startDate")
    ET.SubElement(startDate, "year").text = "2024"
    ET.SubElement(startDate, "month").text = "08"
    ET.SubElement(startDate, "day").text = "30"  
    endDate = ET.SubElement(root, "endDate")
    ET.SubElement(endDate, "year").text = "2025"
    ET.SubElement(endDate, "month").text = "01"
    ET.SubElement(endDate, "day").text = "28"
    ET.SubElement(root, "identifier", type = "localId").text = "Valfritt lokalt ID här"
    related = ET.SubElement(root, "related", repeatId = "0", type = "earlier")
    programme = ET.SubElement(related, "programme")
    ET.SubElement(programme, "linkedRecordType").text = "diva-programme"
    ET.SubElement(programme, "linkedRecordId").text = "123"

# create topOrganisation
def topOrganisation(root):
    authority = ET.SubElement(root, "authority", lang="swe")
    name = ET.SubElement(authority, "name", type="corporate")
    namePart = ET.SubElement(name, "namePart")
    namePart.text = "Organisationens namn (detta är en topOrganisation) (och har en länk)"
    variant = ET.SubElement(root, "variant", lang="eng")
    nameVariant = ET.SubElement(variant, "name", type="corporate")
    namePartVariant = ET.SubElement(nameVariant, "namePart")
    namePartVariant.text = "Engelskt namn för organisationen"
    organisationInfo = ET.SubElement(root, "organisationInfo")
    startDate = ET.SubElement(organisationInfo, "startDate")
    ET.SubElement(startDate, "year").text = "2022"
    ET.SubElement(startDate, "month").text = "12"
    ET.SubElement(startDate, "day").text = "23"
    endDate = ET.SubElement(organisationInfo, "endDate")
    ET.SubElement(endDate, "year").text = "2024"
    ET.SubElement(endDate, "month").text = "11"
    ET.SubElement(endDate, "day").text = "28"
    address = ET.SubElement(root, "address")
    ET.SubElement(address, "postOfficeBox").text = "46"
    ET.SubElement(address, "street").text = "Testgatan 8"
    ET.SubElement(address, "postcode").text = "76134"
    ET.SubElement(address, "place").text = "Norrköping"
    ET.SubElement(address, "country").text = "at"
    ET.SubElement(root, "identifier", type="organisationCode").text = "Valfritt lokalt ID här"
    ET.SubElement(root, "identifier", type="organisationNumber").text = "212000-3005"
    ET.SubElement(root, "identifier", type="ror").text = "048a87296"
    location = ET.SubElement(root, "location")
    ET.SubElement(location, "url").text = "url.se"
    ET.SubElement(location, "displayLabel").text = "Länktext för URL"
    ET.SubElement(root, "note", type="internal").text = "En intern anteckning här (visas ej publikt)."
    related = ET.SubElement(root, "related", type="earlier")
    relatedOrg = ET.SubElement(related, "organisation")
    ET.SubElement(relatedOrg, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(relatedOrg, "linkedRecordId").text = "diva-organisation:1530219071900116"

# create partOfOrganisation
def partOfOrganisation(root):
    authority = ET.SubElement(root, "authority", lang="swe")
    name = ET.SubElement(authority, "name", type="corporate")
    ET.SubElement(name, "namePart").text = "Organisationens namn (detta är en PartOfOrganisation) (och har två länkar)"
    variant = ET.SubElement(root, "variant", lang="eng")
    name = ET.SubElement(variant, "name", type="corporate")
    ET.SubElement(name, "namePart").text = "Alternativt namn"
    organisationInfo = ET.SubElement(root, "organisationInfo")
    startDate = ET.SubElement(organisationInfo, "startDate")
    ET.SubElement(startDate, "year").text = "2222"
    ET.SubElement(startDate, "month").text = "12"
    ET.SubElement(startDate, "day").text = "12"
    endDate = ET.SubElement(organisationInfo, "endDate")
    ET.SubElement(endDate, "year").text = "2222"
    ET.SubElement(endDate, "month").text = "12"
    ET.SubElement(endDate, "day").text = "12"
    ET.SubElement(root, "identifier", type="organisationCode").text = "Valfritt lokalt ID här"
    ET.SubElement(root, "identifier", type="organisationNumber").text = "212000-3005"
    address = ET.SubElement(root, "address")
    ET.SubElement(address, "postOfficeBox").text = "235"
    ET.SubElement(address, "street").text = "Testgatan 5"
    ET.SubElement(address, "postcode").text = "12345"
    ET.SubElement(address, "place").text = "Köping"
    ET.SubElement(address, "country").text = "sw"
    location = ET.SubElement(root, "location")
    ET.SubElement(location, "url").text = "url.se"
    ET.SubElement(location, "displayLabel").text = "En länktext"
    ET.SubElement(root, "note", type="internal").text = "En intern anteckning (visas ej publikt)."
    related_parent = ET.SubElement(root, "related", type="parent")
    organisation_parent = ET.SubElement(related_parent, "organisation")
    ET.SubElement(organisation_parent, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(organisation_parent, "linkedRecordId").text = "diva-organisation:1530219071900116"
    related_earlier = ET.SubElement(root, "related", type="earlier", repeatId="0")
    organisation_earlier = ET.SubElement(related_earlier, "organisation")
    ET.SubElement(organisation_earlier, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(organisation_earlier, "linkedRecordId").text = "diva-organisation:1530301461607844"

def localGenericMarkup(root):
    ET.SubElement(root, "localGenericMarkup").text = "En lokal uppmärkning"
    ET.SubElement(root, "description").text = "En beskrivning när det behövs."

# create the validationrecord
def validate_build(record_type):
    workOrder = ET.Element('workOrder')
    order = ET.Element('order')
    validationOrder = ET.SubElement(order, 'validationOrder')
    recordInfo = ET.SubElement(validationOrder, 'recordInfo')
    dataDivider = ET.SubElement(recordInfo, "dataDivider")
    ET.SubElement(dataDivider, "linkedRecordType").text = "system"
    ET.SubElement(dataDivider, "linkedRecordId").text = "diva"
    validationType = ET.SubElement(recordInfo, 'validationType')
    ET.SubElement(validationType, "linkedRecordType").text = "validationType"
    ET.SubElement(validationType, "linkedRecordId").text = "validationOrder"
    recordType = ET.SubElement(validationOrder, "recordType")
    ET.SubElement(recordType, "linkedRecordType").text = "recordType"
    if record_type in ["topOrganisation", "partOfOrganisation"]:
        ET.SubElement(recordType, "linkedRecordId").text = "diva-organisation"
    else: 
        ET.SubElement(recordType, "linkedRecordId").text = RECORDID_ENDPOINT[record_type] # <-- ändras beroende på posttyp 
    ET.SubElement(validationOrder, "validateLinks").text = validateLinks # <-- true eller false
    ET.SubElement(validationOrder, "metadataToValidate").text = metadataToValidate # <-- new eller existing (action - create, update) [samt check för unique!]
    workOrder.append(order)
    return workOrder

# create the record and post
def create(root, record_type):
    output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"+ET.tostring(root).decode("UTF-8")
    if record_type in ["topOrganisation", "partOfOrganisation"]:
        response = requests.post(f"{basic_urls[url]}{"diva-organisation"}", data=output, headers=xml_headers)
    else:
        response = requests.post(f"{basic_urls[url]}{RECORDID_ENDPOINT[record_type]}", data=output, headers=xml_headers)
    print (response.status_code, response.text)
    print(output) # <-- visar i konsollen vad man skickar in vid en create
    #print(f"{basic_urls[url]}{RECORDID_ENDPOINT[record_type]}") #record_type
    #print(xml_headers)

# list of functions, one for each recordtype and one for all
function_map = {
    "output": output, 
    "journal": journal,
    "funder": funder,
    "publisher": publisher,
    "person": person,
    "series": series,
    "subject": subject,
    "course": course,
    "project": project,
    "programme": programme,
    "topOrganisation": topOrganisation,
    "partOfOrganisation": partOfOrganisation,
    "localGenericMarkup": localGenericMarkup,
    "all": None
}

# validate chosen record
def validateRecord():
    # all (can take all)
    if isinstance(recordId, list) and 'all' in recordId:
        for record_type, function in function_map.items():
            if function is not None:
                if record_type in ["topOrganisation", "partOfOrganisation"]:
                    root = ET.Element("organisation")
                else:
                    root = ET.Element(record_type) # skapar ett root-element för xml:en
                recordInfo(id, root, record_type) # funktion som skapar recordInfo-delen
                function(root)
                workOrder = validate_build(record_type) # funktion som skapar validerings-delen
                ET.SubElement(workOrder, 'record').append(root) # lägger till root i workorder
                validate_post(workOrder)
    # list (can only take one)
    elif isinstance(recordId, list):
        for record_type in recordId:
            if record_type in function_map and function_map[record_type] is not None:
                if record_type in ["topOrganisation", "partOfOrganisation"]:
                    root = ET.Element("organisation")
                else:
                    root = ET.Element(record_type) # skapar ett root-element för xml:en
                recordInfo(id, root, record_type) # funktion som skapar recordInfo-delen
                function_map[record_type](root)
                workOrder = validate_build(record_type) # return från validate
                ET.SubElement(workOrder, 'record').append(root)
                validate_post(workOrder)
            else:
                print(f"Function for '{recordId}' not found")

def validate_post(workOrder):
    output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"+ET.tostring(workOrder).decode("UTF-8")
    url = "https://cora.epc.ub.uu.se/diva/rest/record/workOrder"
    response = requests.post(url, data=output, headers=xml_validateHeaders)
    print(response.status_code, response.text)
    print(output)

# create chosen record
def createRecord():
    # all (can take all)
    if isinstance(recordId, list) and 'all' in recordId:
        for record_type, function in function_map.items():
            if function is not None:
                if record_type in ["topOrganisation", "partOfOrganisation"]:
                    root = ET.Element("organisation")
                else:
                    root = ET.Element(record_type) # skapar ett root-element för xml:en
                recordInfo(id, root, record_type) # funktion som skapar recordInfo-delen
                function(root) # loopar igenom funktionerna för specik recordtype
                create(root, record_type) # creates record and posts
    # list (can only take one)
    elif isinstance(recordId, list):
        for record_type in recordId:
            if record_type in function_map and function_map[record_type] is not None:
                if record_type in ["topOrganisation", "partOfOrganisation"]:
                    root = ET.Element("organisation")
                else:
                    root = ET.Element(record_type) # skapar ett root-element för xml:en
                recordInfo(id, root, record_type) # funktion som skapar recordInfo-delen
                function_map[record_type](root) #recordId
                create(root, record_type) # eller recordId? # skickar in själva posten
            else:
                print(f"Function for '{record_type}' not found")

# choose for validate...
validateLinks = 'true' # <--'true' or 'false'
metadataToValidate = 'new' # <-- 'new' or 'existing'
# choose values to create with...
recordId = ['partOfOrganisation'] # <-- ändra posttyp, välj vilken som skapas or 'all'
id = '444' # <-- ändra postens id-nummer
url = 'dev' # <-- ändra miljö, URL [preview, pre, dev]

def start():
    #validateRecord()
    createRecord()

start()