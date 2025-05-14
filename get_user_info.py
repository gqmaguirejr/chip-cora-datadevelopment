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
import optparse

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
    if Verbose_Flag:
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
    if Verbose_Flag:
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

def delete_a_record(recordType, record_id):
    global Verbose_Flag
    global app_token_client

    recs=get_record_json(recordType, record_id)
    print(f"recs for {recordType}: {record_id}")
    if recs:
        if Verbose_Flag:
            pprint.pprint(recs)
        for al in recs['record']['actionLinks']:
            if Verbose_Flag:
                print(f"action link: {al}")
            if al == 'delete':
                del_url=recs['record']['actionLinks']['delete']['url']
                print(f"{del_url=}")
                # try deleting a record
                del_auth_token = app_token_client.get_auth_token()
                del_headers = { 'Accept': '*/*',
                                'authToken': del_auth_token}
                response = requests.delete(del_url, headers=del_headers)
                # print(f"{response.status_code=}\n{response.text=}\n{response.headers=}\n{response.request.headers=}")
                if response.status_code == '200':
                    if Verbose_Flag:
                        print(f"successfully deleted: {del_url}")
                    return True
    else:
        if Verbose_Flag:
            print("record not found")       
    return False

def get_languageItem(recs):
    rdn=recs['record']['data']['name']
    cid=None
    clang=None
    text_lang_name=dict()
    if rdn == 'metadata':
        rdc=recs['record']['data']['children']
        for c in rdc:
            if c['name'] == 'recordInfo':
                for gc in c['children']:
                    if gc['name'] == 'id':
                        cid =  gc.get('value')
    return cid

def get_languageItemTextId(recs):
    rdn=recs['record']['data']['name']
    cid=None
    clang=None
    text_lang_name=dict()
    if rdn == 'metadata':
        rdc=recs['record']['data']['children']
        for c in rdc:
            if c['name'] == 'textId':
                for gc in c['children']:
                    if gc['name'] == 'linkedRecordId':
                        cid =  gc.get('value')
    return cid



def get_languageItemText(recs):
    rdn=recs['record']['data']['name']
    cid=None
    clang=None
    text_lang_name=dict()
    if rdn == 'text':
        rdc=recs['record']['data']['children']
        for c in rdc:
            if c['name'] == 'recordInfo':
                for gc in c['children']:
                    if gc['name'] == 'id':
                        cid =  gc.get('value')
            elif c['name'] == 'textPart':
                clang=c['attributes'].get('lang')
                for gc in c['children']:
                    text_lang_name[clang]=gc.get('value')
    return cid, text_lang_name


def test_block1():
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


    fromNo=root.find('./fromNo').text
    toNo=root.find('./toNo').text
    totalNo=root.find('./totalNo').text
    print(f"{fromNo=} {toNo=} {totalNo=}")

    user_type_field_width=16
    user_id_field_width=30
    login_id_field_width=40
    userFirstname_field_width=16
    userLastname_field_width=16

    totalNo_as_int=int(totalNo)
    if totalNo_as_int > 0:
        user_type='user_type'
        user_id='user_id'
        login_id='login_id'
        userFirstname='userFirstname'
        userLastname='userLastname'
        print(f"{user_type:<{user_type_field_width}}{user_id:<{user_id_field_width}}{login_id:<{login_id_field_width}}{userFirstname:<{userFirstname_field_width}}{userLastname:<{userLastname_field_width}}")


    for rec in root.findall('./data/record/data/user'):
        if Verbose_Flag:
            print(rec.attrib)
        if rec.attrib and rec.attrib['type']:
            user_type=rec.attrib['type']
            user_id=rec.find('recordInfo/id').text
            login_id=rec.find('loginId').text
            userFirstname=rec.find('userFirstname').text
            userLastname=rec.find('userLastname').text
            print(f"{user_type:<{user_type_field_width}}{user_id:<{user_id_field_width}}{login_id:<{login_id_field_width}}{userFirstname:<{userFirstname_field_width}}{userLastname:<{userLastname_field_width}}")

    # dataList = CommonData.read_source_xml(filePath_sourceXml)
    # list_dataRecord = []
    # for data_record in dataList.findall('.//DATA_RECORD'):
    #     list_dataRecord.append(data_record)
    
    # print(f'Number of records read: {len(list_dataRecord)}')
    
    print(f"\nget_record_json('diva-output', 'diva-output:15009801329005961')")
    rr=get_record_json('diva-output', 'diva-output:15009801329005961')
    if Verbose_Flag:
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



    print(f"\nget_records_json('diva-output')")
    recs=get_records_json('diva-output')
    if Verbose_Flag:
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

    print(f"\nget_records_json('diva-person')")
    recs=get_records_json('diva-person')
    if Verbose_Flag:
        print(f"diva-peron {recs=}")
    if recs:
        if not recs.get('dataList'):
            print('no dataList')
        totalNo_as_str=recs['dataList']['totalNo']
        number_of_records=int(recs['dataList']['totalNo'])
        print(f"{number_of_records} records found")
        if number_of_records > 0:
            pprint.pprint(recs, width=120)



    permanent_record_types=['diva-output', 'diva-publisher', 'diva-journal',
                            'diva-funder', 'diva-publisher', 'diva-person', 'diva-series', 'diva-subject',
                            'diva-course', 'diva-project', 'diva-programme', 'diva-partOfOrganisation',
                            'diva-topOrganisation', 'diva-localGenericMarkup']

    print(f'\nExplore the different types of permanet record types')
    for ty in permanent_record_types:
        print(f'\nexploring {ty}')
        recs=get_records_json(ty)
        if recs:
            if not recs.get('dataList'):
                print('no dataList')
                continue
            totalNo_as_str=recs['dataList']['totalNo']
            number_of_records=int(recs['dataList']['totalNo'])
            print(f"{number_of_records} records found")
            if number_of_records == 0:
                continue
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
                            print(f"{drlc['name']}: {drlc['attributes']=}")
                            grand_cildren=drlc['children']
                            for gc in grand_cildren:
                                if gc['name'] == 'name':
                                    print(f"{drlc['name']}: type {gc['attributes']['type']}")
                                    if gc['children']:
                                        for c in gc['children']:
                                            print(f"{drlc['name']}: {c['name']} {c['value']}")
                        elif drlc['name'] == 'recordInfo':
                            grand_cildren=drlc['children']
                            for gc in grand_cildren:
                                if gc['name'] == 'id':
                                    print(f"id is {gc['value']}")
                        elif drlc['name'] in ['attachment', 'admin', 'identifier', 'identifier', 'identifier', 'classification', 'originInfo', 'subject', 'abstract', 'name', 'titleInfo', 'genre', 'language', 'genre']:
                            continue # simply ignore these cases
                        elif drlc['name'] in  ['location']:
                            grand_cildren=drlc['children']
                            for gc in grand_cildren:
                                print(f"\t{gc['name']} {gc.get('value')}")
                        else:
                            print(f"unknown case: {drlc['name']}")
   
    #/rest/record/searchResult/publicTextSearch?searchData=%7B%22name%22%3A%22textSearch%22%2C%22children%22%3A%5B%7B%22name%22%3A%22include%22%2C%22children%22%3A%5B%7B%22name%22%3A%22includePart%22%2C%22children%22%3A%5B%7B%22name%22%3A%22translationSearchTerm%22%2C%22value%22%3A%22kth%22%7D%5D%7D%5D%7D%5D%7D&preventCache=1746762291840

    search_value="kth"
    print(f'\npublicTextSeaqrch given a translationSearchTerm value: {search_value}')
    #search_data={"name":"textSearch","children":[{"name":"include","children":[{"name":"includePart","children":[{"name":"translationSearchTerm","value":"kth"}]}]}]}
    search_data={"name":"textSearch",
                 "children":[{"name":"include",
                              "children":[{"name":"includePart",
                                           "children":[{"name":"translationSearchTerm","value":search_value}]}]}]}
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
                            print('recordInfo')
                            for gc in drlc['children']:
                                if gc['name'] == 'id':
                                    print(f"\tid: {gc['value']}")
                        elif drlc['name'] == 'textPart':
                            print(f"language code: {drlc['attributes']['lang']} type: {drlc['attributes']['type']}")
                            for gc in drlc['children']:
                                if gc['name'] == 'text':
                                    print(f"\ttext value: {gc['value']}")

    # /rest/record/searchResult/publicTextSearch?searchData=%7B%22name%22%3A%22textSearch%22%2C%22children%22%3A%5B%7B%22name%22%3A%22include%22%2C%22children%22%3A%5B%7B%22name%22%3A%22includePart%22%2C%22children%22%3A%5B%7B%22name%22%3A%22recordIdSearchTerm%22%2C%22value%22%3A%22kthTestDiVALoginUnitText%22%7D%5D%7D%5D%7D%5D%7D&preventCache=1746765864510

    key='kthTestDiVALoginUnitText'
    print(f'\npublicTextSeaqrch given a recordIdSearchTerm: {key}')
    search_data={"name":  "textSearch",
                 "children": [{"name": "include",
                              "children": [{"name": "includePart",
                                           "children": [{"name": "recordIdSearchTerm",
                                                         "value": key}]}]}]}

    recs=searchResult_search('publicTextSearch', search_data)
    #print(f'{recs=}')
    if Verbose_Flag:
        pprint.pprint(recs)
    if recs:
        if not recs.get('dataList'):
            print('no dataList')
        else:
            print(f"Reearch of publicTextSearch for kthTestDiVALoginUnitText")
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
                    if number_of_records > 1:
                        print(f"record {idx=}")
                    for drlc in record_data_children:
                        if Verbose_Flag:
                            print('printing drlc')
                            pprint.pprint(drlc, width=120)
                        if drlc['name'] == 'recordInfo':
                            print('recordInfo')
                            for gc in drlc['children']:
                                if gc['name'] == 'id':
                                    print(f"\tid: {gc['value']}")
                        elif drlc['name'] == 'textPart':
                            print(f"language code: {drlc['attributes']['lang']} type: {drlc['attributes']['type']}")
                            for gc in drlc['children']:
                                if gc['name'] == 'text':
                                    print(f"\ttext value: {gc['value']}")

    Verbose_Flag=False
    print('\ndiva-output search')
    # /rest/record/searchResult/diva-outputSearch?searchData=%7B%22name%22%3A%22search%22%2C%22children%22%3A%5B%7B%22name%22%3A%22include%22%2C%22children%22%3A%5B%7B%22name%22%3A%22includePart%22%2C%22children%22%3A%5B%7B%22name%22%3A%22recordIdSearchTerm%22%2C%22value%22%3A%22diva-

    diva_output_id="diva-output:15009801329005961"
    search_data={"name": "search",
                 "children": [{"name": "include",
                               "children": [{"name": "includePart",
                                             "children": [{"name": "recordIdSearchTerm",
                                                           "value": diva_output_id}]}]}]}

    recs=searchResult_search('diva-outputSearch', search_data)
    if Verbose_Flag:
        pprint.pprint(recs)
    if recs:
        if not recs.get('dataList'):
            print('no dataList')
        else:
            print(f"Result of diva-outputSearch for {diva_output_id}")
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
                    if number_of_records > 1:
                        print(f"record {idx=}")
                    for drlc in record_data_children:
                        if Verbose_Flag:
                            if drlc['name'] not in ['titleInfo', 'attachment',  'admin', 'identifier', 'name', 'genre', 'language', 'recordInfo', 'originInfo', 'classification']:
                                print('printing drlc')
                                pprint.pprint(drlc, width=120)
                        if drlc['name'] == 'recordInfo':
                            print('recordInfo')
                            for gc in drlc['children']:
                                if gc.get('name') in ['permissionUnit', 'validationType', 'dataDivider', 'type', 'createdBy', 'createdBy']:
                                    print(f"\t{gc['name']}")
                                    for ggc in gc['children']:
                                        print(f"\t\t{ggc['name']}: {ggc['value']}")
                                elif gc.get('name') in ['updated']:
                                    for ggc in gc['children']:
                                        if ggc['name'] == 'updatedBy':
                                            print(f"\t{ggc['name']}")
                                            for gggc in ggc['children']:
                                                print(f"\t\t{gggc['name']}: {gggc['value']}")
                                else:
                                    if gc.get('value'):
                                        print(f"\t{gc['name']}: {gc['value']}")
                                    else:
                                        print(f"\t{gc['name']}: !!!")
                        elif drlc['name'] == 'textPart':
                            print(f"language code: {drlc['attributes']['lang']} type: {drlc['attributes']['type']}")
                            for gc in drlc['children']:
                                if gc['name'] == 'text':
                                    print(f"text value: {gc['value']}")
                        elif drlc['name'] == 'attachment':
                            for gc in drlc['children']:
                                if gc['name'] == 'type':
                                    print(f"{drlc['name']}: type: {gc['value']}")
                                elif gc['name'] == 'attachmentFile':
                                    for ggc in gc['children']:
                                        print(f"\t{gc['name']}: {ggc['name']}: {ggc['value']}")
                        elif drlc['name'] == 'name':
                            if drlc.get('attributes'):
                                type_of_name=drlc['attributes']['type']
                                print(f"{type_of_name=}")
                                for gc in drlc['children']:
                                    if gc['name'] == 'role':
                                        for ggc in gc['children']:
                                            print(f"\t{ggc['name']}: {ggc['value']}")
                                    elif gc['name'] == 'namePart':
                                        print(f"\t{gc['attributes']['type']}: {gc['value']}")
                                    else:
                                        print(f"unknow case: {gc}")
                        elif drlc['name'] == 'identifier':
                            print(f"{drlc['name']}: {drlc['attributes']['type']}: {drlc['value']}")
                        elif drlc['name'] == 'classification':
                            print(f"{drlc['name']}: authority {drlc['attributes']['authority']}: {drlc['value']}")
                        elif drlc['name'] == 'originInfo':
                            for gc in drlc['children']:
                                if gc['name'] == 'dateIssued':
                                    for gcc in gc['children']:
                                        print(f"dateIssued: {gcc['name']} {gcc['value']}")
                        elif drlc['name'] == 'languageTerm':
                            print(f"language code: {drlc['value']} attributes {drlc['attributes']}")
                        elif drlc['name'] == 'titleInfo':
                            for gc in drlc['children']:
                                if gc['name'] == 'title':
                                    print(f"title [{drlc['attributes']['lang']}]: {gc['value']}")
                        elif drlc['name'] == 'language':
                            for gc in drlc['children']:
                                print(f"{gc['name']} language code: {gc['value']}, attributes {gc['attributes']['type']} {gc['attributes']['authority']}")
                        elif drlc['name'] == 'admin':
                            for gc in drlc['children']:
                                print(f"{drlc['name']}: {gc['name']}: {gc['value']}")
                        elif drlc['name'] == 'genre':
                            print(f"genre: {drlc['value']} type: {drlc['attributes']['type']}")

                        else:
                            print(f"unknown case {drlc=}")


    #searchData=%7B%22name%22%3A%22search%22%2C%22children%22%3A%5B%7B%22name%22%3A%22include%22%2C%22children%22%3A%5B%7B%22name%22%3A%22includePart%22%2C%22children%22%3A%5B%7B%22name%22%3A%22genericSearchTerm%22%2C%22value%22%3A%22free_text_a%22%7D%2C%7B%22name%22%3A%22recordIdSearchTerm%22%2C%22value%22%3A%22id_b%22%7D%2C%7B%22name%22%3A%22oldIdSearchTerm%22%2C%22value%22%3A%22oldid_c%22%7D%2C%7B%22name%22%3A%22titleSearchTerm%22%2C%22value%22%3A%22title_d%22%7D%2C%7B%22name%22%3A%22doiSearchTerm%22%2C%22value%22%3A%22doi_e%22%7D%2C%7B%22name%22%3A%22seLibrSearchTerm%22%2C%22value%22%3A%22libris_f%22%7D%2C%7B%22name%22%3A%22localIdSearchTerm%22%2C%22value%22%3A%22local_id_g%22%7D%2C%7B%22name%22%3A%22keywordsSearchTerm%22%2C%22value%22%3A%22keywords_h%22%7D%2C%7B%22name%22%3A%22noteExternalSearchTerm%22%2C%22value%22%3A%22note_i%22%7D%5D%7D%5D%7D%2C%7B%22name%22%3A%22start%22%2C%22value%22%3A%222025%22%7D%5D%7D&preventCache=1746865082895


    # it is possible to search using multiple criteria in the diva-output
    search_data={"name":"search",
                 "children":[{"name":"include",
                              "children":[{"name":"includePart",
                                           "children":[{"name":"genericSearchTerm","value":"free_text_a"},
                                                       {"name":"recordIdSearchTerm","value":"id_b"},
                                                       {"name":"oldIdSearchTerm","value":"oldid_c"},
                                                       {"name":"titleSearchTerm","value":"title_d"},
                                                       {"name":"doiSearchTerm","value":"doi_e"},
                                                       {"name":"seLibrSearchTerm","value":"libris_f"},
                                                       {"name":"localIdSearchTerm","value":"local_id_g"},
                                                       {"name":"keywordsSearchTerm","value":"keywords_h"},
                                                       {"name":"noteExternalSearchTerm","value":"note_i"}
                                                       ]}
                                          ]},
                             {"name":"start","value":"2025"}]}


    # Additionally, there are two search fields using pull-down lists: ``Sustainable Development'' ("sdgSearchTerm") and `Standard for Swedish classification of research topics (SSIF)'' ("ssifSearchTerm")
    # In Swedish: Hållbar utveckling and Standard för svensk indelning av forskningsämnen (SSIF)

    # Search?searchData=%7B%22name%22%3A%22search%22%2C%22children%22%3A%5B%7B%22name%22%3A%22include%22%2C%22children%22%3A%5B%7B%22name%22%3A%22includePart%22%2C%22children%22%3A%5B%7B%22name%22%3A%22genericSearchTerm%22%2C%22value%22%3A%22free_text_a%22%7D%2C%7B%22name%22%3A%22recordIdSearchTerm%22%2C%22value%22%3A%22id_b%22%7D%2C%7B%22name%22%3A%22oldIdSearchTerm%22%2C%22value%22%3A%22oldid_c%22%7D%2C%7B%22name%22%3A%22titleSearchTerm%22%2C%22value%22%3A%22title_d%22%7D%2C%7B%22name%22%3A%22doiSearchTerm%22%2C%22value%22%3A%22doi_e%22%7D%2C%7B%22name%22%3A%22seLibrSearchTerm%22%2C%22value%22%3A%22libris_f%22%7D%2C%7B%22name%22%3A%22localIdSearchTerm%22%2C%22value%22%3A%22local_id_g%22%7D%2C%7B%22name%22%3A%22keywordsSearchTerm%22%2C%22value%22%3A%22keywords_h%22%7D%2C%7B%22name%22%3A%22noteExternalSearchTerm%22%2C%22value%22%3A%22note_i%22%7D%2C%7B%22name%22%3A%22sdgSearchTerm%22%2C%22value%22%3A%22sdg1%22%7D%2C%7B%22name%22%3A%22ssifSearchTerm%22%2C%22value%22%3A%2210206%22%7D%5D%7D%5D%7D%2C%7B%22name%22%3A%22start%22%2C%22value%22%3A%222025%22%7D%5D%7D&preventCache=1746872096967

    search_data={"name": "search",
                 "children": [{"name": "include",
                               "children": [{"name": "includePart",
                                             "children": [{"name":"genericSearchTerm", "value":"free_text_a"},
                                                          {"name":"recordIdSearchTerm","value":"id_b"},
                                                          {"name":"oldIdSearchTerm","value":"oldid_c"},
                                                          {"name":"titleSearchTerm","value":"title_d"},
                                                          {"name":"doiSearchTerm","value":"doi_e"},
                                                          {"name":"seLibrSearchTerm","value":"libris_f"},
                                                          {"name":"localIdSearchTerm","value":"local_id_g"},
                                                          {"name":"keywordsSearchTerm","value":"keywords_h"},
                                                          {"name":"noteExternalSearchTerm","value":"note_i"},
                                                          {"name":"sdgSearchTerm","value":"sdg1"},
                                                          {"name":"ssifSearchTerm","value":"10206"}]
                                             }]
                               },
                              {"name":"start","value":"2025"}]}

    # Note that ``Sustainable Development'' ("sdgSearchTerm") has a pull-down list of the UN's Sustainable Development Goals (SDGs). The options in this list are:
    # <option value="sdg1">1. No poverty					Ingen fattigdom
    # <option value="sdg2">2. Zero hunger					Ingen hunger
    # <option value="sdg3">3. Good health and well-being			God hälsa och välbefinnande
    # <option value="sdg4">4. Quality education					God utbildning för alla
    # <option value="sdg5">5. Gender equality					Jämställdhet
    # <option value="sdg6">6. Clean water and sanitation			Rent vatten och sanitet för alla
    # <option value="sdg7">7. Affordable and clean energy			Hållbar energi för alla
    # <option value="sdg8">8. Decent work and economic growth			Anständiga arbetsvillkor och ekonomisk tillväxt
    # <option value="sdg9">9. Industry, innovation and infrastructure		Hållbar industri, innovationer och infrastruktur
    # <option value="sdg10">10. Reduced inequalities				Minskad ojämlikhet
    # <option value="sdg11">11. Sustainable cities and communities		Hållbara städer och samhällen
    # <option value="sdg12">12. Responsible consumption and production		Hållbar konsumtion och produktion
    # <option value="sdg13">13. Climate action					Bekämpa klimatförändringarna
    # <option value="sdg14">14. Life below water				Hav och marina resurser
    # <option value="sdg15">15. Life on land					Ekosystem och biologisk mångfald
    # <option value="sdg16">16. Peace, justice and strong institutions		Fredliga och inkluderande samhällen
    # <option value="sdg17">17. Partnerships for the goals			Genomförande och globalt partnerskap

    # Similarly `Standard for Swedish classification of research topics (SSIF)'' ("ssifSearchTerm") has a pulldown lisat with the following options:
    # <option value="1">(1) Natural sciences					Naturvetenskap
	# <option value="101">(101) Mathematical sciences			Matematik
	# <option value="10101">(10101) Mathematical Analysis			Matematisk analys
	# <option value="10102">(10102) Geometry				Geometri
	# <option value="10103">(10103) Algebra and Logic			Algebra och logik
	# <option value="10104">(10104) Discrete Mathematics			Diskret matematik
	# <option value="10105">(10105) Computational Mathematics		Beräkningsmatematik
	# <option value="10106">(10106) Probability Theory and Statistics	Sannolikhetsteori och statistik
	# <option value="10199">(10199) Other Mathematics			Annan matematik
	# <option value="102">(102) Computer and Information Sciences		Data- och informationsvetenskap (Datateknik)
	# <option value="10201">(10201) Computer Sciences			Datavetenskap (datalogi)
	# <option value="10202">(10202) Information Systems			Systemvetenskap, informationssystem och informatik
	# <option value="10203">(10203) Bioinformatics (Computational Biology)	Bioinformatik (beräkningsbiologi)
	# <option value="10204">(10204) Human Computer Interaction		Människa-datorinteraktion (interaktionsdesign)
	# <option value="10205">(10205) Software Engineering			Programvaruteknik
	# <option value="10206">(10206) Computer Engineering			Datorteknik
	# <option value="10207">(10207) Computer graphics and computer vision	Datorgrafik och datorseende
	# <option value="10208">(10208) Natural Language Processing		Språkbehandling och datorlingvistik
	# <option value="10210">(10210) Artificial Intelligence			Artificiell intelligens
	# <option value="10211">(10211) Security, Privacy and Cryptography	Säkerhet, integritet och kryptologi
	# <option value="10212">(10212) Algorithms				Algoritmer
	# <option value="10213">(10213) Formal Methods				Formella metoder
	# <option value="10214">(10214) Networked, Parallel and Distributed Computing	Nätverks-, parallell- och distribuerad beräkning
	# <option value="10299">(10299) Other Computer and Information Science	Annan data- och informationsvetenskap
	# <option value="103">(103) Physical Sciences				Fysik
	# <option value="10301">(10301) Subatomic Physics			Subatomär fysik
	# <option value="10302">(10302) Atom and Molecular Physics and Optics	Atom- och molekylfysik och optik
	# <option value="10303">(10303) Fusion, Plasma and Space Physics	Fusion, plasma och rymdfysik
	# <option value="10304">(10304) Condensed Matter Physics		Den kondenserade materiens fysik
	# <option value="10305">(10305) Astronomy, Astrophysics, and Cosmology	Astronomi, astrofysik och kosmologi
        # <option value="10307">(10307) Biophysics				Biofysik
	# <option value="10308">(10308) Statistical physics and complex systems	Statistisk fysik och komplexa system
	# <option value="10399">(10399) Other Physics Topics			Annan fysik
	# <option value="104">(104) Chemical Sciences				Kemi
	# <option value="10401">(10401) Analytical Chemistry			Analytisk kemi
	# <option value="10402">(10402) Physical Chemistry			Fysikalisk kemi
	# <option value="10403">(10403) Materials Chemistry			Materialkemi
	# <option value="10404">(10404) Inorganic Chemistry			Oorganisk kemi
	# <option value="10405">(10405) Organic Chemistry			Organisk kemi
	# <option value="10406">(10406) Polymer Chemistry			Polymerkemi
	# <option value="10407">(10407) Theoretical Chemistry			Teoretisk kemi
	# <option value="10408">(10408) Biochemistry				Biokemi
	# <option value="10499">(10499) Other Chemistry Topics			Annan kemi
	# <option value="105">(105) Earth and Related Environmental Sciences	Geovetenskap och relaterad miljövetenskap
	# <option value="10501">(10501) Climate Science				Klimatvetenskap
	# <option value="10502">(10502) Environmental Sciences			Miljövetenskap
	# <option value="10503">(10503) Multidisciplinary Geosciences		Multidisciplinär geovetenskap
	# <option value="10504">(10504) Geology					Geologi
	# <option value="10505">(10505) Geophysics				Geofysik
	# <option value="10506">(10506) Geochemistry				Geokemi
	# <option value="10507">(10507) Physical Geography			Naturgeografi
	# <option value="10508">(10508) Meteorology and Atmospheric Sciences	Meteorologi och atmosfärsvetenskap
	# <option value="10509">(10509) Oceanography, Hydrology and Water Resources	Oceanografi, hydrologi och vattenresurser
	# <option value="10510">(10510) Palaeontology and Palaeoecology		Paleontologi och paleoekologi
	# <option value="10599">(10599) Other Earth Sciences			Annan geovetenskap
	# <option value="106">(106) Biological Sciences				Biologi
	# <option value="10601">(10601) Structural Biology			Strukturbiologi
	# <option value="10604">(10604) Cell Biology				Cellbiologi
	# <option value="10605">(10605) Immunology				Immunologi
	# <option value="10606">(10606) Microbiology				Mikrobiologi
	# <option value="10607">(10607) Botany					Botanik
	# <option value="10608">(10608) Zoology					Zoologi
	# <option value="10609">(10609) Genetics and Genomics			Genetik och genomik
	# <option value="10610">(10610) Bioinformatics and Computational Biology	Bioinformatik och beräkningsbiologi
	# <option value="10611">(10611) Ecology					Ekologi
	# <option value="10612">(10612) Biological Systematics			Biologisk systematik
	# <option value="10613">(10613) Behavioural Sciences Biology		Etologi
	# <option value="10614">(10614) Developmental Biology			Utvecklingsbiologi
	# <option value="10615">(10615) Evolutionary Biology			Evolutionsbiologi
	# <option value="10616">(10616) Molecular Biology			Molekylärbiologi
	# <option value="10699">(10699) Other Biological Topics			Annan biologi
	# <option value="107">(107) Other Natural Sciences			Annan naturvetenskap
	# <option value="10799">(10799) Other Natural Sciences			Annan naturvetenskap
	# <option value="2">(2) Engineering and Technology			Teknik
	# <option value="201">(201) Civil Engineering				Samhällsbyggnadsteknik
	# <option value="20101">(20101) Architectural Engineering		Arkitekturteknik
	# <option value="20102">(20102) Construction Management			Byggprocess och förvaltning
	# <option value="20103">(20103) Building Technologies			Husbyggnad
	# <option value="20104">(20104) Infrastructure Engineering		Infrastrukturteknik
	# <option value="20105">(20105) Transport Systems and Logistics		Transportteknik och logistik
	# <option value="20106">(20106) Geotechnical Engineering and Engineering Geology	Geoteknik och teknisk geologi
	# <option value="20107">(20107) Water Engineering			Vattenteknik
	# <option value="20109">(20109) Structural Engineering			Byggkonstruktion
	# <option value="20110">(20110) Building materials			Byggnadsmaterial
	# <option value="20199">(20199) Other Civil Engineering			Annan samhällsbyggnadsteknik
	# <option value="202">(202) Electrical Engineering, Electronic Engineering, Information Engineering	Elektroteknik och elektronik
	# <option value="20201">(20201) Robotics and automation			Robotik och automation
	# <option value="20202">(20202) Control Engineering			Reglerteknik
	# <option value="20203">(20203) Communication Systems			Kommunikationssystem
	# <option value="20204">(20204) Telecommunications			Telekommunikation
	# <option value="20205">(20205) Signal Processing			Signalbehandling
	# <option value="20206">(20206) Computer Systems			Datorsystem
	# <option value="20207">(20207) Embedded Systems			Inbäddad systemteknik
	# <option value="20208">(20208) Computer Vision and learning System	Datorseende och lärande system
	# <option value="20209">(20209) Power Systems and Components		Elkraftsystem och -komponenter
	# <option value="20299">(20299) Other Electrical Engineering, Electronic Engineering, Information Engineering	Annan elektroteknik och elektronik
	# <option value="203">(203) Mechanical Engineering			Maskinteknik
	# <option value="20301">(20301) Applied Mechanics			Teknisk mekanik
	# <option value="20302">(20302) Vehicle and Aerospace Engineering	Farkost och rymdteknik
	# <option value="20304">(20304) Energy Engineering			Energiteknik
	# <option value="20305">(20305) Reliability and Maintenance		Tillförlitlighets- och kvalitetsteknik
	# <option value="20306">(20306) Fluid Mechanics				Strömningsmekanik
	# <option value="20307">(20307) Production Engineering, Human Work Science and Ergonomics	Produktionsteknik, arbetsvetenskap och ergonomi
	# <option value="20309">(20309) Solid and Structural Mechanics		Solid- och strukturmekanik
	# <option value="20310">(20310) Industrial engineering and management	Industriell ekonomi
	# <option value="20399">(20399) Other Mechanical Engineering		Annan maskinteknik
	# <option value="204">(204) Chemical Engineering			Kemiteknik
	# <option value="20402">(20402) Surface- and Corrosion Engineering	Yt- och korrosionsteknik
	# <option value="20403">(20403) Polymer Technologies			Polymerteknologi
	# <option value="20405">(20405) Catalytic Processes			Katalytiska processer
	# <option value="20406">(20406) Separation Processes			Separationsprocesser
	# <option value="20407">(20407) Circular Food Process Technologies	Livsmedelsprocessteknik
	# <option value="20499">(20499) Other Chemical Engineering		Annan kemiteknik
	# <option value="205">(205) Materials Engineering			Materialteknik
	# <option value="20501">(20501) Ceramics and Powder Metallurgical Materials	Keramiska och pulvermetallurgiska material
	# <option value="20502">(20502) Composite Science and Engineering	Kompositmaterial och kompositteknik
	# <option value="20503">(20503) Paper, Pulp and Fiber Technology	Pappers-, massa- och fiberteknik
	# <option value="20504">(20504) Textile, Rubber and Polymeric Materials	Textil-, gummi- och polymermaterial
	# <option value="20505">(20505) Manufacturing, Surface and Joining Technology	Bearbetnings-, yt- och fogningsteknik
	# <option value="20506">(20506) Metallurgy and Metallic Materials	Metallurgi och metalliska material
	# <option value="20599">(20599) Other Materials Engineering		Annan materialteknik
	# <option value="206">(206) Medical Engineering				Medicinteknik
	# <option value="20601">(20601) Medical Laboratory Technologies		Medicinsk laboratorieteknik
	# <option value="20602">(20602) Medical Materials			Medicinsk materialteknik
	# <option value="20603">(20603) Medical Imaging				Medicinsk bildvetenskap
	# <option value="20604">(20604) Medical Instrumentation			Medicinsk instrumentering
	# <option value="20605">(20605) Medical Modelling and Simulation	Medicinsk modellering och simulering
	# <option value="20606">(20606) Medical Informatics Engineering		Medicinteknisk informatik
	# <option value="20699">(20699) Other Medical Engineering		Annan medicinteknik
	# <option value="207">(207) Environmental Engineering			Naturresursteknik
	# <option value="20702">(20702) Energy Systems				Energisystem
	# <option value="20703">(20703) Earth Observation			Jordobservationsteknik
	# <option value="20704">(20704) Mineral and Mine Engineering		Mineral- och gruvteknik
	# <option value="20705">(20705) Marine Engineering			Marinteknik
	# <option value="20707">(20707) Environmental Management		Miljöteknik och miljöledning
	# <option value="20799">(20799) Other Environmental Engineering		Annan naturresursteknik
	# <option value="208">(208) Environmental Biotechnology			Miljöbioteknik
	# <option value="20801">(20801) Bioremediation				Biosanering
        # <option value="20802">(20802) Diagnostic Biotechnology		Diagnostisk bioteknologi
	# <option value="20803">(20803) Water Treatment				Vattenbehandlingsbioteknik
	# <option value="20899">(20899) Other Environmental Biotechnology	Annan miljöbioteknik
	# <option value="209">(209) Industrial Biotechnology			Industriell bioteknik
	# <option value="20901">(20901) Bioprocess Technology			Bioprocessteknik
	# <option value="20902">(20902) Biochemicals				Biokemikalier
	# <option value="20903">(20903) Bio Materials				Biomaterial
	# <option value="20904">(20904) Bioenergy				Bioenergi
	# <option value="20905">(20905) Pharmaceutical and Medical Biotechnology	Läkemedel- och medicinsk processbioteknik
	# <option value="20906">(20906) Biocatalysis and Enzyme Technology	Biokatalys och enzymteknik
	# <option value="20909">(20909) Food Biotechnology			Livsmedelsbioteknik
	# <option value="20999">(20999) Other Industrial Biotechnology		Annan industriell bioteknik
	# <option value="210">(210) Nano-technology				Nanoteknik
	# <option value="21002">(21002) Nanotechnology for Electronic Applications	Nanoteknisk elektronik
	# <option value="21003">(21003) Nanotechnology for Material Science	Nanoteknisk materialvetenskap
	# <option value="21004">(21004) Nanotechnology for Energy Applications	Nanotekniska energitillämpningar
	# <option value="21005">(21005) Nanotechnology for/in Life Science and Medicine	Nanotekniska livsvetenskaper och medicin
	# <option value="21099">(21099) Other Nanotechnology			Annan nanoteknik
	# <option value="211">(211) Other Engineering and Technologies		Annan teknik
	# <option value="21199">(21199) Other Engineering and Technologies	Annan teknik
	# <option value="3">(3) Medical and Health Sciences			Medicin och hälsovetenskap
	# <option value="301">(301) Basic Medicine				Medicinska och farmaceutiska grundvetenskaper
	# <option value="30101">(30101) Pharmaceutical Sciences			Farmaceutiska vetenskaper
	# <option value="30102">(30102) Pharmacology and Toxicology		Farmakologi och toxikologi
	# <option value="30103">(30103) Medicinal Chemistry			Läkemedelskemi
	# <option value="30104">(30104) Social and Clinical Pharmacy		Samhällsfarmaci och klinisk farmaci
	# <option value="30105">(30105) Neurosciences				Neurovetenskaper
	# <option value="30106">(30106) Physiology and Anatomy			Fysiologi och anatomi
	# <option value="30107">(30107) Medical Genetics and Genomics		Medicinsk genetik och genomik
	# <option value="30108">(30108) Cell and Molecular Biology		Cell- och molekylärbiologi
	# <option value="30109">(30109) Microbiology in the Medical Area	Mikrobiologi inom det medicinska området
	# <option value="30110">(30110) Immunology in the Medical Area		Immunologi inom det medicinska området
	# <option value="30111">(30111) Medical Life Sciences			Medicinska biovetenskaper
	# <option value="30112">(30112) Basic Cancer Research			Basal cancerforskning
	# <option value="30113">(30113) Medical Bioinformatics and Systems Biology	Medicinsk bioinformatik och systembiologi
	# <option value="30114">(30114) Evolution and Developmental Genetics	Evolution och utvecklingsgenetik
	# <option value="30115">(30115) Medical Epigenetics and Epigenomics	Medicinsk epigenetik och epigenomik
	# <option value="30116">(30116) Epidemiology				Epidemiologi
	# <option value="30117">(30117) Medical Informatics			Medicinsk informatik
	# <option value="30118">(30118) Medical Biostatistics			Medicinsk biostatistik
	# <option value="30199">(30199) Other Basic Medicine			Andra medicinska och farmaceutiska grundvetenskaper
	# <option value="302">(302) Clinical Medicine				Klinisk medicin
	# <option value="30201">(30201) Anesthesiology and Intensive Care	Anestesi och intensivvård
	# <option value="30202">(30202) Hematology				Hematologi
	# <option value="30203">(30203) Cancer and Oncology			Cancer och onkologi
	# <option value="30204">(30204) Dermatology and Venereal Diseases	Dermatologi och venereologi
	# <option value="30205">(30205) Endocrinology and Diabetes		Endokrinologi och diabetes
	# <option value="30206">(30206) Cardiology and Cardiovascular Disease	Kardiologi och kardiovaskulära sjukdomar
	# <option value="30207">(30207) Neurology				Neurologi
	# <option value="30208">(30208) Radiology and Medical Imaging		Radiologi och bildbehandling
	# <option value="30209">(30209) Infectious Medicine			Infektionsmedicin
	# <option value="30211">(30211) Orthopaedics				Ortopedi
	# <option value="30212">(30212) Surgery					Kirurgi
	# <option value="30213">(30213) Gastroenterology and Hepatology		Gastroenterologi and hepatologi
	# <option value="30215">(30215) Psychiatry				Psykiatri
	# <option value="30216">(30216) Odontology				Odontologi
	# <option value="30217">(30217) Ophthalmology				Oftalmologi
	# <option value="30218">(30218) Oto-rhino-laryngology			Oto-rhino-laryngologi
	# <option value="30219">(30219) Respiratory Medicine and Allergy	Lungmedicin och allergi
	# <option value="30220">(30220) Gynaecology, Obstetrics and Reproductive Medicine	Gynekologi, obstetrik och reproduktionsmedicin
	# <option value="30221">(30221) Pediatrics				Pediatrik
	# <option value="30222">(30222) Geriatrics				Geriatrik
	# <option value="30223">(30223) Clinical Laboratory Medicine		Klinisk laboratoriemedicin
	# <option value="30224">(30224) General Medicine			Allmänmedicin
	# <option value="30225">(30225) Rheumatology				Reumatologi
	# <option value="30226">(30226) Autoimmunity and Inflammation		Autoimmunitet och inflamation
	# <option value="30227">(30227) Internal Medicine			Internmedicin
	# <option value="30228">(30228) Urology					Urologi
	# <option value="30229">(30229) Nephrology				Njurmedicin
	# <option value="30230">(30230) Childbirth and Maternity care		Förlossnings- och mödravård
	# <option value="30299">(30299) Other Clinical Medicine			Annan klinisk medicin
	# <option value="303">(303) Health Sciences				Hälsovetenskap
	# <option value="30301">(30301) Health Care&nbsp;Service and Management, Health Policy and Services and&nbsp;Health Economy	Hälso- och sjukvårdsorganisation, hälsopolitik och hälsoekonomi
	# <option value="30303">(30303) Occupational Health and Environmental Health	Arbetsmedicin och miljömedicin
	# <option value="30304">(30304) Nutrition and Dietetics			Näringslära och dietkunskap
	# <option value="30305">(30305) Nursing					Omvårdnad
	# <option value="30306">(30306) Occupational Therapy			Arbetsterapi
	# <option value="30307">(30307) Physiotherapy				Fysioterapi
	# <option value="30308">(30308) Sport and Fitness Sciences		Idrottsvetenskap och fitness
	# <option value="30309">(30309) Drug Abuse and Addiction		Beroendelära och missbruk
	# <option value="30310">(30310) Medical Ethics				Medicinsk etik
	# <option value="30311">(30311) Public Health, Global Health and Social Medicine	Folkhälsovetenskap, global hälsa och socialmedicin
	# <option value="30312">(30312) Palliative Medicine and Palliative Care	Palliativ medicin och palliativ vård
	# <option value="30313">(30313) Oral Health				Oral hälsa
	# <option value="30314">(30314) Rehabilitation Medicine			Rehabiliteringsmedicin
	# <option value="30399">(30399) Other Health Sciences			Annan hälsovetenskap
	# <option value="304">(304) Medical Biotechnology			Medicinsk bioteknologi
	# <option value="30401">(30401) Medical Biotechnology (Focus on Cell Biology (incl. Stem Cell Biology), Molecular Biology, Microbiology, Biochemistry or Biopharmacy)	Medicinsk bioteknologi (Inriktn. mot cellbiologi (inkl. stamcellsbiologi), molekylärbiologi, mikrobiologi, biokemi eller biofarmaci)
	# <option value="30402">(30402) Biomedical Laboratory Science/Technology	Biomedicinsk laboratorievetenskap/teknologi
	# <option value="30403">(30403) Biomaterials Science			Biomaterialvetenskap
	# <option value="30499">(30499) Other Medical Biotechnology		Annan medicinsk bioteknologi
	# <option value="305">(305) Other Medical and Health Sciences		Annan medicin och hälsovetenskap
	# <option value="30501">(30501) Forensic Science			Rättsmedicin
	# <option value="30502">(30502) Gerontology, specialising in Medical and Health Sciences	Gerontologi, medicinsk/hälsovetenskaplig inriktning
	# <option value="30599">(30599) Other Medical and Health Sciences not elsewhere specified	Övrig annan medicin och hälsovetenskap
	# <option value="4">(4) Agricultural and Veterinary sciences		Lantbruksvetenskap och veterinärmedicin
	# <option value="401">(401) Agriculture, Forestry and Fisheries		Jordbruk, skogsbruk och fiske
	# <option value="40101">(40101) Agricultural Science			Jordbruksvetenskap
	# <option value="40102">(40102) Horticulture				Trädgårdsvetenskap/hortikultur
	# <option value="40103">(40103) Food Science				Livsmedelsvetenskap
	# <option value="40104">(40104) Forest Science				Skogsvetenskap
	# <option value="40105">(40105) Wood Science				Trävetenskap
	# <option value="40106">(40106) Soil Science				Markvetenskap
	# <option value="40107">(40107) Fish and Aquacultural Science		Fisk- och akvakulturforskning
	# <option value="402">(402) Animal and Dairy Science			Husdjursvetenskap
	# <option value="40201">(40201) Animal and Dairy Science		Husdjursvetenskap
	# <option value="403">(403) Veterinary Science				Veterinärmedicin
	# <option value="40301">(40301) Medical Bioscience			Medicinsk biovetenskap
	# <option value="40302">(40302) Pathobiology				Patobiologi
	# <option value="40303">(40303) Clinical Science			Klinisk vetenskap
	# <option value="40399">(40399) Other Veterinary Science		Annan veterinärmedicin
	# <option value="404">(404) Agricultural Biotechnology			Bioteknologi med applikationer på växter och djur
	# <option value="40401">(40401) Plant Biotechnology			Växtbioteknologi
	# <option value="40402">(40402) Genetics and Breeding in Agricultural Sciences	Genetik och förädling inom lantbruksvetenskap
	# <option value="405">(405) Other Agricultural Sciences			Annan lantbruksvetenskap
	# <option value="40502">(40502) Fish and Wildlife Management		Vilt- och fiskeförvaltning
	# <option value="40504">(40504) Environmental Sciences and Nature Conservation	Miljö- och naturvårdsvetenskap
	# <option value="40505">(40505) Landscape Architecture			Landskapsarkitektur
	# <option value="40506">(40506) Agricultural Economics and Management and Rural development	Jordbruksekonomi och landsbygdsutveckling
	# <option value="40507">(40507) Environmental Economics and Management	Miljöekonomi och förvaltning
	# <option value="40599">(40599) Other Agricultural Sciences not elsewhere specified	Övrig annan lantbruksvetenskap
	# <option value="5">(5) Social Sciences					Samhällsvetenskap
	# <option value="501">(501) Psychology					Psykologi
	# <option value="50101">(50101) Psychology (Excluding Applied Psychology)	Psykologi (Exklusive tillämpad psykologi)
	# <option value="50102">(50102) Applied Psychology			Tillämpad psykologi
	# <option value="502">(502) Economics and Business			Ekonomi och näringsliv
	# <option value="50201">(50201) Economics				Nationalekonomi
	# <option value="50202">(50202) Business Administration			Företagsekonomi
	# <option value="50203">(50203) Economic History			Ekonomisk historia
	# <option value="503">(503) Educational Sciences			Utbildningsvetenskap
	# <option value="50301">(50301) Pedagogy				Pedagogik
	# <option value="50302">(50302) Didactics				Didaktik
	# <option value="50304">(50304) Educational Work			Pedagogiskt arbete
	# <option value="50399">(50399) Other Educational Sciences		Annan utbildningsvetenskaplig forskning
	# <option value="504">(504) Sociology					Sociologi
	# <option value="50401">(50401) Sociology (Excluding Social Work, Social Anthropology, Demography and Criminology)	Sociologi (Exklusive socialt arbete, socialantropologi, demografi och kriminologi)
	# <option value="50402">(50402) Social Work				Socialt arbete
	# <option value="50404">(50404) Social Anthropology			Socialantropologi
	# <option value="50405">(50405) Demography				Demografi
	# <option value="50406">(50406) Criminology				Kriminologi
	# <option value="505">(505) Law						Juridik
	# <option value="50501">(50501) Law					Juridik
	# <option value="50503">(50503) Other Legal Research			Annan rättsvetenskaplig forskning
	# <option value="506">(506) Political Science				Statsvetenskap
	# <option value="50601">(50601) Political Science (Excluding Peace and Conflict Studies)	Statsvetenskap (Exklusive freds- och konfliktforskning)
	# <option value="50604">(50604) Peace and Conflict Studies		Freds- och konfliktforskning
	# <option value="507">(507) Social and Economic Geography		Social och ekonomisk geografi
	# <option value="50701">(50701) Human Geography				Kulturgeografi
	# <option value="50702">(50702) Economic Geography			Ekonomisk geografi
	# <option value="50703">(50703) Other Geographic Studies		Andra geografiska studier
	# <option value="508">(508) Media and Communications			Medie-, kommunikations-, och informationsvetenskaper
	# <option value="50801">(50801) Media and Communication Studies		Medie- och kommunikationsvetenskap
	# <option value="50804">(50804) Information Systems, Social aspects	Systemvetenskap, informationssystem och informatik med samhällsvetenskaplig inriktning
	# <option value="50805">(50805) Information Studies			Biblioteks-och informationsvetenskap
	# <option value="509">(509) Other Social Sciences			Annan samhällsvetenskap
	# <option value="50902">(50902) Gender Studies				Genusstudier
	# <option value="50903">(50903) Work Sciences				Arbetslivsstudier
	# <option value="50904">(50904) International Migration and Ethnic Relations	Internationell migration och etniska relationer (IMER)
	# <option value="50905">(50905) Public Administration Studies		Studier av offentlig förvaltning
	# <option value="50906">(50906) Development Studies			Utvecklingsstudier
	# <option value="50907">(50907) Statistics in Social Sciences		Statistik inom samhällsvetenskap
	# <option value="50908">(50908) Health and Diet Studies in Social Sciences	Samhällsvetenskapliga hälso- och koststudier
	# <option value="50909">(50909) Environmental Studies in Social Sciences	Miljövetenskapliga studier inom samhällsvetenskap
	# <option value="50910">(50910) Child and Youth Studies			Barn- och ungdomsvetenskap
	# <option value="50911">(50911) War, Crisis, and Security Studies	Krigs-, kris-, säkerhetsvetenskaper
	# <option value="50912">(50912) Science and Technology Studies		Teknik och samhälle
	# <option value="50999">(50999) Other Social Sciences not elsewhere specified	Övrig annan samhällsvetenskap
	# <option value="6">(6) Humanities and the Arts				Humaniora och konst
	# <option value="601">(601) History and Archaeology			Historia och arkeologi
	# <option value="60101">(60101) History					Historia
	# <option value="60102">(60102) Technology and Environmental History	Teknik- och miljöhistoria
	# <option value="60103">(60103) Archaeology				Arkeologi
	# <option value="60104">(60104) History of Science and Ideas		Idé- och lärdomshistoria
	# <option value="60105">(60105) Classical Archaeology and Ancient History	Antikvetenskap
	# <option value="602">(602) Languages and Literature			Språk och litteratur
	# <option value="60201">(60201) Comparative Language Studies and Linguistics	Jämförande språkvetenskap och allmän lingvistik
	# <option value="60202">(60202) Studies of Specific Languages		Studier av enskilda språk
	# <option value="60203">(60203) General Literary&nbsp;studies		Litteraturvetenskap
	# <option value="60204">(60204) Studies of Specific Literatures		Litteraturstudier
	# <option value="60205">(60205) Philology				Filologi
	# <option value="60206">(60206) Translation Studies			Översättningsvetenskap
	# <option value="60207">(60207) Rhetoric				Retorik
	# <option value="603">(603) Philosophy, Ethics and Religion		Filosofi, etik och religion
	# <option value="60301">(60301) Philosophy				Filosofi
	# <option value="60302">(60302) Ethics					Etik
	# <option value="60303">(60303) Religious Studies			Religionsvetenskap
	# <option value="60304">(60304) History of Religions			Religionshistoria
	# <option value="60306">(60306) Aesthetics				Estetik
	# <option value="604">(604) Arts					Konst
	# <option value="60407">(60407) Art History				Konstvetenskap
	# <option value="60408">(60408) Musicology				Musikvetenskap
	# <option value="60409">(60409) Performing Art Studies		Teatervetenskap
	# <option value="60410">(60410) Film Studies				Filmvetenskap
	# <option value="60411">(60411) Visual Arts				Fri Konst
	# <option value="60412">(60412) Music					Musik
	# <option value="60413">(60413) Literary Composition			Litterär gestaltning
	# <option value="60414">(60414) Performing Arts				Scenkonst
	# <option value="60415">(60415) Architecture				Arkitektur
	# <option value="60416">(60416) Design					Design
	# <option value="60417">(60417) Film					Film
	# <option value="60418">(60418) Crafts					Konsthantverk
	# <option value="60419">(60419) Photography				Fotografi
	# <option value="605">(605) Other Humanities				Annan humaniora och konst
	# <option value="60502">(60502) Cultural Studies			Kulturstudier
        # <option value="60503">(60503) Ethnology				Etnologi
	# <option value="60504">(60504) Interdisciplinary Studies in Humanities and Arts	Tvärdiciplinära studier i humaniora och konst
	# <option value="60599">(60599) Other Humanities not elsewhere specified</select>	Övrig annan humaniora

    if False:
        print(f"\nget_records_json('validationType')")
        recs=get_records_json('validationType')
        if Verbose_Flag:
            print(f"{recs=}")
        pprint.pprint(recs, width=120)

    print(f"\nget_record_json('validationType', 'diva_degree-project')")
    recs=get_record_json('validationType', 'diva_degree-project')
    if Verbose_Flag:
        print(f"{recs=}")
    pprint.pprint(recs, width=120)

    # metadata/degreeProjectNewGroup
    print(f"\nget_record_json('metadata', 'degreeProjectNewGroup')")
    recs=get_record_json('metadata', 'degreeProjectNewGroup')
    if Verbose_Flag:
        print(f"{recs=}")
    pprint.pprint(recs, width=120)

    for al in recs['record']['actionLinks']:
        print(f"action link: {al}")

    for d in recs['record']['data']:
        print(f"{type(d)} data: {d}")
    print(f"type: {recs['record']['data']['attributes']['type']}")
    print(f"name: {recs['record']['data']['name']}")
    for c in recs['record']['data']['children']:
        if c.get('name'):
            print(f"\tname: {c.get('name')} {c.get('value')}")
        if c.get('children'):
            for gc in c['children']:
                if gc.get('name'):
                    print(f"\t\tname: {gc.get('name')} {gc.get('value')} {gc.get('repeatId')}")
                if gc.get('children'):
                    for ggc in gc['children']:
                        if ggc.get('name'):
                            print(f"\t\t\tname: {ggc.get('name')}  {ggc.get('value')}")
                        if ggc.get('children'):
                            for gggc in ggc['children']:
                                if gggc.get('name'):
                                    print(f"\t\t\t\tname: {gggc.get('name')} {gggc.get('value')}")

            
        # else:
        #     print(f"{d} is unexpected")

    print(f"\nget_record_json('validationType', 'diva-journal')")
    recs=get_record_json('validationType', 'diva-journal')
    if Verbose_Flag:
        print(f"{recs=}")
    pprint.pprint(recs, width=120)


    m='namePersonalAuthorGroup'
    print(f"\nget_record_json('metadata', {m})")
    recs=get_record_json('metadata', m)
    if Verbose_Flag:
        print(f"{recs=}")
    pprint.pprint(recs, width=120)

    m='titleInfoLangGroup'
    print(f"\nget_record_json('metadata', {m})")
    recs=get_record_json('metadata', m)
    if Verbose_Flag:
        print(f"{recs=}")
    pprint.pprint(recs, width=120)


    m='langCollectionVar'
    print(f"\nget_record_json('metadata', {m})")
    recs=get_record_json('metadata', m)
    if Verbose_Flag:
        print(f"{recs=}")
    pprint.pprint(recs, width=120)

    languageCollectionDict=dict()
    languageCollectionDictLang=dict()

    m='languageCollection'
    print(f"\nget_record_json('metadata', {m})")
    recs=get_record_json('metadata', m)
    if Verbose_Flag:
        print(f"{recs=}")
        pprint.pprint(recs, width=120)
    rdc=recs['record']['data']['children']
    for rdm in rdc:
        if rdm['name'] == 'collectionItemReferences':
            for gc in rdm['children']:
                rid=gc.get('repeatId')
                for ggc in gc['children']:
                    if ggc['name'] == 'linkedRecordId':
                            languageCollectionDict[ggc['value']]=rid
    print(f"{languageCollectionDict=}")


    for m in languageCollectionDict:
        if Verbose_Flag:
            print(f"\nget_record_json('metadata', {m})")
        recs=get_record_json('metadata', m)
        if Verbose_Flag:
            print(f"{recs=}")
            pprint.pprint(recs, width=120)
        t=get_languageItemTextId(recs)
        if Verbose_Flag:
            print(f"{t}")

        if Verbose_Flag:
            print(f"\nget_record_json('text', {t})")
        recs=get_record_json('text', t)
        if Verbose_Flag:
            print(f"{recs=}")
            pprint.pprint(recs, width=120)
        cid, text_lang_name= get_languageItemText(recs)
        if Verbose_Flag:
            print(f"{cid} {text_lang_name}")
        languageCollectionDictLang[m]={'cid': cid, 'names': text_lang_name}

    print(f"{languageCollectionDictLang=}")

    # t='sweLangItemText'
    # print(f"\nget_record_json('text', {t})")
    # recs=get_record_json('text', t)
    # if True or Verbose_Flag:
    #     print(f"{recs=}")
    #     pprint.pprint(recs, width=120)
    #     cid, text_lang_name= get_languageItemText(recs)
    #     print(f"{cid} {text_lang_name}")
    Verbose_Flag=False
    records_to_delete = ['diva-journal:22032485904726285', 'diva-journal:22032485904207272', 'diva-journal:22032485903647429', 'diva-journal:22032485904252629', 'diva-journal:22032485903712357']
    if False:
        for rec in records_to_delete:
            delete_a_record('diva-journal', rec)



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
    global Verbose_Flag
    global json_dict
    if Verbose_Flag:
        print(f"entering output(root)")

    artisticWork = ET.SubElement(root, "artisticWork", type="outputType") 
    artisticWork.text = "true"  
    language = ET.SubElement(root, "language", repeatId="0")
    ET.SubElement(language, "languageTerm", authority="iso639-2b", type="code").text = json_dict['Title']['Language']
    #ET.SubElement(root, "note", type="publicationStatus").text = "accepted"  
    #ET.SubElement(root, "genre", type="contentType").text = "ref"
    #ET.SubElement(root, "genre", type="reviewed").text = "refereed"
    #ET.SubElement(root, "typeOfResource").text = "movingImage"
    #titleInfo = ET.SubElement(root, "titleInfo", lang="swe")
    titleInfo = ET.SubElement(root, "titleInfo", lang=json_dict['Title']['Language'])
    ET.SubElement(titleInfo, "title").text = json_dict['Title']['Main title']
    subtitle=json_dict['Title'].get('Subtitle')
    if subtitle:
        ET.SubElement(titleInfo, "subTitle").text = subtitle
    alt_title=json_dict.get('Alternative title')
    if alt_title:
        titleInfo_alt = ET.SubElement(root, "titleInfo", lang=alt_title['Language'], repeatId="1", type="alternative")
        ET.SubElement(titleInfo_alt, "title").text = alt_title['Main title']
        alt_subtitle=alt_title.get('Subtitle')
        if alt_subtitle:
            ET.SubElement(titleInfo_alt, "subTitle").text = alt_subtitle
    author1=json_dict['Author1']
    author2=json_dict.get('Author2')
    name_personal = ET.SubElement(root, "name", repeatId="2", type="personal")
    person = ET.SubElement(name_personal, "person")
    ET.SubElement(person, "linkedRecordType").text = "diva-person"
    ET.SubElement(person, "linkedRecordId").text = "444"
    name_corporate = ET.SubElement(root, "name", repeatId="3", type="corporate")
    organisation = ET.SubElement(name_corporate, "organisation")
    ET.SubElement(organisation, "linkedRecordType").text = "diva-organisation"
    ET.SubElement(organisation, "linkedRecordId").text = "diva-organisation:1530219071900116" 
    ET.SubElement(root, "note", type="creatorCount").text = "1"

    # abstracts
    eng_abstract="""An abstract is (typically) about 250 and 350 words (1/2 A4-page) with the following components:\n% key parts of the abstract\n\begin{itemize}\n\item What is the topic area? (optional) Introduces the subject area for the project.\n\item Short problem statement\n\item Why was this problem worth a third-cycle thesis? (\ie why is the problem both significant and of a suitable degree of difficulty for your intended degree? Why has no one else solved it yet?)\n\item How did you solve the problem? What was your method/insight?\n\item Results/Conclusions/Consequences/Impact: What are your key results/\linebreak[4]conclusions? What will others do based on your results? What can be done now that you have finished - that could not be done before your thesis project was completed?\end{itemize}\n"""
    ET.SubElement(root, "abstract", lang="eng", repeatId="4").text = eng_abstract

    eng_keywords="Canvas Learning Management System, Docker containers, Performance tuning"
    subject = ET.SubElement(root, "subject", lang="end", repeatId="5")
    ET.SubElement(subject, "topic").text = eng_keywords
    ET.SubElement(root, "classification", authority="ssif", repeatId="6").text = "10201"
    subject_diva = ET.SubElement(root, "subject", authority="diva")  
    topic_diva = ET.SubElement(subject_diva, "topic", repeatId="7")  
    ET.SubElement(topic_diva, "linkedRecordType").text = "diva-subject" 
    ET.SubElement(topic_diva, "linkedRecordId").text = "diva-subject:1437069069944102" 

    #subject_sdg = ET.SubElement(root, "subject", authority="sdg")
    #ET.SubElement(subject_sdg, "topic", repeatId="8").text = "sdg3"

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
    ET.SubElement(place, "placeTerm").text = "Stockholm" 
    #ET.SubElement(originInfo, "edition").text = "2" 
    #ET.SubElement(root, "note", type="external").text = "Extern anteckning om resursen (synlig publikt)" 
    #location = ET.SubElement(root, "location", repeatId="11") 
    #ET.SubElement(location, "url").text = "url.se" 
    #ET.SubElement(location, "displayLabel").text = "En länktext" 
    #ET.SubElement(root, "identifier", type="doi").text = "10.1000/182" 
    #ET.SubElement(root, "identifier", repeatId="12", type="localId").text = "Valfritt lokalt ID här" 
    #ET.SubElement(root, "identifier", type="archiveNumber").text = "345435" 
    #ET.SubElement(root, "identifier", type="patentNumber").text = "234324" 
    #ET.SubElement(root, "identifier", type="pmid").text = "10097079" 
    #ET.SubElement(root, "identifier", type="wos").text = "56565675" 
    #ET.SubElement(root, "identifier", type="scopus").text = "2-s2.0-12" 
    #ET.SubElement(root, "identifier", type="openAlex").text = "Open Alex ID" 
    #ET.SubElement(root, "identifier", type="se-libr").text = "1234ABcd" 
    #ET.SubElement(root, "identifier", type="isrn").text = "4567867687" 
    #ET.SubElement(root, "identifier", displayLabel="print", repeatId="13", type="isbn").text = "3880531013" 
    #ET.SubElement(root, "identifier", displayLabel="print", repeatId="14", type="ismn").text = "9790060115615"
    ET.SubElement(root, "extent").text = "355 sidor"
    physicalDescription = ET.SubElement(root, "physicalDescription")

    other_information=json_dict['Other information']

    ET.SubElement(physicalDescription, "extent").text = json_dict['Other information']['Number of pages']
    #dateOther_patent = ET.SubElement(root, "dateOther", type="patent") 
    #ET.SubElement(dateOther_patent, "year").text = "2022" 
    #ET.SubElement(dateOther_patent, "month").text = "12" 
    #ET.SubElement(dateOther_patent, "day").text = "04" 
    #ET.SubElement(root, "imprint").text = "Uppsala" 
    #academicSemester = ET.SubElement(root, "academicSemester") 
    #ET.SubElement(academicSemester, "year").text = "2023" 
    #ET.SubElement(academicSemester, "semester").text = "ht" 

    #
    #studentDegree = ET.SubElement(root, "studentDegree") 
    #ET.SubElement(studentDegree, "degreeLevel").text = "M2" 
    #ET.SubElement(studentDegree, "universityPoints").text = "10" 
    #course = ET.SubElement(studentDegree, "course") 
    #ET.SubElement(course, "linkedRecordType").text = "diva-course" 
    #ET.SubElement(course, "linkedRecordId").text = "444" 
    #programme = ET.SubElement(studentDegree, "programme") 
    #ET.SubElement(programme, "linkedRecordType").text = "diva-programme" 
    #ET.SubElement(programme, "linkedRecordId").text = "444" 
    #relatedItem_conference = ET.SubElement(root, "relatedItem", type="conference") 
    #titleInfo_conference = ET.SubElement(relatedItem_conference, "titleInfo", lang="swe") 
    #ET.SubElement(titleInfo_conference, "title").text = "Huvudtitel för konferens" 
    #ET.SubElement(titleInfo_conference, "subTitle").text = "Undertitel för konferens" 
    #relatedItem_series = ET.SubElement(root, "relatedItem", repeatId="15", type="series") 
    #series = ET.SubElement(relatedItem_series, "series") 
    #ET.SubElement(series, "linkedRecordType").text = "diva-series" 
    #ET.SubElement(series, "linkedRecordId").text = "diva-series:1437068740596935"
    #relatedItem_journal = ET.SubElement(root, "relatedItem", type="journal") 
    #journal = ET.SubElement(relatedItem_journal, "journal") 
    #ET.SubElement(journal, "linkedRecordType").text = "diva-journal" 
    #ET.SubElement(journal, "linkedRecordId").text = "444" 
    #relatedItem_book = ET.SubElement(root, "relatedItem", type="book") 
    #titleInfo_book = ET.SubElement(relatedItem_book, "titleInfo", lang="swe") 
    #ET.SubElement(titleInfo_book, "title").text = "Huvudtitel för bok" 
    # ET.SubElement(titleInfo_book, "subTitle").text = "Undertitel för bok" 
    # ET.SubElement(relatedItem_book, "note", type="statementOfResponsibility").text = "Redaktör för bok" 
    # originInfo_book = ET.SubElement(relatedItem_book, "originInfo") 
    # dateIssued_book = ET.SubElement(originInfo_book, "dateIssued") 
    # ET.SubElement(dateIssued_book, "year").text = "2021" 
    # ET.SubElement(dateIssued_book, "month").text = "12" 
    # ET.SubElement(dateIssued_book, "day").text = "03" 
    # copyrightDate_book = ET.SubElement(originInfo_book, "copyrightDate") 
    # ET.SubElement(copyrightDate_book, "year").text = "2021" 
    # ET.SubElement(copyrightDate_book, "month").text = "11" 
    # ET.SubElement(copyrightDate_book, "day").text = "05" 
    # dateOther_book = ET.SubElement(originInfo_book, "dateOther", type="online") 
    # ET.SubElement(dateOther_book, "year").text = "2021" 
    # ET.SubElement(dateOther_book, "month").text = "10" 
    # ET.SubElement(dateOther_book, "day").text = "04" 
    # agent_book = ET.SubElement(originInfo_book, "agent") 
    # publisher_book = ET.SubElement(agent_book, "publisher", repeatId="16") 
    # ET.SubElement(publisher_book, "linkedRecordType").text = "diva-publisher" 
    # ET.SubElement(publisher_book, "linkedRecordId").text = "diva-publisher:1437068056503025" 
    # role_book = ET.SubElement(agent_book, "role") 
    # ET.SubElement(role_book, "roleTerm").text = "pbl" 
    # place_book = ET.SubElement(originInfo_book, "place", repeatId="17") 
    # ET.SubElement(place_book, "placeTerm").text = "Uppsala" 
    # ET.SubElement(originInfo_book, "edition").text = "2" 
    # ET.SubElement(relatedItem_book, "identifier", displayLabel="print", repeatId="18", type="isbn").text = "3880531013" 
    # part_book = ET.SubElement(relatedItem_book, "part") 
    # extent_book = ET.SubElement(part_book, "extent") 
    # ET.SubElement(extent_book, "start").text = "1" 
    # ET.SubElement(extent_book, "end").text = "350" 
    # relatedItem_series_book = ET.SubElement(relatedItem_book, "relatedItem", repeatId="19", type="series") 
    # series_book = ET.SubElement(relatedItem_series_book, "series") 
    # ET.SubElement(series_book, "linkedRecordType").text = "diva-series" 
    # ET.SubElement(series_book, "linkedRecordId").text = "diva-series:1437068740596935" 
    # relatedItem_conferencePublication = ET.SubElement(root, "relatedItem", type="conferencePublication") 
    # titleInfo_conferencePublication = ET.SubElement(relatedItem_conferencePublication, "titleInfo", lang="swe") 
    # ET.SubElement(titleInfo_conferencePublication, "title").text = "Huvudtitel för proceeding" 
    # ET.SubElement(titleInfo_conferencePublication, "subTitle").text = "Undertitel för proceeding" 
    # ET.SubElement(relatedItem_conferencePublication, "note", type="statementOfResponsibility").text = "Redaktör för proceeding" 
    # originInfo_conferencePublication = ET.SubElement(relatedItem_conferencePublication, "originInfo") 
    # dateIssued_conferencePublication = ET.SubElement(originInfo_conferencePublication, "dateIssued") 
    # ET.SubElement(dateIssued_conferencePublication, "year").text = "2022" 
    # ET.SubElement(dateIssued_conferencePublication, "month").text = "12" 
    # ET.SubElement(dateIssued_conferencePublication, "day").text = "04" 
    # copyrightDate_conferencePublication = ET.SubElement(originInfo_conferencePublication, "copyrightDate") 
    # ET.SubElement(copyrightDate_conferencePublication, "year").text = "2022" 
    # ET.SubElement(copyrightDate_conferencePublication, "month").text = "10" 
    # ET.SubElement(copyrightDate_conferencePublication, "day").text = "01" 
    # dateOther_conferencePublication = ET.SubElement(originInfo_conferencePublication, "dateOther", type="online") 
    # ET.SubElement(dateOther_conferencePublication, "year").text = "2021" 
    # ET.SubElement(dateOther_conferencePublication, "month").text = "10" 
    # ET.SubElement(dateOther_conferencePublication, "day").text = "02" 
    # agent_conferencePublication = ET.SubElement(originInfo_conferencePublication, "agent") 
    # publisher_conferencePublication = ET.SubElement(agent_conferencePublication, "publisher", repeatId="20") 
    # ET.SubElement(publisher_conferencePublication, "linkedRecordType").text = "diva-publisher" 
    # ET.SubElement(publisher_conferencePublication, "linkedRecordId").text = "diva-publisher:1437068056503025" 
    # role_conferencePublication = ET.SubElement(agent_conferencePublication, "role") 
    # ET.SubElement(role_conferencePublication, "roleTerm").text = "pbl" 
    # place_conferencePublication = ET.SubElement(originInfo_conferencePublication, "place", repeatId="21") 
    # ET.SubElement(place_conferencePublication, "placeTerm").text = "Uppsala" 
    # ET.SubElement(originInfo_conferencePublication, "edition").text = "3" 
    # ET.SubElement(relatedItem_conferencePublication, "identifier", displayLabel="online", repeatId="22", type="isbn").text = "3880531015" 
    # part_conferencePublication = ET.SubElement(relatedItem_conferencePublication, "part") 
    # extent_conferencePublication = ET.SubElement(part_conferencePublication, "extent") 
    # ET.SubElement(extent_conferencePublication, "start").text = "1" 
    # ET.SubElement(extent_conferencePublication, "end").text = "350"
    # relatedItem_series_conferencePublication = ET.SubElement(relatedItem_conferencePublication, "relatedItem", repeatId="23", type="series") 
    # series_conferencePublication = ET.SubElement(relatedItem_series_conferencePublication, "series") 
    # ET.SubElement(series_conferencePublication, "linkedRecordType").text = "diva-series" 
    # ET.SubElement(series_conferencePublication, "linkedRecordId").text = "diva-series:1437068740596935" 
    # relatedItem_funder = ET.SubElement(root, "relatedItem", repeatId="24", type="funder") 
    # funder = ET.SubElement(relatedItem_funder, "funder") 
    # ET.SubElement(funder, "linkedRecordType").text = "diva-funder" 
    # ET.SubElement(funder, "linkedRecordId").text = "diva-funder:1437067710216461" 
    # relatedItem_initiative = ET.SubElement(root, "relatedItem", type="initiative") 
    # ET.SubElement(relatedItem_initiative, "initiative", repeatId="25").text = "diabetes" 
    # relatedItem_project = ET.SubElement(root, "relatedItem", type="project") 
    # project = ET.SubElement(relatedItem_project, "project") 
    # ET.SubElement(project, "linkedRecordType").text = "diva-project" 
    # ET.SubElement(project, "linkedRecordId").text = "444" 
    # relatedItem_researchData = ET.SubElement(root, "relatedItem", repeatId="26", type="researchData") 
    # titleInfo_researchData = ET.SubElement(relatedItem_researchData, "titleInfo", lang="swe") 
    # ET.SubElement(titleInfo_researchData, "title").text = "Huvudtitel forskningsdata" 
    # ET.SubElement(titleInfo_researchData, "subTitle").text = "Undertitel forskningsdata" 
    # ET.SubElement(relatedItem_researchData, "identifier", type="doi").text = "10.1000/182" 
    # location_researchData = ET.SubElement(relatedItem_researchData, "location", repeatId="27") 
    # ET.SubElement(location_researchData, "url").text = "url.se" 
    # ET.SubElement(location_researchData, "displayLabel").text = "En länktext"
    # related = ET.SubElement(root, "related", repeatId="28", type="constituent")
    # output = ET.SubElement(related, "output", repeatId="29")
    # ET.SubElement(output, "linkedRecordType").text = "diva-output"
    # ET.SubElement(output, "linkedRecordId").text = "diva-output:1523950164148129"
    # degree_granting_institution = ET.SubElement(root, "degreeGrantingInstitution", type="corporate")
    # organisation = ET.SubElement(degree_granting_institution, "organisation")
    # ET.SubElement(organisation, "linkedRecordType").text = "diva-organisation"
    # ET.SubElement(organisation, "linkedRecordId").text = "diva-organisation:1530219071900116"
    # role = ET.SubElement(degree_granting_institution, "role")
    # ET.SubElement(role, "roleTerm").text = "dgg"
    # relatedItem_defence = ET.SubElement(root, "relatedItem", type="defence") 
    # dateOther_defence = ET.SubElement(relatedItem_defence, "dateOther", type="defence") 
    # ET.SubElement(dateOther_defence, "year").text = "1988" 
    # ET.SubElement(dateOther_defence, "month").text = "11" 
    # ET.SubElement(dateOther_defence, "day").text = "01" 
    # ET.SubElement(dateOther_defence, "hh").text = "10" 
    # ET.SubElement(dateOther_defence, "mm").text = "30" 
    # ET.SubElement(relatedItem_defence, "location").text = "En plats för disputationen" 
    # ET.SubElement(relatedItem_defence, "address").text = "Doktorsgatan 5" 
    # place_defence = ET.SubElement(relatedItem_defence, "place") 
    # ET.SubElement(place_defence, "placeTerm").text = "Uppsala" 
    # language_defence = ET.SubElement(relatedItem_defence, "language") 
    # ET.SubElement(language_defence, "languageTerm", authority="iso639-2b", type="code").text = "swe" 
    # ET.SubElement(root, "accessCondition", authority="kb.se").text = "gratis" 
    # localGenericMarkup = ET.SubElement(root, "localGenericMarkup", repeatId="30") 
    # ET.SubElement(localGenericMarkup, "linkedRecordType").text = "diva-localGenericMarkup" 
    # ET.SubElement(localGenericMarkup, "linkedRecordId").text = "444" 
    # admin = ET.SubElement(root, "admin") 
    # ET.SubElement(admin, "reviewed").text = "true" 
    # adminInfo = ET.SubElement(root, "adminInfo") 
    # ET.SubElement(adminInfo, "visibility").text = "published" 
    # location_orderLink = ET.SubElement(root, "location", displayLabel="orderLink") 
    # ET.SubElement(location_orderLink, "url").text = "url.se" 
    # ET.SubElement(location_orderLink, "displayLabel").text = "En länktext" 



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

# basic url for record
basic_urls = {
    "preview": 'https://cora.epc.ub.uu.se/diva/rest/record/',
    "pre": 'https://pre.diva-portal.org/rest/record/',
    "dev": 'http://130.238.171.238:38082/diva/rest/record/',
}

# create the record and post
def create(root, record_type):
    global Verbose_Flag
    if Verbose_Flag:
        print(f"entering create(root, {record_type})")

    xml_headers = {'Content-Type':'application/vnd.cora.record+xml', 'Accept':'application/vnd.cora.record+xml', 'authToken': app_token_client.get_auth_token()}
    #print(xml_headers)
    output_str = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"+ET.tostring(root).decode("UTF-8")
    response = requests.post(f"{basic_urls[system]}{RECORDID_ENDPOINT[record_type]}", data=output_str, headers=xml_headers)
    print(f"{response.status_code=}, {response.text=}, {response.headers=}")
    print(output_str) # <-- visar i konsollen vad man skickar in vid en create
    #print(f"{basic_urls[system]}{RECORDID_ENDPOINT[record_type]}") #record_type
    #print(xml_headers)

# create chosen record
def createRecord(record_type):
    global Verbose_Flag
    if Verbose_Flag:
        print(f"entering createRecord({record_type})")
    id = '444444'
    root = ET.Element(record_type) # skapar ett root-element för xml:en
    recordInfo(id, root, record_type) # funktion som skapar recordInfo-delen
    output(root) # create a diva-output record
    create(root, record_type) # creates record and posts


def start():
    global data_logger
    global Verbose_Flag
    global json_dict

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

    if False:
        test_block1()

    # try creating a record
    Verbose_Flag=True
    createRecord('output')
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
    validate_headers_xml = {'Content-Type':'application/vnd.cora.workorder+xml',
                            'Accept':'application/vnd.cora.record+xml', 'authToken':auth_token}
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
    headersXml = {'Content-Type':'application/vnd.cora.record+xml',
                  'Accept':'application/vnd.cora.record+xml', 'authToken':auth_token}
    urlCreate = ConstantsData.BASE_URL[system] + recordType
    recordToCreate = new_record_build(data_record)
    #oldId_fromSource = CommonData.get_oldId(data_record)
    oldId_fromSource=None

    output = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + ET.tostring(recordToCreate).decode("UTF-8")
    response = requests.post(urlCreate, data=output, headers=headersXml)
#    print(response.status_code, response.text)
    if response.text:
        data_logger.info(f"{oldId_fromSource}: {response.status_code}. {response.text}")
    if response.status_code not in ([201]):
        data_logger.error(f"{oldId_fromSource}: {response.status_code}. {response.text}")
    return response.text


def main(argv):
    global Verbose_Flag
    global json_dict

    parser = optparse.OptionParser()

    parser.add_option('-v', '--verbose',
                      dest="verbose",
                      default=False,
                      action="store_true",
                      help="Print lots of output to stdout"
    )

    options, remainder = parser.parse_args()

    Verbose_Flag=options.verbose
    if Verbose_Flag:
        print('ARGV      :', sys.argv[1:])
        print('VERBOSE   :', options.verbose)
        print('REMAINING :', remainder)

    if (len(remainder) < 1):
        print("using default: fordiva-cleaned.json")
        json_filename='fordiva-cleaned.json'
    else:
        json_filename=remainder[0]

    if not json_filename:
        print("Unknown source for the JSON: {}".format(json_filename))
        return

    json_dict=dict()

    try:
        with open(json_filename, 'r', encoding='utf-8') as json_FH:
            json_string=json_FH.read()
            json_dict=json.loads(json_string)
    except FileNotFoundError:
        print("File not found: {json_filename}".format(json_filename))
        return

    if Verbose_Flag:
        print("read JSON: {}".format(json_dict))

    start()



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
