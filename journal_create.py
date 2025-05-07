
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
import os
import sys
import threading
import time
sys.path.append(os.path.abspath('src'))

import requests
from common.RunRotatingLogger import RunRotatingLogger

from commondata import CommonData
from constantsdata import ConstantsData
from cora.client.AppTokenClient import AppTokenClient
from tqdm import tqdm
import xml.etree.ElementTree as ET

system = 'preview'
# system = 'local'
recordType = 'diva-journal'
nameInData = 'journal'
WORKERS = 8
filePath_validateBase = (r"validationOrder_base.xml")
# filePath_sourceXml = (r"db_xml\db_diva-"+nameInData+".xml")
filePath_sourceXml = (r"db_xml/journal_from_db.xml")

request_counter = 0
app_token_client = None
data_logger = None


def start():
    global data_logger
#    login_logger = RunRotatingLogger('login', 'logs/apptokenlog.txt').get()
#    login_logger.info(f"_handle_login_response:{response}")
    
    data_logger = RunRotatingLogger('data', 'logs/data_processing.txt').get()
    data_logger.info("Data processing started")
    
    
    starttime = time.time()
    start_app_token_client()
    
    dataList = CommonData.read_source_xml(filePath_sourceXml)
    list_dataRecord = []
    for data_record in dataList.findall('.//DATA_RECORD'):
        list_dataRecord.append(data_record)
    
    print(f'Number of records read: {len(list_dataRecord)}')
    
#    with Pool(WORKERS) as pool:
    with ThreadPool(WORKERS) as pool:
#        test = pool.map(new_record_build, list_dataRecord)
#            print(test)
#        pool.map(validate_record, list_dataRecord)
#        list(tqdm(
#            pool.imap_unordered(validate_record, list_dataRecord),
#            total=len(list_dataRecord),
#            desc="Validating records"
#        ))
        list(tqdm(
            pool.imap_unordered(create_record, list_dataRecord),
            total=len(list_dataRecord),
            desc="Created records"
        ))
        # pool.map(ServersideData.create_record, list_dataRecord)
#    global app_token_client
    
    print(f'Tidsåtgång: {time.time() - starttime}')

    
def start_app_token_client():
    global app_token_client
    dependencies = {"requests": requests,
                    "time": time,
                    "threading": threading}
    app_token_client = AppTokenClient(dependencies)

    login_spec = {"login_url": ConstantsData.LOGIN_URLS[system],
            "login_id": 'divaAdmin@cora.epc.ub.uu.se',
            "app_token": "49ce00fb-68b5-4089-a5f7-1c225d3cf156"}
    app_token_client.login(login_spec)


def new_record_build(data_record):
        newRecordElement = ET.Element(nameInData)
        CommonData.recordInfo_build(nameInData, data_record, newRecordElement)
        CommonData.titleInfo_build(data_record, newRecordElement)
        counter = 0
        counter = CommonData.identifier_build(data_record, newRecordElement, 'pissn', counter)
        counter = CommonData.identifier_build(data_record, newRecordElement, 'eissn', counter)
        CommonData.endDate_build(data_record, newRecordElement, 'originInfo')
        CommonData.location_build(data_record, newRecordElement)
        return newRecordElement


def validate_record(data_record):
    global app_token_client
    global data_logger
    
    auth_token = app_token_client.get_auth_token()
    validate_headers_xml = {'Content-Type':'application/vnd.uub.workorder+xml',
                            'Accept':'application/vnd.uub.record+xml', 'authToken':auth_token}
    validate_url = ConstantsData.BASE_URL[system] + 'workOrder'
    newRecordToCreate = new_record_build(data_record)
    oldId_fromSource = CommonData.get_oldId(data_record)
    newRecordToValidate = CommonData.validateRecord_build(nameInData, filePath_validateBase, newRecordToCreate)
    output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + ET.tostring(newRecordToValidate).decode("UTF-8")
    response = requests.post(validate_url, data=output, headers=validate_headers_xml)
#    print(response.status_code, response.text)
    if '<valid>true</valid>' not in response.text:
        with open(f'errorlog.txt', 'a', encoding='utf-8') as log:
            log.write(f"{oldId_fromSource}: {response.status_code}. {response.text}\n\n")
    if response.text:
        data_logger.info(f"{oldId_fromSource}: {response.status_code}. {response.text}")
        with open(f'log.txt', 'a', encoding='utf-8') as log:
            log.write(f"{oldId_fromSource}: {response.status_code}. {response.text}\n\n")


def create_record(data_record):
    global app_token_client
    global data_logger
    
    auth_token = app_token_client.get_auth_token()
    headersXml = {'Content-Type':'application/vnd.uub.record+xml',
                  'Accept':'application/vnd.uub.record+xml', 'authToken':auth_token}
    urlCreate = ConstantsData.BASE_URL[system] + recordType
    recordToCreate = new_record_build(data_record)
    oldId_fromSource = CommonData.get_oldId(data_record)
    output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + ET.tostring(recordToCreate).decode("UTF-8")
    response = requests.post(urlCreate, data=output, headers=headersXml)
#    print(response.status_code, response.text)
    if response.text:
        data_logger.info(f"{oldId_fromSource}: {response.status_code}. {response.text}")
    if response.status_code not in ([201]):
        data_logger.error(f"{oldId_fromSource}: {response.status_code}. {response.text}")
    return response.text


if __name__ == "__main__":
    start()
