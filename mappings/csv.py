from .core import Core


class CSVMapping(Core):
    def __init__(self, source, statics):
        super().__init__(source, statics)

    def applyMapping(self):
        newRecord = self.initEmptyRecord()

        for field, structure in self.mapping.items():
            try:
                if isinstance(structure, tuple):
                    fieldData = structure[0].format(
                        *[self.source[i] for i in structure[1:]]
                    ) 
                else:
                    fieldData = [
                        s[0].format(*[self.source[i] for i in s[1:]])
                        for s in structure
                    ]
            except IndexError:
                print('Missing data from field {}'.format(field))
                continue

            setattr(newRecord, field, fieldData)

        newRecord.identifiers = list(filter(
            lambda x: x[0] != '|', newRecord.identifiers
        ))
        self.record = newRecord
        self.applyFormatting()
