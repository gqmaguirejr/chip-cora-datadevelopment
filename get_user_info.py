#!/usr/bin/python3
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

#system = 'preview'
# system = 'local'
system = 'pre'
recordType = 'diva-journal'
nameInData = 'journal'
WORKERS = 8
filePath_validateBase = (r"validationOrder_base.xml")
# filePath_sourceXml = (r"db_xml\db_diva-"+nameInData+".xml")
filePath_sourceXml = (r"db_xml/journal_from_db.xml")

request_counter = 0
app_token_client = None
data_logger = None

from atexit import register

# Note that you cannot cancel the MainThread
def all_done():
    global Verbose_Flag
    for thr in threading._enumerate():
        if Verbose_Flag:
            print(f"{thr.name=}")
        if thr.name != 'MainThread':
            if thr.is_alive():
                thr.cancel()
                thr.join()

register(all_done)


def read_source_xml(sourceXml):
    return  ET.ElementTree(ET.fromstring(sourceXml))



def get_user():

    global Verbose_Flag
    global app_token_client
    global data_logger
    
    page_response=''

    auth_token = app_token_client.get_auth_token()
    headers = {'Content-Type': 'application/vnd.uub.recordList+xml',
               'Accept':'*/*',
               'authToken':auth_token,
               'accept-encoding': 'gzip, deflate, br, zstd',
               'accept-language': 'en-US,en;q=0.9'
               }
    url = ConstantsData.BASE_URL[system] + 'user'
    if Verbose_Flag:
        print(f"{url=}")

    response = requests.get(url, headers=headers)

    print(f"{response.status_code=}")
    if response.status_code == requests.codes.ok:
        if Verbose_Flag:
            print(f"{response.text=}")
            #print(f"{r.headers=}")
        page_response=response.text
        #page_response=json.loads(response.text)
    else:
        if Verbose_Flag:
            print(f"{response.status_code=} {response.text=}")
    return page_response



def start():
    global data_logger
    global Verbose_Flag
    Verbose_Flag=True

#    login_logger = RunRotatingLogger('login', 'logs/apptokenlog.txt').get()
#    login_logger.info(f"_handle_login_response:{response}")
    
    data_logger = RunRotatingLogger('data', 'logs/data_processing.txt').get()
    data_logger.info("Data processing started")
    
    
    starttime = time.time()
    start_app_token_client()
    
    # for testing by GQMJr
    print("made it to start()")
    auth_token = app_token_client.get_auth_token()
    print(f"{auth_token}")
    Verbose_Flag=False
    user_info_xml=get_user()
    print(f"{len(user_info_xml)=}")
    tree=read_source_xml(user_info_xml)
    root = tree.getroot()
    print(f"top level tag: {root.tag} {root=}")
    #for child in root:
    #    print(child.tag, child.attrib)
    top_level_view=[elem.tag for elem in root.iter()]
    if Verbose_Flag:
        print(f"{top_level_view=}")

    Verbose_Flag=True
    fromNo=root.find('./fromNo').text
    toNo=root.find('./toNo').text
    totalNo=root.find('./totalNo').text
    print(f"{fromNo=} {toNo=} {totalNo=}")

    for rec in root.findall('./data/record/data/user'):
        print(rec.attrib)
        if rec.attrib and rec.attrib['type']:
            user_type=rec.attrib['type']
            user_id=rec.find('recordInfo/id').text
            login_id=rec.find('loginId').text
            userFirstname=rec.find('userFirstname').text
            userLastname=rec.find('userLastname').text
            print(f"{user_type}\t{user_id=}\t{login_id=}\t{userFirstname=}\t{userLastname=}")

    # dataList = CommonData.read_source_xml(filePath_sourceXml)
    # list_dataRecord = []
    # for data_record in dataList.findall('.//DATA_RECORD'):
    #     list_dataRecord.append(data_record)
    
    # print(f'Number of records read: {len(list_dataRecord)}')
    
    
    print(f'Tidsåtgång: {time.time() - starttime}')

    # shutdown in an orderly maner by cancelling the timer for the authToken
    # The all_done() function will get called to kill off all the threads
    app_token_client.cancel_timer()


    
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
