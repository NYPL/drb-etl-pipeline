class Rights:
    ALLOWED_FIELDS = [
        'license', 'rightsStatement', 'source'
    ]

    REQUIRED_FIELDS = [
        'license', 'rightsStatement', 'source'
    ]

    def __init__(self, **kwargs):
        self.attrs = set(kwargs.keys())

        for field, value in kwargs.items():
            setattr(self, field, value)

    def addField(self, field, value):
        setattr(self, field, value)
        self.attrs.add(field)

    def addFields(self, fields):
        if isinstance(fields, dict):
            for field, value in fields.items(): self.addField(field, value)
        elif isinstance(fields, list):
            for field, value in fields: self.addField(field, value)

    def __iter__(self):
        for reqField in self.REQUIRED_FIELDS:
            if getattr(self, reqField, None) is None:
                raise OPDS2RightsException('{} must be present in Rights'.format(reqField))

        if len(self.attrs - set(self.ALLOWED_FIELDS)) > 1:
            unpermittedAttrs = self.attrs - set(self.ALLOWED_FIELDS)
            raise OPDS2RightsException('{} fields are not permitted in Rights'.format(','.join(list(unpermittedAttrs))))

        for field in self.ALLOWED_FIELDS:
            try:
                yield field, getattr(self, field)
            except AttributeError:
                pass

    def __repr__(self):
        return '<Rights(license={}, rightsStatement={}, source={})>'.format(self.license, self.rightsStatement, self.source)

class OPDS2RightsException(Exception):
    pass
