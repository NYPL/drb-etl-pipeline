#Extracting the edition number from the has_version field of records for any future records
def extract(version : str, language : str):
        editStatement = version
        editDict = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, \
                    'sixth': 6, 'seventh': 7, 'eigth': 8, 'ninth': 9, 'tenth': 10}
        editNumber = None

        if language == 'English':
            #Edition statements with edition numbers in their string form like first, second, third, etc.
            for word in editStatement.split():
                if word in editDict.keys():
                    editNumber = editDict[word]
                    return editNumber

        #Edition statements with edition numbers in their int form like 1, 2, 3, etc.
        if editNumber == None:
            for word in list(editStatement):
                if word.isdigit():
                    editNumber = int(word)
                    return editNumber

if __name__ == '__main__':
    extract()