from flask import Blueprint, request, current_app
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog
from datetime import date

logger = createLog(__name__)

citation = Blueprint('citation', __name__, url_prefix='/citation')

citationSet = {'mla', 'apa', 'chicago'}

@citation.route('/<uuid>', methods=['GET'])
def citationFetch(uuid):
    logger.info('Fetching Identifier {}'.format(uuid))

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    searchParams = APIUtils.normalizeQueryParams(request.args)
    logger.debug(searchParams)

    citeFormats = request.args.get('format') #Default value is None if no arguments set
    formatList = citeFormats.split(',')
    formatListSet = set(formatList)
    logger.debug(formatListSet)

    if formatListSet.issubset(citationSet) == False:
        logger.warning('Page not found')
        return APIUtils.formatResponseObject(
                400, 'pageNotFound', {'message': 'Need to specify citation format'}
            )

    citationWork = dbClient.fetchSingleWork(uuid)
    
    outputCitations = {}

    for format in formatListSet:
        logger.info("Do formatting here")
        if format == 'mla':
            newCite = mlaGenerator(citationWork)
        outputCitations[format] = newCite

    if citationWork:
        statusCode = 200
        responseBody = outputCitations
    else:
        statusCode = 404
        responseBody = {
            'message': f'Unable to locate work with UUID {uuid}'
        }

    logger.info(f'Citation Fetch {statusCode} on /citation/{uuid}')

    dbClient.closeSession()

    return APIUtils.formatResponseObject(
        statusCode, 'citation', responseBody
    )

def mlaGenerator(citationWork):
    if citationWork:
        if citationWork.title == "The Bible":
            return mlaBibleGenerator(citationWork)

        elif citationWork.editions[0].measurements:
            if citationWork.editions[0].measurements[0] == {"type": "government_document", "value": "1"}:
                return mlaGovGenerator(citationWork)

        elif len(citationWork.authors) == 0:
            return mlaNoAuthorGenerator(citationWork)

        elif len(citationWork.authors) == 1:
            return mlaOneAuthorGenerator(citationWork)

        elif len(citationWork.authors) == 2:
            return mlaTwoAuthorsGenerator(citationWork)

        elif len(citationWork.authors) == 3:
            return mlaThreeAuthorsGenerator(citationWork)
            
        else:
            return "MLA Citation not avaliable"
    else:
        return "MLA Citation not avaliable"

def mlaBibleGenerator(citationWork):
    #Bible editions before 1900
        #Specific version info of Bible currently not displayed in database
    if citationWork.editions[0].publication_date < date(1900, 1, 1):
        citationResponse = f"{citationWork.title}. Unknown version, \
                            {citationWork.editions[0].publication_place}, \
                            {citationWork.editions[0].publication_date}."
            
        return ' '.join(citationResponse.split())

    #Bible editions during and after 1900
        #Specific version info of Bible currently not displayed in database
    else:      
        citationResponse = f"{citationWork.title}. Unknown version, \
                            {citationWork.editions[0].publishers[0]['name']}, \
                            {citationWork.editions[0].publication_date}."
            
        return ' '.join(citationResponse.split())

def mlaGovGenerator(citationWork):
    #Government Publications before 1900
    if citationWork.editions[0].publication_date < date(1900, 1, 1):

        govName = citationWork.authors[0]['name']
        govNameAndAgency = govName.replace('.', ',', 1)

        citationResponse = f"{govNameAndAgency} \
                    {citationWork.title}. \
                    {citationWork.editions[0].publishers[0]['name']}, \
                    {citationWork.editions[0].publication_date}."
            
        return ' '.join(citationResponse.split())

    else:

        govName = citationWork.authors[0]['name']
        govNameAndAgency = govName.replace('.', ',', 1)

        citationResponse = f"{govNameAndAgency} \
                            {citationWork.title}. \
                            {citationWork.editions[0].publication_place}, \
                            {citationWork.editions[0].publication_date}."
            
        return ' '.join(citationResponse.split())

def mlaNoAuthorGenerator(citationWork):
    #Translated works/works prepared by editors before 1900
    if citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.contributors:

        i = 0
        transName = ''
        editorName = ''

        while i < len(citationWork.contributors):
            if citationWork.contributors[i]['roles'] == 'translator':
                transName = citationWork.contributors[i]['roles']
            if citationWork.contributors[i]['roles'] == 'editor':
                editorName = citationWork.contributors[i]['roles']
            i += 1
        
        if transName and editorName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]

            citationResponse = f"{citationWork.title}. \
                    translated by {transFirstName} {transLastName}, \
                    edited by {editorFirstName} {editorLastName}, {citationWork.editions[0].publication_place}, \
                    {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
                    
        if transName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            citationResponse = f"{citationWork.title}. \
                    translated by {transFirstName} {transLastName}, {citationWork.editions[0].publication_place}, \
                    {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        if citationWork.contributors[i]['roles'] == 'editor':
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            citationResponse = f"{citationWork.title}, \
                edited by {editorFirstName} {editorLastName}, {citationWork.editions[0].publication_place}, \
                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

    #Translated works/works prepared by editors during or after 1900
    if citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.contributors:

        i = 0
        transName = ''
        editorName = ''

        while i < len(citationWork.contributors):
            if citationWork.contributors[i]['roles'] == 'translator':
                transName = citationWork.contributors[i]['roles']
            if citationWork.contributors[i]['roles'] == 'editor':
                editorName = citationWork.contributors[i]['roles']
            i += 1
        
        if transName and editorName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]

            citationResponse = f"{citationWork.title}. \
                                translated by {transFirstName} {transLastName}, \
                                edited by {editorFirstName} {editorLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
                    
        if transName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            citationResponse = f"{citationWork.title}. \
                                translated by {transFirstName} {transLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        if editorName:
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            citationResponse = f"{citationWork.title}, \
                                edited by {editorFirstName} {editorLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
    
            
    #Single edition books with no author before 1900
    if citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is None:

        citationResponse = f"{citationWork.title}. {citationWork.editions[0].publication_place}, \
                            {citationWork.editions[0].publication_date}."

        return ' '.join(citationResponse.split())
                
    #Multiple edition books with no author before 1900
    elif citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is not None:

        citationResponse = f"{citationWork.title}. {citationWork.edition_statement}, \
                            {citationWork.editions[0].publication_place}, \
                            {citationWork.editions[0].publication_date}."

        return ' '.join(citationResponse.split())

    #Single edition books with no author during and after 1900
    elif citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is None:

        citationResponse = f"{citationWork.title}. {citationWork.editions[0].publishers[0]['name']}, \
                            {citationWork.editions[0].publication_date}." 

        return ' '.join(citationResponse.split())

    #Multiple edition books with no author during and after 1900
    elif citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is not None:

        citationResponse = f"{citationWork.title}. {citationWork.edition_statement}, \
                            {citationWork.editions[0].publishers[0]['name']}, \
                            {citationWork.editions[0].publication_date}." 

        return ' '.join(citationResponse.split())

def mlaOneAuthorGenerator(citationWork):
    #Translated works/works prepared by editors before 1900
    if citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.contributors:

        i = 0
        transName = ''
        editorName = ''

        while i < len(citationWork.contributors):
            if citationWork.contributors[i]['roles'] == 'translator':
                transName = citationWork.contributors[i]['roles']
            if citationWork.contributors[i]['roles'] == 'editor':
                editorName = citationWork.contributors[i]['roles']
            i += 1
        
        if transName and editorName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            authName = citationWork.authors[0]['name']

            citationResponse = f"{authName}. {citationWork.title}. \
                    translated by {transFirstName} {transLastName}, \
                    edited by {editorFirstName} {editorLastName}, {citationWork.editions[0].publication_place}, \
                    {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
                    
        if transName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            authName = citationWork.authors[0]['name']
            citationResponse = f"{authName}. {citationWork.title}. \
                    translated by {transFirstName} {transLastName}, {citationWork.editions[0].publication_place}, \
                    {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        if citationWork.contributors[i]['roles'] == 'editor':
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            authName = citationWork.authors[0]['name']
            citationResponse = f"{authName}. {citationWork.title}, \
                edited by {editorFirstName} {editorLastName}, {citationWork.editions[0].publication_place}, \
                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

    #Translated works/works prepared by editors during or after 1900
    if citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.contributors:

        i = 0
        transName = ''
        editorName = ''

        while i < len(citationWork.contributors):
            if citationWork.contributors[i]['roles'] == 'translator':
                transName = citationWork.contributors[i]['roles']
            if citationWork.contributors[i]['roles'] == 'editor':
                editorName = citationWork.contributors[i]['roles']
            i += 1
        
        if transName and editorName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            authName = citationWork.authors[0]['name']

            citationResponse = f"{authName}. {citationWork.title}. \
                                translated by {transFirstName} {transLastName}, \
                                edited by {editorFirstName} {editorLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
                    
        if transName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            citationResponse = f"{authName}. {citationWork.title}. \
                                translated by {transFirstName} {transLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        if editorName:
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            citationResponse = f"{authName}. {citationWork.title}, \
                                edited by {editorFirstName} {editorLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())


    #Single edition books with one author before 1900
    elif citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is None:

        authName = citationWork.authors[0]['name']

        #Book by corporate author or organization
        if authName == citationWork.editions[0].publishers[0]['name']:
            citationResponse = f"{citationWork.title}. \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_place}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        else:   
            citationResponse = f"{authName}. {citationWork.title}. \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_place} \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

    #Multiple edition books with one author before 1900
    elif citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is not None:

        authName = citationWork.authors[0]['name']

        #Book by corporate author or organization
        if authName == citationWork.editions[0].publishers[0]['name']:
            citationResponse = f"{citationWork.title}. {citationWork.edition_statement}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_place}, \
                                {citationWork.editions[0].publication_date}."
            return ' '.join(citationResponse.split())

        else:   
            citationResponse = f"{authName}. {citationWork.title}. {citationWork.edition_statement}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_place} \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
    
        
    #Single edition books with one author during and after 1900
    elif citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is None:
        
        authName = citationWork.authors[0]['name']

        #Book by corporate author or organization
        if authName == citationWork.editions[0].publishers[0]['name']:
            citationResponse = f"{citationWork.title}. \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."
            return ' '.join(citationResponse.split())

        else:   
            citationResponse = f"{authName}. {citationWork.title}. \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."
            return ' '.join(citationResponse.split())

    #Multiple Edition books with one author during and after 1900
    elif citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is not None:

        authName = citationWork.authors[0]['name']

        #Book by corporate author or organization
        if authName == citationWork.editions[0].publishers[0]['name']:
            citationResponse = f"{citationWork.title}. {citationWork.edition_statement} \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."
            return ' '.join(citationResponse.split())

        else:   
            citationResponse = f"{authName}. {citationWork.title}. {citationWork.edition_statement} \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."
            return ' '.join(citationResponse.split())

def mlaTwoAuthorsGenerator(citationWork):
    #Translated works/works prepared by editors before 1900
    if citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.contributors:

        i = 0
        transName = ''
        editorName = ''

        while i < len(citationWork.contributors):
            if citationWork.contributors[i]['roles'] == 'translator':
                transName = citationWork.contributors[i]['roles']
            if citationWork.contributors[i]['roles'] == 'editor':
                editorName = citationWork.contributors[i]['roles']
            i += 1
        
        if transName and editorName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]

            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. \
                                {citationWork.title}. \
                                translated by {transFirstName} {transLastName}, \
                                edited by {editorFirstName} {editorLastName}, \
                                {citationWork.editions[0].publication_place}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
                    
        if transName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]

            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. {citationWork.title}. \
                    translated by {transFirstName} {transLastName}, {citationWork.editions[0].publication_place}, \
                    {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        if citationWork.contributors[i]['roles'] == 'editor':
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]

            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. {citationWork.title}, \
                edited by {editorFirstName} {editorLastName}, {citationWork.editions[0].publication_place}, \
                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

    #Translated works/works prepared by editors during or after 1900
    if citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.contributors:

        i = 0
        transName = ''
        editorName = ''

        while i < len(citationWork.contributors):
            if citationWork.contributors[i]['roles'] == 'translator':
                transName = citationWork.contributors[i]['roles']
            if citationWork.contributors[i]['roles'] == 'editor':
                editorName = citationWork.contributors[i]['roles']
            i += 1
        
        if transName and editorName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]

            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. {citationWork.title}. \
                                translated by {transFirstName} {transLastName}, \
                                edited by {editorFirstName} {editorLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
                    
        if transName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]

            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. {citationWork.title}. \
                                translated by {transFirstName} {transLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        if editorName:
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]
            
            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. {citationWork.title}, \
                                edited by {editorFirstName} {editorLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."
            
            return ' '.join(citationResponse.split())

        #Single edition books with two authors before 1900
        elif citationWork.editions[0].publication_date < date(1900, 1, 1) and \
            citationWork.editions[0].edition_statement is None:

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]

            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. \
                                {citationWork.title}. {citationWork.editions[0].publication_place}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        #Multiple edition books with two authors before 1900
        elif citationWork.editions[0].publication_date < date(1900, 1, 1) and \
            citationWork.editions[0].edition_statement is not None:

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]

            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. \
                                {citationWork.title}. {citationWork.edition_statement} \
                                {citationWork.editions[0].publication_place}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
            
        #Single Edition books with two authors during and after 1900
        elif citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
            citationWork.editions[0].edition_statement is None:

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]
                
            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. \
                                {citationWork.title}. {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."
            
            return ' '.join(citationResponse.split())

        #Multiple Edition books with two authors during and after 1900
        elif citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
            citationWork.editions[0].edition_statement is not None:

            authName1 = citationWork.authors[0]['name']
            authName2 = citationWork.authors[1]['name']
            listAuthName = authName2.split(', ')
            auth2LastName = listAuthName[0]
            auth2FirstName = listAuthName[1]
                
            citationResponse = f"{authName1}, and {auth2FirstName} {auth2LastName}. \
                                {citationWork.title}. {citationWork.edition_statement}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."
            
            return ' '.join(citationResponse.split())

def mlaThreeAuthorsGenerator(citationWork):

    #Translated works/works prepared by editors before 1900
    if citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.contributors:

        i = 0
        transName = ''
        editorName = ''

        while i < len(citationWork.contributors):
            if citationWork.contributors[i]['roles'] == 'translator':
                transName = citationWork.contributors[i]['roles']
            if citationWork.contributors[i]['roles'] == 'editor':
                editorName = citationWork.contributors[i]['roles']
            i += 1
        
        if transName and editorName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            authName = citationWork.authors[0]['name']

            citationResponse = f"{authName}, et al. {citationWork.title}. \
                    translated by {transFirstName} {transLastName}, \
                    edited by {editorFirstName} {editorLastName}, {citationWork.editions[0].publication_place}, \
                    {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
                    
        if transName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            authName = citationWork.authors[0]['name']
            citationResponse = f"{authName}, et al. {citationWork.title}. \
                    translated by {transFirstName} {transLastName}, {citationWork.editions[0].publication_place}, \
                    {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        if citationWork.contributors[i]['roles'] == 'editor':
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            authName = citationWork.authors[0]['name']
            citationResponse = f"{authName}, et al. {citationWork.title}, \
                edited by {editorFirstName} {editorLastName}, {citationWork.editions[0].publication_place}, \
                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

    #Translated works/works prepared by editors during or after 1900
    if citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.contributors:

        i = 0
        transName = ''
        editorName = ''

        while i < len(citationWork.contributors):
            if citationWork.contributors[i]['roles'] == 'translator':
                transName = citationWork.contributors[i]['roles']
            if citationWork.contributors[i]['roles'] == 'editor':
                editorName = citationWork.contributors[i]['roles']
            i += 1
        
        if transName and editorName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            authName = citationWork.authors[0]['name']

            citationResponse = f"{authName}, et al. {citationWork.title}. \
                                translated by {transFirstName} {transLastName}, \
                                edited by {editorFirstName} {editorLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())
                    
        if transName:
            listTransName = transName.split(', ')
            transLastName = listTransName[0]
            transFirstName = listTransName[1]
            citationResponse = f"{authName}, et al. {citationWork.title}. \
                                translated by {transFirstName} {transLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

        if editorName:
            listEditorName = editorName.split(', ')
            editorLastName = listEditorName[0]
            editorFirstName = listEditorName[1]
            citationResponse = f"{authName}, et al. {citationWork.title}, \
                                edited by {editorFirstName} {editorLastName}, \
                                {citationWork.editions[0].publishers[0]['name']}, \
                                {citationWork.editions[0].publication_date}."

            return ' '.join(citationResponse.split())

    #Single Edition books with three authors or more before 1900
    elif citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is None:
            
        authName = citationWork.authors[0]['name']

        citationResponse = f"{authName}, et al. {citationWork.title}. \
                {citationWork.editions[0].publication_place}, \
                {citationWork.editions[0].publication_date}."

        return ' '.join(citationResponse.split())
        
    #Multiple edition books with three authors or more before 1900
    elif citationWork.editions[0].publication_date < date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is not None:
            
        authName = citationWork.authors[0]['name']

        citationResponse = f"{authName}, et al. {citationWork.title}. \
                            {citationWork.edition_statement} \
                            {citationWork.editions[0].publication_place}, \
                            {citationWork.editions[0].publication_date}."

        return ' '.join(citationResponse.split())
        
    #Single Edition books with three authors during and after 1900
    elif citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is None:

        authName = citationWork.authors[0]['name']

        citationResponse = f"{authName}, et al. {citationWork.title}. \
                {citationWork.editions[0].publishers[0]['name']}, {citationWork.editions[0].publication_date}."

        return ' '.join(citationResponse.split())

    #Multiple edition books with three authors during and after 1900
    elif citationWork.editions[0].publication_date >= date(1900, 1, 1) and \
        citationWork.editions[0].edition_statement is not None:

        authName = citationWork.authors[0]['name']

        citationResponse = f"{authName}, et al. {citationWork.title}. {citationWork.edition_statement}, \
                    {citationWork.editions[0].publishers[0]['name']}, {citationWork.editions[0].publication_date}."

        return ' '.join(citationResponse.split())
        