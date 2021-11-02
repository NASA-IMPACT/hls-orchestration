# hls-pr2mgrs

Landsat 8 PathRow to Sentinel 2 Tiles.

### Install

```
$ pip install pip -U
$ pip install .[deploy]
```

### Deploy

```
$ cd stack
$ cdk init && cdk deploy
```


### Lambda Invocation

The lambda handler accepts either `PATHROW` or `MGRS` argument passed in a dictionary

```python
from hls_pr2mgrs.handler import handler

>> handler({"PATHROW": "001001"}, {})
>> ['29XNK',
 '29XNL',
 '30XVQ',
 '30XVR',
 '30XWP',
 '30XWQ',
 '30XWR',
 '31XDJ',
 '31XDK',
 '31XDL',
 '31XEJ',
 '31XEK',
 '31XEL']

>> handler({"MGRS": "29XNK"}, {})
>> ['001001',
 '001002',
 '002001',
 '002002',
 '003001',
 '003002',
 '004001',
 '004002',
 '005001',
 '005002',
 '006001',
 '006002',
 '007001',
 '007002',
 '008001',
 '009001',
 '010001',
 '011001',
 '229003',
 '230002',
 '230003',
 '231002',
 '232002',
 '233002',
 '233003']
```
