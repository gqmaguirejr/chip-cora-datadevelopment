class  CoraData:
    @staticmethod
    def findChildWithNameInData(childrenList, nameInData):
        for child in childrenList:
            childNameInData = child['name']
            if childNameInData == nameInData:
                return child
        return None
        
    @staticmethod
    def getValueWithNameInData(specificChild):
        if specificChild is not None:
            childValue = specificChild['value']
            return childValue
        return None

    @staticmethod
    def getFirstAtomicValueWithNameInData(childrenList, nameInData):
        specificChild = CoraData.findChildWithNameInData(childrenList, nameInData)
        childValue = CoraData.getValueWithNameInData(specificChild)
        return childValue

    @staticmethod
    def appendValueToList(childValue, element, list):
        if childValue is not None:
            list.append(element)

    @staticmethod
    def getOrganisationNameValueWithNameInData(childrenList, nameInData): # borde kunna vara samma som nedan
        specificChild = CoraData.findChildWithNameInData(childrenList, nameInData)
        specificChildsChildren = CoraData.findChildWithNameInData(specificChild['children'], 'name')
        return specificChildsChildren['value']

    @staticmethod
    def getLinkedRecordIdWithNameInData(dataChildren, nameInData): # borde kunna vara samma som ovan
        linkedChild = CoraData.findChildWithNameInData(dataChildren, nameInData) 
        linkedRecordId = CoraData.findChildWithNameInData(linkedChild['children'], 'linkedRecordId')
        return linkedRecordId['value']

    @staticmethod
    def getValidationTypeLink(recordInfoChildren):
        validationType = CoraData.getLinkedRecordIdWithNameInData(recordInfoChildren, 'type')
        # newValidationType = checkValidationTypeLinkAndGetNewValue(validationType)
        return validationType

    @staticmethod
    def getParentEarlierLinks(recordChildren, typeOfOrganisationLink): # BYT UT RECORDCHILDREN TILL RESPONSE_RECORD
        linkedId = []
        for organisationLink in recordChildren:
            childNameInData = organisationLink['name']
            if childNameInData == typeOfOrganisationLink:
                organisationLinkValue = CoraData.findChildWithNameInData(organisationLink['children'], 'organisationLink') 
                linkedRecordId = CoraData.findChildWithNameInData(organisationLinkValue['children'], 'linkedRecordId')
                linkedId.append(linkedRecordId['value'])
        return linkedId 