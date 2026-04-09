import os
import sys

sys.path.append(os.path.dirname(__file__))
from cell01_db_connection_and_query_helper import q


def display(df):
    print(df.to_string(index=False))

# basic stats
display(q("SELECT COUNT(*) AS station_count FROM station"))
display(q("SELECT COUNT(*) AS availability_count FROM availability"))

# reord count by day
display(
    q(
        "SELECT DATE(last_update) AS day, COUNT(*) AS records "
        "FROM availability GROUP BY DATE(last_update) ORDER BY day"
    )
)
