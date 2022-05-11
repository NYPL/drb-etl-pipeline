#Extracting the edition number from the has_version field of records for any future records
def extract(version : str, language : str):

    editDict = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, \
                'sixth': 6, 'seventh': 7, 'eigth': 8, 'ninth': 9, 'tenth': 10}

    editFrenchDict = {'premier': 1, 'première': 1, 'deuxième': 2, 'troisième': 3, 'quatrième': 4, 'cinquième': 5, \
                'sixième': 6, 'septième': 7, 'huitième': 8, 'neuvième': 9, 'dixième': 10}

    editGermanDict = {'erste': 1, 'zweite': 2, 'dritte': 3, 'vierte': 4, 'fünfte': 5, \
                'sechste': 6, 'siebte': 7, 'achte': 8, 'neunte': 9, 'zehnte': 10}

    editSpanishDict = {'primero': 1, 'segundo': 2, 'tercero': 3, 'cuarto': 4, 'quinto': 5, \
                'sexto': 6, 'séptimo': 7, 'octavo': 8, 'noveno': 9, 'décimo': 10}

    editDutchDict = {'eerste': 1, 'tweede': 2, 'derde': 3, 'vierde': 4, 'vijfde': 5, \
                'zesde': 6, 'zevende': 7, 'achtste': 8, 'negende': 9, 'tiende': 10}
                
    editRussianDict = {'первый': 1, 'pervyi': 1, 'второй': 2, 'vtoroi': 2, 'третий': 3, \
                'tretii': 3, 'четвертый ': 4, 'chetvyortyi': 4, 'пятый': 5, 'pyatyi': 5, \
                'шестой': 6, 'shestoi': 6, 'седьмой': 7, 'sed’moi': 7, 'восьмой ': 8, \
                'vos’moi': 8, 'девятый': 9, 'devyatyi': 9, 'десятый': 10, 'desyatyi': 10}

    editStatement = version
    editNumber = None

    #Edition statements with edition numbers in their English ordinal form 
    if language.lower() == 'english' or language.lower() == 'en' or language.lower() == 'eng':   
        for word in editStatement.split():
            if word in editDict.keys():
                editNumber = editDict[word]
                return editNumber

    #Edition statements with edition numbers in their French ordinal form 
    if language.lower() == 'french' or language.lower() == 'fr' or language.lower() == 'fre':
        for word in editStatement.split():
            if word in editFrenchDict.keys():
                editNumber = editFrenchDict[word]
                return editNumber
    
    #Edition statements with edition numbers in their German ordinal form 
    if language.lower() == 'german' or language.lower() == 'ge' or language.lower() == 'dt':
        for word in editStatement.split():
            if word in editGermanDict.keys():
                editNumber = editGermanDict[word]
                return editNumber

    #Edition statements with edition numbers in their Spanish ordinal form 
    if language.lower() == 'spanish' or language.lower() == 'spa' or language.lower() == 'span':
        for word in editStatement.split():
            if word in editSpanishDict.keys():
                editNumber = editSpanishDict[word]
                return editNumber

    #Edition statements with edition numbers in their English ordinal form 
    if language.lower() == 'dutch' or language.lower() == 'nl' or language.lower() == 'du' or language.lower() == 'dut':
        for word in editStatement.split():
            if word in editDutchDict.keys():
                editNumber = editDutchDict[word]
                return editNumber

    #Edition statements with edition numbers in their Russian ordinal form 
    if language.lower() == 'russian' or language.lower() == 'ru' or language.lower() == 'rus':
        for word in editStatement.split():
            if word in editRussianDict.keys():
                editNumber = editRussianDict[word]
                return editNumber

    #Edition statements with edition numbers in their numerical form
    if editNumber == None:
        for word in list(editStatement):
            if word.isdigit():
                editNumber = int(word)
                return editNumber

if __name__ == '__main__':
    extract()