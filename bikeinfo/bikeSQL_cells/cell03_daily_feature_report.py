import os
import sys

sys.path.append(os.path.dirname(__file__))
from cell01_db_connection_and_query_helper import q

daily_sql = """
SELECT
    DATE(last_update) AS day,
    AVG(available_bikes) AS avg_bikes,
    AVG(available_bike_stands) AS avg_stands,
    COUNT(*) AS records
FROM availability
GROUP BY DATE(last_update)
ORDER BY day;
"""

print(q(daily_sql).head().to_string(index=False))
