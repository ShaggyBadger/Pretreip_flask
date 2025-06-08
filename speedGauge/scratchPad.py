import settings
from src import db_utils
import statistics

conn = settings.db_connection()
c = conn.cursor()

date_list = db_utils.get_all_dates()

filtered = []
non_filtered = []
generated = []

sql = f'SELECT percent_speeding, percent_speeding_source FROM {settings.speedGaugeData} WHERE start_date = ? AND percent_speeding_source IS NULL'
values = (date_list[-1],)

c.execute(sql, values)
results = c.fetchall()

for result in results:
	filtered.append(result[0])

sql = f'SELECT percent_speeding, percent_speeding_source FROM {settings.speedGaugeData} WHERE start_date = ?'
values = (date_list[-1],)

c.execute(sql, values)
results = c.fetchall()

for result in results:
	non_filtered.append(result[0])
	
sql = f'SELECT percent_speeding, percent_speeding_source FROM {settings.speedGaugeData} WHERE start_date = ? AND percent_speeding_source = ?'
values = (date_list[-1], 'generated')

c.execute(sql, values)
results = c.fetchall()

for result in results:
	generated.append(result[0])


print(len(filtered))
print(len(non_filtered))
print(len(generated))

print(statistics.mean(filtered))
print(statistics.mean(non_filtered))
print(statistics.mean(generated))

conn.close()
