class  ConstantsData:
    LOGIN_URLS = {
        'local': 'http://localhost:8182/login/rest/apptoken',
        'preview': 'https://cora.epc.ub.uu.se/diva/login/rest/apptoken',
        'mig': 'https://mig.diva-portal.org/login/rest/apptoken',
        'pre': 'https://pre.diva-portal.org/login/rest/apptoken',
    }
    BASE_URL = {
        "local": "http://localhost:8082/diva/rest/record/",
        "preview": "https://cora.epc.ub.uu.se/diva/rest/record/",
        "dev": "http://130.238.171.238:38082/diva/rest/record/",
        "pre": "https://pre.diva-portal.org/rest/record/",
        "mig": "https://mig.diva-portal.org/rest/record/"
    } 