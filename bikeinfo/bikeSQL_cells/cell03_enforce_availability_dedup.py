import os
import sys

import sqlalchemy as sqla

sys.path.append(os.path.dirname(__file__))
from cell01_db_connection_and_query_helper import engine, q

try:
    from IPython.display import display
except ImportError:
    def display(df):
        print(df.to_string(index=False))

display(
    q(
        "SELECT COUNT(*) AS duplicate_rows "
        "FROM ("
        "  SELECT number, last_update, COUNT(*) AS c "
        "  FROM availability "
        "  GROUP BY number, last_update "
        "  HAVING c > 1"
        ") d"
    )
)

with engine.begin() as conn:
    has_unique = conn.execute(
        sqla.text(
            "SHOW INDEX FROM availability "
            "WHERE Key_name = 'uq_availability_number_last_update'"
        )
    ).first()

    if not has_unique:
        conn.execute(
            sqla.text(
                """
                DELETE a
                FROM availability a
                JOIN availability b
                  ON a.number = b.number
                 AND a.last_update <=> b.last_update
                 AND a.id > b.id
                """
            )
        )
        conn.execute(
            sqla.text(
                "CREATE UNIQUE INDEX uq_availability_number_last_update "
                "ON availability (number, last_update)"
            )
        )

display(
    q(
        "SHOW INDEX FROM availability "
        "WHERE Key_name = 'uq_availability_number_last_update'"
    )
)
