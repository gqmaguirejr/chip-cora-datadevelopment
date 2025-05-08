# Experiments with the Cora API

This repository initially contained scripts for creating and migrating metadata.
It started as a copy of https://github.com/lsu-ub-uu/cora-datadevelopment/tree/master

I am using it to explore the Cora API in the hopes of being able to automate
putting metadata and PDF file(s) for degree projects into the new Cora base
DiVA.

## get_user_info.py

# Purpose
Using journal_create.py as a base, modified it to get user information
to explore the record user part of the API. This was also a chance to try
getting an authentication token and use it for something that failed when I
did not have an authentication token.

Input:
```
./get_user_info.py
```

Output:
```
made it to start()
<authtoken>
response.status_code=200
len(user_info_xml)=190454
top level tag: dataList root=<Element 'dataList' at 0x7fd319ec9530>
fromNo='0' toNo='19' totalNo='19'
{'type': 'systemOneUser'}
<type>	user_id='<user_id>'	login_id='x@y'	userFirstname='xxxx'	userLastname='yyyyy'
...

```
