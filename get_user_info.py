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

import json
import gzip
import pprint

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
    #global Verbose_Flag
    Verbose_Flag=False
    for thr in threading._enumerate():
        if Verbose_Flag:
            print(f"{thr.name=}")
        if thr.name != 'MainThread':
            if thr.is_alive():
                thr.cancel()
                thr.join()

register(all_done)


def giveup_token(authtoken):
    global Verbose_Flag
    global app_token_client
    #DELETE {baseUrl}/authToken/{tokenId}
    url=f"https://pre.diva-portal.org/login/rest/authToken/{authtoken}"
    if Verbose_Flag:
        print(f"{url=}")
    headers = {'Content-Type':'application/vnd.cora.login',
               'Accept': '*/*',
               'accept-encoding': 'gzip, deflate, br, zstd',
               'accept-language': 'en-US,en;q=0.9',
               'authToken': authtoken}

    response = requests.delete(url, headers=headers)
    print(f"{response.status_code=}\n{response.text=}\n{response.headers=}\n{response.request.headers=}")
    app_token_client=None
    return response

# The above delete request fails with:
# url='https://pre.diva-portal.org/login/rest/authToken/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
# response.status_code=404
# response.text='<!doctype html><html lang="en"><head><title>HTTP Status 404 – Not Found</title><style type="text/css">body {font-family:Tahoma,Arial,sans-serif;} h1, h2, h3, b {color:white;background-color:#525D76;} h1 {font-size:22px;} h2 {font-size:16px;} h3 {font-size:14px;} p {font-size:12px;} a {color:black;} .line {height:1px;background-color:#525D76;border:none;}</style></head><body><h1>HTTP Status 404 – Not Found</h1><hr class="line" /><p><b>Type</b> Status Report</p><p><b>Message</b> Not Found</p><p><b>Description</b> The origin server did not find a current representation for the target resource or is not willing to disclose that one exists.</p><hr class="line" /><h3>Apache Tomcat/11.0.2</h3></body></html>'
# response.headers={'Date': 'Thu, 08 May 2025 10:26:01 GMT', 'Server': 'Apache/2.4.63 (Unix) mod_qos/11.63', 'Content-Type': 'text/html;charset=utf-8', 'Content-Language': 'en', 'Content-Length': '713', 'Strict-Transport-Security': 'max-age=31536000', 'X-Varnish': '87953399', 'Age': '0', 'Via': '1.1 varnish (Varnish/7.1)', 'Connection': 'keep-alive'}
#response.request.headers={'User-Agent': 'python-requests/2.31.0', 'accept-encoding': 'gzip, deflate, br, zstd', 'Accept': '*/*', 'Connection': 'keep-alive', 'Content-Type': 'application/vnd.uub.login', 'accept-language': 'en-US,en;q=0.9', 'authToken': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', 'Content-Length': '0'}



def read_source_xml(sourceXml):
    return  ET.ElementTree(ET.fromstring(sourceXml))



def get_user():

    global Verbose_Flag
    global app_token_client
    global data_logger
    
    page_response=''

    auth_token = app_token_client.get_auth_token()
    headers = {'Content-Type': 'application/vnd.cora.recordList+xml',
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

def get_record_json(recordType, id):
    global Verbose_Flag
    global app_token_client
    
    page_response=''

    auth_token = app_token_client.get_auth_token()
    headers = {'Content-Type': 'application/vnd.cora.record+json',
               'Accept':'application/vnd.cora.record+json',
               'authToken':auth_token,
               'accept-encoding': 'gzip, deflate, br, zstd',
               'accept-language': 'en-US,en;q=0.9'
               }
    url = ConstantsData.BASE_URL[system] + f'{recordType}/{id}'
    if Verbose_Flag:
        print(f"{url=}")

    response = requests.get(url, headers=headers)
    if Verbose_Flag:
        print(f"{response.status_code=}")
    if response.status_code == requests.codes.ok:
        if Verbose_Flag:
            print(f"{response.text=}")
            #print(f"{r.headers=}")
        page_response=json.loads(response.text)
        #page_response=json.loads(response.text)
    else:
        if Verbose_Flag:
            print(f"{response.status_code=} {response.text=}")
    return page_response

def get_records_json(recordType):
    global Verbose_Flag
    global app_token_client
    
    page_response=[]

    auth_token = app_token_client.get_auth_token()
    headers = {'Content-Type': 'application/vnd.cora.recordList+json',
               'Accept':'application/vnd.cora.recordList+json',
               'authToken':auth_token,
               'accept-encoding': 'gzip, deflate, br, zstd',
               'accept-language': 'en-US,en;q=0.9'
               }
    url = ConstantsData.BASE_URL[system] + f'{recordType}'
    if Verbose_Flag:
        print(f"{url=}")

    response = requests.get(url, headers=headers)
    if Verbose_Flag:
        print(f"{response.status_code=}")
    if response.status_code == requests.codes.ok:
        if Verbose_Flag:
            print(f"{response.text=}")
            #print(f"{r.headers=}")
        page_response=json.loads(response.text)
        #page_response=json.loads(response.text)
    else:
        if Verbose_Flag:
            print(f"{response.status_code=} {response.text=}")
    return page_response



def searchResult_search(search_id, search_data):
    global Verbose_Flag
    global app_token_client
    global data_logger

    page_response=''

    payload={'searchData': json.dumps(search_data, separators=(',', ':'))}
    #payload={'searchData': search_data}

    auth_token = app_token_client.get_auth_token()
    headers = {'Content-Type': 'application/vnd.cora.recordList+json',
               'Accept':'application/vnd.cora.recordList+json',
               'authToken':auth_token,
               'accept-encoding': 'gzip, deflate, br, zstd',
               'accept-language': 'en-US,en;q=0.9'
               }
    url = ConstantsData.BASE_URL[system] + f'searchResult/{search_id}'
    if Verbose_Flag:
        print(f"{url=}")

    response = requests.get(url, headers=headers, params=payload)
    print(f"{response.status_code=}")
    if response.status_code == requests.codes.ok:
        if Verbose_Flag:
            print(f"{response.text=}")
            print(f"{response.headers=}")
            print(f"{response.request.headers=}")
        if response.headers.get('gzip'):
            print(f"{response.content=}")
            uncomp=gzip.decompress(response.content)
            page_response=json.loads(uncomp)
        else:
            page_response=json.loads(response.text)
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
    
    
    # for testing by GQMJr
    print("made it to start()")

    starttime = time.time()
    start_app_token_client()
    
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
    
    rr=get_record_json('diva-output', 'diva-output:15009801329005961')
    print(f"{rr=}")
    pprint.pprint(rr, width=120)

    # Returns:
    # {'record': {'actionLinks': {'delete': {'rel': 'delete',
    #                                    'requestMethod': 'DELETE',
    #                                    'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15009801329005961'},
    #                         'index': {'accept': 'application/vnd.cora.record+json',
    #                                   'body': {'children': [{'children': [{'name': 'linkedRecordType',
    #                                                                        'value': 'recordType'},
    #                                                                       {'name': 'linkedRecordId',
    #                                                                        'value': 'diva-output'}],
    #                                                          'name': 'recordType'},
    #                                                         {'name': 'recordId',
    #                                                          'value': 'diva-output:15009801329005961'},
    #                                                         {'name': 'type', 'value': 'index'}],
    #                                            'name': 'workOrder'},
    #                                   'contentType': 'application/vnd.cora.recordgroup+json',
    #                                   'rel': 'index',
    #                                   'requestMethod': 'POST',
    #                                   'url': 'https://pre.diva-portal.org/rest/record/workOrder/'},
    #                         'read': {'accept': 'application/vnd.cora.record+json',
    #                                  'rel': 'read',
    #                                  'requestMethod': 'GET',
    #                                  'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15009801329005961'},
    #                         'update': {'accept': 'application/vnd.cora.record+json',
    #                                    'contentType': 'application/vnd.cora.recordgroup+json',
    #                                    'rel': 'update',
    #                                    'requestMethod': 'POST',
    #                                    'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15009801329005961'}},
    #         'data': {'children': [{'children': [{'name': 'type', 'value': 'attachment'},
    #                                             {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                       'rel': 'read',
    #                                                                       'requestMethod': 'GET',
    #                                                                       'url': 'https://pre.diva-portal.org/rest/record/binary/binary:15009821683601401'}},
    #                                              'children': [{'name': 'linkedRecordType', 'value': 'binary'},
    #                                                           {'name': 'linkedRecordId',
    #                                                            'value': 'binary:15009821683601401'}],
    #                                              'name': 'attachmentFile'}],
    #                                'name': 'attachment',
    #                                'repeatId': '0'},
    #                               {'children': [{'name': 'reviewed', 'value': 'true'}], 'name': 'admin'},
    #                               {'attributes': {'type': 'isrn'}, 'name': 'identifier', 'value': 'KTH/BKN/R-164-SE'},
    #                               {'attributes': {'authority': 'ssif'},
    #                                'name': 'classification',
    #                                'repeatId': '0',
    #                                'value': '20199'},
    #                               {'children': [{'children': [{'name': 'year', 'value': '2017'}],
    #                                              'name': 'dateIssued'}],
    #                                'name': 'originInfo'},
    #                               {'attributes': {'type': 'personal'},
    #                                'children': [{'children': [{'name': 'roleTerm', 'repeatId': '0', 'value': 'aut'}],
    #                                              'name': 'role'},
    #                                             {'attributes': {'type': 'given'},
    #                                              'name': 'namePart',
    #                                              'value': 'Roghayeh'},
    #                                             {'attributes': {'type': 'family'},
    #                                              'name': 'namePart',
    #                                              'value': 'Abbasiverki'}],
    #                                'name': 'name',
    #                                'repeatId': '0'},
    #                               {'attributes': {'lang': 'eng'},
    #                                'children': [{'name': 'title',
    #                                              'value': 'Initial study on seismic analyses of concrete and '
    #                                                       'embankment dams in Sweden'}],
    #                                'name': 'titleInfo'},
    #                               {'attributes': {'type': 'contentType'}, 'name': 'genre', 'value': 'ref'},
    #                               {'children': [{'attributes': {'authority': 'iso639-2b', 'type': 'code'},
    #                                              'name': 'languageTerm',
    #                                              'value': 'eng'}],
    #                                'name': 'language',
    #                                'repeatId': '0'},
    #                               {'attributes': {'type': 'outputType'},
    #                                'name': 'genre',
    #                                'value': 'publication_report'},
    #                               {'children': [{'name': 'visibility', 'value': 'published'},
    #                                             {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                       'rel': 'read',
    #                                                                       'requestMethod': 'GET',
    #                                                                       'url': 'https://pre.diva-portal.org/rest/record/permissionUnit/kth'}},
    #                                              'children': [{'name': 'linkedRecordType', 'value': 'permissionUnit'},
    #                                                           {'name': 'linkedRecordId', 'value': 'kth'}],
    #                                              'name': 'permissionUnit'},
    #                                             {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                       'rel': 'read',
    #                                                                       'requestMethod': 'GET',
    #                                                                       'url': 'https://pre.diva-portal.org/rest/record/validationType/publication_report'}},
    #                                              'children': [{'name': 'linkedRecordType', 'value': 'validationType'},
    #                                                           {'name': 'linkedRecordId',
    #                                                            'value': 'publication_report'}],
    #                                              'name': 'validationType'},
    #                                             {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                       'rel': 'read',
    #                                                                       'requestMethod': 'GET',
    #                                                                       'url': 'https://pre.diva-portal.org/rest/record/system/divaData'}},
    #                                              'children': [{'name': 'linkedRecordType', 'value': 'system'},
    #                                                           {'name': 'linkedRecordId', 'value': 'divaData'}],
    #                                              'name': 'dataDivider'},
    #                                             {'name': 'tsVisibility', 'value': '2025-05-08T08:26:11.613501Z'},
    #                                             {'name': 'id', 'value': 'diva-output:15009801329005961'},
    #                                             {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                       'rel': 'read',
    #                                                                       'requestMethod': 'GET',
    #                                                                       'url': 'https://pre.diva-portal.org/rest/record/recordType/diva-output'}},
    #                                              'children': [{'name': 'linkedRecordType', 'value': 'recordType'},
    #                                                           {'name': 'linkedRecordId', 'value': 'diva-output'}],
    #                                              'name': 'type'},
    #                                             {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                       'rel': 'read',
    #                                                                       'requestMethod': 'GET',
    #                                                                       'url': 'https://pre.diva-portal.org/rest/record/user/161616'}},
    #                                              'children': [{'name': 'linkedRecordType', 'value': 'user'},
    #                                                           {'name': 'linkedRecordId', 'value': '161616'}],
    #                                              'name': 'createdBy'},
    #                                             {'name': 'tsCreated', 'value': '2025-05-08T08:26:11.619838Z'},
    #                                             {'children': [{'name': 'tsUpdated',
    #                                                            'value': '2025-05-08T08:55:54.418078Z'},
    #                                                           {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                     'rel': 'read',
    #                                                                                     'requestMethod': 'GET',
    #                                                                                     'url': 'https://pre.diva-portal.org/rest/record/user/161616'}},
    #                                                            'children': [{'name': 'linkedRecordType',
    #                                                                          'value': 'user'},
    #                                                                         {'name': 'linkedRecordId',
    #                                                                          'value': '161616'}],
    #                                                            'name': 'updatedBy'}],
    #                                              'name': 'updated',
    #                                              'repeatId': '0'}],
    #                                'name': 'recordInfo'}],
    #                  'name': 'output'}}}



    recs=get_records_json('diva-output')
    print(f"{recs=}")
    pprint.pprint(recs, width=120)

    # Returns:
    # {'dataList': {'containDataOfType': 'diva-output',
    #         'data': [{'record': {'actionLinks': {'delete': {'rel': 'delete',
    #                                                         'requestMethod': 'DELETE',
    #                                                         'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15009801329005961'},
    #                                              'index': {'accept': 'application/vnd.cora.record+json',
    #                                                        'body': {'children': [{'children': [{'name': 'linkedRecordType',
    #                                                                                             'value': 'recordType'},
    #                                                                                            {'name': 'linkedRecordId',
    #                                                                                             'value': 'diva-output'}],
    #                                                                               'name': 'recordType'},
    #                                                                              {'name': 'recordId',
    #                                                                               'value': 'diva-output:15009801329005961'},
    #                                                                              {'name': 'type', 'value': 'index'}],
    #                                                                 'name': 'workOrder'},
    #                                                        'contentType': 'application/vnd.cora.recordgroup+json',
    #                                                        'rel': 'index',
    #                                                        'requestMethod': 'POST',
    #                                                        'url': 'https://pre.diva-portal.org/rest/record/workOrder/'},
    #                                              'read': {'accept': 'application/vnd.cora.record+json',
    #                                                       'rel': 'read',
    #                                                       'requestMethod': 'GET',
    #                                                       'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15009801329005961'},
    #                                              'update': {'accept': 'application/vnd.cora.record+json',
    #                                                         'contentType': 'application/vnd.cora.recordgroup+json',
    #                                                         'rel': 'update',
    #                                                         'requestMethod': 'POST',
    #                                                         'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15009801329005961'}},
    #                              'data': {'children': [{'children': [{'name': 'type', 'value': 'attachment'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/binary/binary:15009821683601401'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'binary'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'binary:15009821683601401'}],
    #                                                                   'name': 'attachmentFile'}],
    #                                                     'name': 'attachment',
    #                                                     'repeatId': '0'},
    #                                                    {'children': [{'name': 'reviewed', 'value': 'true'}],
    #                                                     'name': 'admin'},
    #                                                    {'attributes': {'type': 'isrn'},
    #                                                     'name': 'identifier',
    #                                                     'value': 'KTH/BKN/R-164-SE'},
    #                                                    {'attributes': {'authority': 'ssif'},
    #                                                     'name': 'classification',
    #                                                     'repeatId': '0',
    #                                                     'value': '20199'},
    #                                                    {'children': [{'children': [{'name': 'year', 'value': '2017'}],
    #                                                                   'name': 'dateIssued'}],
    #                                                     'name': 'originInfo'},
    #                                                    {'attributes': {'type': 'personal'},
    #                                                     'children': [{'children': [{'name': 'roleTerm',
    #                                                                                 'repeatId': '0',
    #                                                                                 'value': 'aut'}],
    #                                                                   'name': 'role'},
    #                                                                  {'attributes': {'type': 'given'},
    #                                                                   'name': 'namePart',
    #                                                                   'value': 'Roghayeh'},
    #                                                                  {'attributes': {'type': 'family'},
    #                                                                   'name': 'namePart',
    #                                                                   'value': 'Abbasiverki'}],
    #                                                     'name': 'name',
    #                                                     'repeatId': '0'},
    #                                                    {'attributes': {'lang': 'eng'},
    #                                                     'children': [{'name': 'title',
    #                                                                   'value': 'Initial study on seismic analyses of '
    #                                                                            'concrete and embankment dams in '
    #                                                                            'Sweden'}],
    #                                                     'name': 'titleInfo'},
    #                                                    {'attributes': {'type': 'contentType'},
    #                                                     'name': 'genre',
    #                                                     'value': 'ref'},
    #                                                    {'children': [{'attributes': {'authority': 'iso639-2b',
    #                                                                                  'type': 'code'},
    #                                                                   'name': 'languageTerm',
    #                                                                   'value': 'eng'}],
    #                                                     'name': 'language',
    #                                                     'repeatId': '0'},
    #                                                    {'attributes': {'type': 'outputType'},
    #                                                     'name': 'genre',
    #                                                     'value': 'publication_report'},
    #                                                    {'children': [{'name': 'visibility', 'value': 'published'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/permissionUnit/kth'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'permissionUnit'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'kth'}],
    #                                                                   'name': 'permissionUnit'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/validationType/publication_report'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'validationType'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'publication_report'}],
    #                                                                   'name': 'validationType'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/system/divaData'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'system'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'divaData'}],
    #                                                                   'name': 'dataDivider'},
    #                                                                  {'name': 'tsVisibility',
    #                                                                   'value': '2025-05-08T08:26:11.613501Z'},
    #                                                                  {'name': 'id',
    #                                                                   'value': 'diva-output:15009801329005961'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/recordType/diva-output'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'recordType'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'diva-output'}],
    #                                                                   'name': 'type'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/user/161616'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'user'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': '161616'}],
    #                                                                   'name': 'createdBy'},
    #                                                                  {'name': 'tsCreated',
    #                                                                   'value': '2025-05-08T08:26:11.619838Z'},
    #                                                                  {'children': [{'name': 'tsUpdated',
    #                                                                                 'value': '2025-05-08T08:55:54.418078Z'},
    #                                                                                {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                                          'rel': 'read',
    #                                                                                                          'requestMethod': 'GET',
    #                                                                                                          'url': 'https://pre.diva-portal.org/rest/record/user/161616'}},
    #                                                                                 'children': [{'name': 'linkedRecordType',
    #                                                                                               'value': 'user'},
    #                                                                                              {'name': 'linkedRecordId',
    #                                                                                               'value': '161616'}],
    #                                                                                 'name': 'updatedBy'}],
    #                                                                   'name': 'updated',
    #                                                                   'repeatId': '0'}],
    #                                                     'name': 'recordInfo'}],
    #                                       'name': 'output'}}},
    #                  {'record': {'actionLinks': {'delete': {'rel': 'delete',
    #                                                         'requestMethod': 'DELETE',
    #                                                         'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15030850390969906'},
    #                                              'index': {'accept': 'application/vnd.cora.record+json',
    #                                                        'body': {'children': [{'children': [{'name': 'linkedRecordType',
    #                                                                                             'value': 'recordType'},
    #                                                                                            {'name': 'linkedRecordId',
    #                                                                                             'value': 'diva-output'}],
    #                                                                               'name': 'recordType'},
    #                                                                              {'name': 'recordId',
    #                                                                               'value': 'diva-output:15030850390969906'},
    #                                                                              {'name': 'type', 'value': 'index'}],
    #                                                                 'name': 'workOrder'},
    #                                                        'contentType': 'application/vnd.cora.recordgroup+json',
    #                                                        'rel': 'index',
    #                                                        'requestMethod': 'POST',
    #                                                        'url': 'https://pre.diva-portal.org/rest/record/workOrder/'},
    #                                              'read': {'accept': 'application/vnd.cora.record+json',
    #                                                       'rel': 'read',
    #                                                       'requestMethod': 'GET',
    #                                                       'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15030850390969906'},
    #                                              'update': {'accept': 'application/vnd.cora.record+json',
    #                                                         'contentType': 'application/vnd.cora.recordgroup+json',
    #                                                         'rel': 'update',
    #                                                         'requestMethod': 'POST',
    #                                                         'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15030850390969906'}},
    #                              'data': {'children': [{'children': [{'name': 'type', 'value': 'inside'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/binary/binary:15030875065066058'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'binary'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'binary:15030875065066058'}],
    #                                                                   'name': 'attachmentFile'}],
    #                                                     'name': 'attachment',
    #                                                     'repeatId': '0'},
    #                                                    {'children': [{'name': 'reviewed', 'value': 'true'}],
    #                                                     'name': 'admin'},
    #                                                    {'children': [{'children': [{'name': 'year', 'value': '1234'}],
    #                                                                   'name': 'dateIssued'}],
    #                                                     'name': 'originInfo'},
    #                                                    {'attributes': {'lang': 'ace'},
    #                                                     'children': [{'name': 'title', 'value': 'aaas'}],
    #                                                     'name': 'titleInfo'},
    #                                                    {'attributes': {'type': 'contentType'},
    #                                                     'name': 'genre',
    #                                                     'value': 'ref'},
    #                                                    {'children': [{'attributes': {'authority': 'iso639-2b',
    #                                                                                  'type': 'code'},
    #                                                                   'name': 'languageTerm',
    #                                                                   'value': 'afa'}],
    #                                                     'name': 'language',
    #                                                     'repeatId': '0'},
    #                                                    {'attributes': {'type': 'outputType'},
    #                                                     'name': 'genre',
    #                                                     'value': 'publication_report'},
    #                                                    {'children': [{'name': 'visibility', 'value': 'published'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/permissionUnit/uu'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'permissionUnit'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'uu'}],
    #                                                                   'name': 'permissionUnit'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/validationType/publication_report'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'validationType'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'publication_report'}],
    #                                                                   'name': 'validationType'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/system/divaData'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'system'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'divaData'}],
    #                                                                   'name': 'dataDivider'},
    #                                                                  {'name': 'tsVisibility',
    #                                                                   'value': '2025-05-08T14:17:00.674625Z'},
    #                                                                  {'name': 'id',
    #                                                                   'value': 'diva-output:15030850390969906'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/recordType/diva-output'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'recordType'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'diva-output'}],
    #                                                                   'name': 'type'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/user/161616'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'user'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': '161616'}],
    #                                                                   'name': 'createdBy'},
    #                                                                  {'name': 'tsCreated',
    #                                                                   'value': '2025-05-08T14:17:00.682214Z'},
    #                                                                  {'children': [{'name': 'tsUpdated',
    #                                                                                 'value': '2025-05-08T14:17:36.445830Z'},
    #                                                                                {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                                          'rel': 'read',
    #                                                                                                          'requestMethod': 'GET',
    #                                                                                                          'url': 'https://pre.diva-portal.org/rest/record/user/161616'}},
    #                                                                                 'children': [{'name': 'linkedRecordType',
    #                                                                                               'value': 'user'},
    #                                                                                              {'name': 'linkedRecordId',
    #                                                                                               'value': '161616'}],
    #                                                                                 'name': 'updatedBy'}],
    #                                                                   'name': 'updated',
    #                                                                   'repeatId': '0'}],
    #                                                     'name': 'recordInfo'}],
    #                                       'name': 'output'}}},
    #                  {'record': {'actionLinks': {'delete': {'rel': 'delete',
    #                                                         'requestMethod': 'DELETE',
    #                                                         'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15008895675602116'},
    #                                              'index': {'accept': 'application/vnd.cora.record+json',
    #                                                        'body': {'children': [{'children': [{'name': 'linkedRecordType',
    #                                                                                             'value': 'recordType'},
    #                                                                                            {'name': 'linkedRecordId',
    #                                                                                             'value': 'diva-output'}],
    #                                                                               'name': 'recordType'},
    #                                                                              {'name': 'recordId',
    #                                                                               'value': 'diva-output:15008895675602116'},
    #                                                                              {'name': 'type', 'value': 'index'}],
    #                                                                 'name': 'workOrder'},
    #                                                        'contentType': 'application/vnd.cora.recordgroup+json',
    #                                                        'rel': 'index',
    #                                                        'requestMethod': 'POST',
    #                                                        'url': 'https://pre.diva-portal.org/rest/record/workOrder/'},
    #                                              'read': {'accept': 'application/vnd.cora.record+json',
    #                                                       'rel': 'read',
    #                                                       'requestMethod': 'GET',
    #                                                       'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15008895675602116'},
    #                                              'update': {'accept': 'application/vnd.cora.record+json',
    #                                                         'contentType': 'application/vnd.cora.recordgroup+json',
    #                                                         'rel': 'update',
    #                                                         'requestMethod': 'POST',
    #                                                         'url': 'https://pre.diva-portal.org/rest/record/diva-output/diva-output:15008895675602116'}},
    #                              'data': {'children': [{'children': [{'name': 'type', 'value': 'summary'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/binary/binary:15010340076836716'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'binary'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'binary:15010340076836716'}],
    #                                                                   'name': 'attachmentFile'}],
    #                                                     'name': 'attachment',
    #                                                     'repeatId': '0'},
    #                                                    {'children': [{'name': 'reviewed', 'value': 'true'}],
    #                                                     'name': 'admin'},
    #                                                    {'attributes': {'type': 'scopus'},
    #                                                     'name': 'identifier',
    #                                                     'value': '2-s2.0-85217066856'},
    #                                                    {'attributes': {'type': 'pmid'},
    #                                                     'name': 'identifier',
    #                                                     'value': '39921387'},
    #                                                    {'attributes': {'type': 'doi'},
    #                                                     'name': 'identifier',
    #                                                     'value': '10.1002/gcc.70029'},
    #                                                    {'attributes': {'authority': 'ssif'},
    #                                                     'name': 'classification',
    #                                                     'repeatId': '0',
    #                                                     'value': '30202'},
    #                                                    {'children': [{'children': [{'name': 'year', 'value': '2025'}],
    #                                                                   'name': 'dateIssued'}],
    #                                                     'name': 'originInfo'},
    #                                                    {'attributes': {'lang': 'eng'},
    #                                                     'children': [{'name': 'topic',
    #                                                                   'value': 'azacitidine, deletion 5q, high-risk '
    #                                                                            'myelodysplastic syndrome, '
    #                                                                            'lenalidomide, outcome, TP53'}],
    #                                                     'name': 'subject',
    #                                                     'repeatId': '0'},
    #                                                    {'attributes': {'lang': 'eng'},
    #                                                     'name': 'abstract',
    #                                                     'repeatId': '0',
    #                                                     'value': 'In myelodysplastic syndromes (MDS), cytogenetic '
    #                                                              'characteristics of the malignant bone marrow cells '
    #                                                              'influence the clinical course. The aim of this '
    #                                                              'study was to evaluate whether cytogenetics is '
    #                                                              'useful to predict outcome and response in patients '
    #                                                              'with del(5q) under azacitidine (AZA) +/- '
    #                                                              'lenalidomide (LEN) therapy. We therefore performed '
    #                                                              'comprehensive cytogenetic analyses in MDS patients '
    #                                                              'with del(5q) treated within the randomized phase '
    #                                                              'II trial NMDSG10B. Seventy-two patients were '
    #                                                              'enrolled in the study and 46 patients (64%) had '
    #                                                              'sufficient cytogenetics at inclusion and response '
    #                                                              'evaluation. Karyotyping was significantly more '
    #                                                              'sensitive during follow-up to detect del(5q) '
    #                                                              'compared to FISH, 34 patients (97%) versus 27 '
    #                                                              'patients (77%) (p = 0.027). The overall response '
    #                                                              'rate (ORR) did not differ between the 11 patients '
    #                                                              'with < 3 aberrations (median 1 aberration) and the '
    #                                                              '59 patients with >= 3 aberrations (median 7 '
    #                                                              'aberrations, range 3-16), while >= 3 aberrations '
    #                                                              'were associated with shorter overall survival '
    #                                                              '(OS), 9.9 months versus 25.2 months (p = 0.004). '
    #                                                              'OS was significantly shorter in patients with '
    #                                                              'unbalanced translocation of 5q than patients with '
    #                                                              'del (5)(q14q34), 8.4 months versus 21.1 months (p '
    #                                                              '= 0.004). Both complex karyotype and multi-hit '
    #                                                              'TP53 alterations were more frequent in patients '
    #                                                              'with unbalanced translocations of 5q versus del '
    #                                                              '(5)(q14q34), 98% and 88% versus 67% and 47% (each '
    #                                                              'p = < 0.001). Most patients with cytogenetic '
    #                                                              'progression had multi-hit TP53 alterations at '
    #                                                              'inclusion. Cytogenetic progression occurred at a '
    #                                                              'similar frequency in the AZA arm and in the AZA + '
    #                                                              'LEN arm. In summary, this study in homogenously '
    #                                                              'treated MDS patients with different abnormalities '
    #                                                              'of 5q demonstrates the influence of cytogenetics '
    #                                                              'on treatment results. Trial Registration: EudraCT '
    #                                                              'number: 2011-001639-21; identifier: NCT01556477.'},
    #                                                    {'attributes': {'type': 'personal'},
    #                                                     'children': [{'children': [{'attributes': {'type': 'corporate'},
    #                                                                                 'children': [{'name': 'namePart',
    #                                                                                               'value': 'Örebro '
    #                                                                                                        'Univ, '
    #                                                                                                        'Fac Med '
    #                                                                                                        '& Hlth, '
    #                                                                                                        'Dept '
    #                                                                                                        'Med, Div '
    #                                                                                                        'Hematol, '
    #                                                                                                        'Örebro, '
    #                                                                                                        'Sweden..'}],
    #                                                                                 'name': 'name'}],
    #                                                                   'name': 'affiliation',
    #                                                                   'repeatId': '0'},
    #                                                                  {'attributes': {'type': 'given'},
    #                                                                   'name': 'namePart',
    #                                                                   'value': 'Bengt'},
    #                                                                  {'attributes': {'type': 'family'},
    #                                                                   'name': 'namePart',
    #                                                                   'value': 'Rasmussen'}],
    #                                                     'name': 'name',
    #                                                     'repeatId': '0'},
    #                                                    {'attributes': {'lang': 'eng'},
    #                                                     'children': [{'name': 'title',
    #                                                                   'value': 'Influence of Cytogenetics on the '
    #                                                                            'Outcome of Patients With High-Risk '
    #                                                                            'Myelodysplastic Syndrome Including '
    #                                                                            'Deletion 5q Treated With Azacitidine '
    #                                                                            'With or Without Lenalidomide'}],
    #                                                     'name': 'titleInfo'},
    #                                                    {'attributes': {'type': 'contentType'},
    #                                                     'name': 'genre',
    #                                                     'value': 'vet'},
    #                                                    {'children': [{'attributes': {'authority': 'iso639-2b',
    #                                                                                  'type': 'code'},
    #                                                                   'name': 'languageTerm',
    #                                                                   'value': 'eng'}],
    #                                                     'name': 'language',
    #                                                     'repeatId': '0'},
    #                                                    {'attributes': {'type': 'outputType'},
    #                                                     'name': 'genre',
    #                                                     'value': 'publication_journal-article'},
    #                                                    {'children': [{'name': 'visibility', 'value': 'published'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/permissionUnit/uu'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'permissionUnit'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'uu'}],
    #                                                                   'name': 'permissionUnit'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/validationType/publication_journal-article'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'validationType'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'publication_journal-article'}],
    #                                                                   'name': 'validationType'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/system/divaData'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'system'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'divaData'}],
    #                                                                   'name': 'dataDivider'},
    #                                                                  {'name': 'tsVisibility',
    #                                                                   'value': '2025-05-08T08:11:05.960834Z'},
    #                                                                  {'name': 'id',
    #                                                                   'value': 'diva-output:15008895675602116'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/recordType/diva-output'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'recordType'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': 'diva-output'}],
    #                                                                   'name': 'type'},
    #                                                                  {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                            'rel': 'read',
    #                                                                                            'requestMethod': 'GET',
    #                                                                                            'url': 'https://pre.diva-portal.org/rest/record/user/161616'}},
    #                                                                   'children': [{'name': 'linkedRecordType',
    #                                                                                 'value': 'user'},
    #                                                                                {'name': 'linkedRecordId',
    #                                                                                 'value': '161616'}],
    #                                                                   'name': 'createdBy'},
    #                                                                  {'name': 'tsCreated',
    #                                                                   'value': '2025-05-08T08:11:05.966470Z'},
    #                                                                  {'children': [{'name': 'tsUpdated',
    #                                                                                 'value': '2025-05-08T08:56:07.781735Z'},
    #                                                                                {'actionLinks': {'read': {'accept': 'application/vnd.cora.record+json',
    #                                                                                                          'rel': 'read',
    #                                                                                                          'requestMethod': 'GET',
    #                                                                                                          'url': 'https://pre.diva-portal.org/rest/record/user/161616'}},
    #                                                                                 'children': [{'name': 'linkedRecordType',
    #                                                                                               'value': 'user'},
    #                                                                                              {'name': 'linkedRecordId',
    #                                                                                               'value': '161616'}],
    #                                                                                 'name': 'updatedBy'}],
    #                                                                   'name': 'updated',
    #                                                                   'repeatId': '0'}],
    #                                                     'name': 'recordInfo'}],
    #                                       'name': 'output'}}}],
    #         'fromNo': '0',
    #         'toNo': '3',
    #         'totalNo': '3'}}

    recs=get_records_json('diva-person')
    print(f"diva-peron {recs=}")
    pprint.pprint(recs, width=120)

    permanent_record_types=['diva-output', 'diva-publisher', 'diva-journal',
                            'diva-funder', 'diva-publisher', 'diva-person', 'diva-series', 'diva-subject',
                            'diva-course', 'diva-project', 'diva-programme', 'diva-partOfOrganisation',
                            'diva-topOrganisation', 'diva-localGenericMarkup']

    Verbose_Flag=False
    for ty in permanent_record_types:
        print(f'exploring {ty}')
        recs=get_records_json(ty)
        if recs:
            if not recs.get('dataList'):
                print('no dataList')
                continue
            totalNo_as_str=recs['dataList']['totalNo']
            number_of_records=int(recs['dataList']['totalNo'])
            print(f"{number_of_records} records found")
            #print(f"{ty} {recs=}")
            if ty not in ['diva-output', 'diva-funder']: # don't pprint these types of records
                pprint.pprint(recs, width=120)
            if number_of_records > 0:
                data_list_records=recs['dataList']['data']
                for dlr in data_list_records:
                    record_data=dlr['record']['data']
                    record_data_children=record_data['children']
                    for drlc in record_data_children:
                        if drlc['name'] == 'authority':
                            print(f"{drlc['attributes']=} {drlc['children']=} {drlc['name']=}")
                            grand_cildren=drlc['children']
                            for gc in grand_cildren:
                                if gc['name'] == 'name':
                                    print(f"{gc['attributes']['type']=}")
                                    if gc['children']:
                                        for c in gc['children']:
                                            print(f"{c['name']=} {c['value']=}")
                        elif drlc['name'] == 'recordInfo':
                            grand_cildren=drlc['children']
                            for gc in grand_cildren:
                                if gc['name'] == 'id':
                                    print(f"id is {gc['value']}")
                        elif drlc['name'] in ['attachment', 'admin', 'identifier', 'identifier', 'identifier', 'classification', 'originInfo', 'subject', 'abstract', 'name', 'titleInfo', 'genre', 'language', 'genre' ]:
                            continue # simply ignore these cases
                        else:
                            print(f"unknown case: {drlc['name']}")
   
    #/rest/record/searchResult/publicTextSearch?searchData=%7B%22name%22%3A%22textSearch%22%2C%22children%22%3A%5B%7B%22name%22%3A%22include%22%2C%22children%22%3A%5B%7B%22name%22%3A%22includePart%22%2C%22children%22%3A%5B%7B%22name%22%3A%22translationSearchTerm%22%2C%22value%22%3A%22kth%22%7D%5D%7D%5D%7D%5D%7D&preventCache=1746762291840

    Verbose_Flag=False
    print('\npublicTextSeaqrch given a text value')
    #search_data={"name":"textSearch","children":[{"name":"include","children":[{"name":"includePart","children":[{"name":"translationSearchTerm","value":"kth"}]}]}]}
    search_data={"name":"textSearch",
                 "children":[{"name":"include",
                              "children":[{"name":"includePart",
                                           "children":[{"name":"translationSearchTerm","value":"kth"}]}]}]}
    recs=searchResult_search('publicTextSearch', search_data)
    #print(f'{recs=}')
    if Verbose_Flag:
        pprint.pprint(recs)
    if recs:
        if not recs.get('dataList'):
            print('no dataList')
        else:
            totalNo_as_str=recs['dataList']['totalNo']
            number_of_records=int(recs['dataList']['totalNo'])
            print(f"{number_of_records} records found")
            if Verbose_Flag:
                pprint.pprint(recs, width=120)
            if number_of_records > 0:
                data_list_records=recs['dataList']['data']
                for idx, dlr in enumerate(data_list_records):
                    record_data=dlr['record']['data']
                    record_data_children=record_data['children']
                    print(f"record {idx=}")
                    for drlc in record_data_children:
                        if Verbose_Flag:
                            print('printing drlc')
                            if Verbose_Flag:
                                pprint.pprint(drlc, width=120)
                        if drlc['name'] == 'recordInfo':
                            print('printing recordInfo')
                            for gc in drlc['children']:
                                if gc['name'] == 'id':
                                    print(f"id: {gc['value']}")
                        elif drlc['name'] == 'textPart':
                            print(f"language code: {drlc['attributes']['lang']} type: {drlc['attributes']['type']}")
                            for gc in drlc['children']:
                                if gc['name'] == 'text':
                                    print(f"text value: {gc['value']}")

                # if drlc['name'] == 'recordInfo':
                #     grand_cildren=drlc['children']
                #     for gc in grand_cildren:
                #                 if gc['name'] == 'id':
                #                     print(f"id is {gc['value']}")
                #         elif drlc['name'] in ['attachment', 'admin', 'identifier', 'identifier', 'identifier', 'classification', 'originInfo', 'subject', 'abstract', 'name', 'titleInfo', 'genre', 'language', 'genre' ]:
                #             continue # simply ignore these cases
                #         else:
                #             print(f"unknown case: {drlc['name']}")


    # /rest/record/searchResult/publicTextSearch?searchData=%7B%22name%22%3A%22textSearch%22%2C%22children%22%3A%5B%7B%22name%22%3A%22include%22%2C%22children%22%3A%5B%7B%22name%22%3A%22includePart%22%2C%22children%22%3A%5B%7B%22name%22%3A%22recordIdSearchTerm%22%2C%22value%22%3A%22kthTestDiVALoginUnitText%22%7D%5D%7D%5D%7D%5D%7D&preventCache=1746765864510
    print('\npublicTextSeaqrch given a key')
    search_data={"name":  "textSearch",
                 "children": [{"name": "include",
                              "children": [{"name": "includePart",
                                           "children": [{"name": "recordIdSearchTerm",
                                                        "value": "kthTestDiVALoginUnitText"}]}]}]}

    recs=searchResult_search('publicTextSearch', search_data)
    #print(f'{recs=}')
    if Verbose_Flag:
        pprint.pprint(recs)
    if recs:
        if not recs.get('dataList'):
            print('no dataList')
        else:
            totalNo_as_str=recs['dataList']['totalNo']
            number_of_records=int(recs['dataList']['totalNo'])
            print(f"{number_of_records} records found")
            if Verbose_Flag:
                pprint.pprint(recs, width=120)
            if number_of_records > 0:
                data_list_records=recs['dataList']['data']
                for idx, dlr in enumerate(data_list_records):
                    record_data=dlr['record']['data']
                    record_data_children=record_data['children']
                    print(f"record {idx=}")
                    for drlc in record_data_children:
                        if Verbose_Flag:
                            print('printing drlc')
                            pprint.pprint(drlc, width=120)
                        if drlc['name'] == 'recordInfo':
                            print('printing recordInfo')
                            for gc in drlc['children']:
                                if gc['name'] == 'id':
                                    print(f"id: {gc['value']}")
                        elif drlc['name'] == 'textPart':
                            print(f"language code: {drlc['attributes']['lang']} type: {drlc['attributes']['type']}")
                            for gc in drlc['children']:
                                if gc['name'] == 'text':
                                    print(f"text value: {gc['value']}")




    Verbose_Flag=False
    print('diva-output search')
    # /rest/record/searchResult/diva-outputSearch?searchData=%7B%22name%22%3A%22search%22%2C%22children%22%3A%5B%7B%22name%22%3A%22include%22%2C%22children%22%3A%5B%7B%22name%22%3A%22includePart%22%2C%22children%22%3A%5B%7B%22name%22%3A%22recordIdSearchTerm%22%2C%22value%22%3A%22diva-

    search_data={"name": "search",
                 "children": [{"name": "include",
                               "children": [{"name": "includePart",
                                             "children": [{"name": "recordIdSearchTerm",
                                                           "value": "diva-output:15009801329005961"}]}]}]}

    search_result=searchResult_search('diva-outputSearch', search_data)
    print(f"\n{search_result=}")
    
    print(f'Tidsåtgång: {time.time() - starttime}')

    # shutdown in an orderly maner by cancelling the timer for the authToken
    # The all_done() function will get called to kill off all the threads
    app_token_client.cancel_timer()
    #stat=giveup_token(app_token_client.get_auth_token())


    
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
