import argparse
import os
from uuid import uuid4

import sqlalchemy as sa

from managers import DBManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("user")
    args = parser.parse_args()
    user = args.user

    dbManager = DBManager(
        user=os.environ.get("POSTGRES_USER", "localuser"),
        pswd=os.environ.get("POSTGRES_PSWD", "localpsql"),
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        db=os.environ.get("POSTGRES_NAME", "drb_test_db"),
    )
    dbManager.generateEngine()
    dbManager.createSession()

    uuid = uuid4()

    with dbManager.session.begin() as _session:
        # First create the collection
        collection_id = dbManager.session.execute(
            sa.text(
                """
                INSERT INTO collections (
                  date_created,
                  uuid,
                  title,
                  creator,
                  description,
                  owner,
                  type
                ) VALUES (
                  NOW(),
                  :uuid,
                  'Sarangs cool collection',
                  :creator,
                  'Some cool stuff!',
                  :owner,
                  'automatic'
                )
                RETURNING id
                """
            ),
            {
                "uuid": uuid,
                "creator": user,
                "owner": user,
            },
        ).scalar()

        # Now the search terms
        dbManager.session.execute(
            sa.text(
                """
                INSERT INTO automatic_collection (
                  collection_id,
                  keyword_query,
                  sort_field,
                  sort_direction,
                  "limit"
                ) VALUES (:collectionId, 'horticulture', :sortField, :sortDirection, :limit)
                """,
            ),
            {
                "collectionId": collection_id,
                "sortField": "date",
                "sortDirection": "DESC",
                "limit": "100",
            },
        )


if __name__ == "__main__":
    main()
