from elasticsearch.helpers import reindex
import os
import yaml


def main():
    try:
        with open('./config/qa.yaml') as envStream:
            try:
                envDict = yaml.full_load(envStream)
            except yaml.YAMLError as err:
                print('Invalid! Please review')
                raise err

    except FileNotFoundError as err:
        print('Missing config YAML file! Check directory')
        raise err

    if envDict:
        for key, value in envDict.items():
            os.environ[key] = value

    print(os.environ['ELASTICSEARCH_INDEX'])
    from managers import ElasticsearchManager
    from model import ESWork

    print('Creating Remote Index')
    esManager = ElasticsearchManager()
    esManager.createElasticConnection()
    esManager.createElasticSearchIndex()
    print('Created')

    localEsManager = ElasticsearchManager('sfr_dcdw')
    localEsManager.createElasticConnection('localhost', '9200', 15)

    reindex(localEsManager.client, 'sfr_dcdw', 'drb_dcdw_qa', target_client=esManager.client)


if __name__ == '__main__':
    main()
