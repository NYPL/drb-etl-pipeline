from model import (
    ESWork,
    ESSubject,
    ESIdentifier,
    ESAgent,
    ESLanguage,
    ESRights,
    ESEdition
)


class SFRElasticRecordManager:
    def __init__(self, dbWork):
        self.dbWork = dbWork
        self.work = None
    
    def getCreateWork(self):
        workData = {
            field: getattr(self.dbWork, field, None)
            for field in ESWork.getFields()
        }

        self.work = ESWork.get(self.dbWork.uuid, ignore=404)
        if self.work is None:
            self.work = ESWork(meta={'id': self.dbWork.uuid}, **workData)
        else:
            self.updateWork(workData)

        self.enhanceWork()
    
    def saveWork(self):
        self.work.save()
    
    def updateWork(self, data):
        for key, value in data.items():
            setattr(self.work, key, value)

    def enhanceWork(self):
        """Build an ElasticSearch object from the provided postgresql ORM
        object. This builds a single object from the related tables of the 
        db object that can be indexed and searched in ElasticSearch.
        """
        self.work.date_created = self.dbWork.date_created
        self.work.date_modified = self.dbWork.date_modified

        self.setSortTitle()
        self.work.alt_titles = [a for a in self.dbWork.alt_titles]

        self.work.subjects = [ESSubject(**s) for s in self.dbWork.subjects]

        self.work.agents = [
            ESAgent(**SFRElasticRecordManager.addAgent(a))
            for a in [*self.dbWork.authors, *self.dbWork.contributors]
        ]

        self.work.identifiers = [
            ESIdentifier(**dict(i)) for i in self.dbWork.identifiers
        ]

        self.work.languages = [
            ESLanguage(**l)
            for l in list(filter(None, self.dbWork.languages))
        ]
        
        self.work.is_government_document = SFRElasticRecordManager.addGovDocStatus(
            self.dbWork.measurements
        )

        self.work.editions = [self.createEdition(e) for e in self.dbWork.editions]

    @staticmethod
    def addAgent(agent):
        agent['sort_name'] = agent['name'].lower()
        agent['roles'] = agent.get('roles', ['author'])
        return agent
    
    @staticmethod
    def addGovDocStatus(measurements):
        govDocMeasurement = list(filter(
            lambda x: x.quantity == 'government_document', measurements
        ))
        if len(govDocMeasurement) > 0:
            if int(govDocMeasurement[0].value) == 1:
                return True
        
        return False

    def createEdition(self, edition):
        newEd = ESEdition(**{
            field: getattr(edition, field, None)
            for field in ESEdition.getFields()
        })
        newEd.edition_id = newEd.id
        del newEd.id

        newEd.alt_titles = [a for a in edition.alt_titles]

        newEd.identifiers = [ESIdentifier(**dict(i)) for i in edition.identifiers]

        newEd.agents = [
            ESAgent(**SFRElasticRecordManager.addAgent(a))
            for a in [*edition.publishers, *edition.contributors]
        ]

        newEd.rights = [ESRights(**r) for r in edition.rights]

        newEd.languages = [
            ESLanguage(**l)
            for l in list(filter(None, edition.languages))
        ]

        newEd.formats = [
            f for f in set(SFRElasticRecordManager.addAvailableFormats(edition.items))
        ]

        return newEd

    @staticmethod
    def addAvailableFormats(items):
        for item in items:
            for link in item.links:
                yield link.media_type
    
    def setSortTitle(self):
        if self.work.sort_title is None:
            self.work.sort_title = self.dbWork.title.lower()
