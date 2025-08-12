# Database Schema: pretrip_db

## Tables
- `users`
  - Each row corresponds to a unique user for the database
- `speedGague_data`
  - Each row corresponds to a row in the csv file from Speedgauge. Each csv file hows records for each driver for a given week, so there should be like 4 or 5 hundred records per file, with one file coming in per week.
- `company_analytics`
  - Each row contains the statistical data for a given week.
  - There may be multiple rows entered for each week. There is a boolean check for allowing generated records from interpolation, and there is a column that specifies how many standard deviations from the mean the filter allows to use for calculations. 


## Table: speedGauge_data

| Column Name                          | Type           | Nullable | Default | Key  | Extra            | Description         |
|------------------------------------|----------------|----------|---------|------|------------------|---------------------|
| id                                 | int            | NO       | NULL    | PRI  | auto_increment   |                     |
| driver_name                        | varchar(255)   | YES      | NULL    |      |                  |       Full name given in the csv file. Sometimes it gets wierd bc there are middle initials, differences in capitalization, etc.              |
| first_name                         | varchar(255)   | YES      | NULL    |      |                  |  This is the parsed first name from the full name from the csv                   |
| last_name                          | varchar(255)   | YES      | NULL    |      |                  |         This is the parsed last name from the full name in the csv.            |
| driver_id                         | int            | YES      | NULL    |      |                  |          This is generally extracted from the csv, but if that fails then we attempt to locate the corresponding driver_name in <span style="color: red"><strong>users</strong></span> table. Then we can get  the driver_id that way. If that fails, we just set the driver_id to NULL.           |
| vehicle_type                      | varchar(255)   | YES      | NULL    |      |                  |  This is a letter given to vehicle types in the csv. All of us are <span style="color: green"><strong>C</strong></span>. This corresponds to the class A trucks we use.                   |
| percent_speeding                  | decimal(5,2)   | YES      | NULL    |      |                  |    This is the money maker! This is the main reason we want the csv file. speedGague provides this number, but it looks like they calculate it by dividing percent_speeding_numberator / percent_speeding_denominator. Those values are later on in the csv file (and later on in this documentation, obv)                |
| is_interpolated                   | tinyint(1)     | YES      | 0       |      |                  |       This is something I made for future use. I intent to write a script that goes through and looks for missing values, then interpolates interior <span style="color: red"><strong>percent_speeding</strong></span>and <span style="color: red"><strong>distance_driven</strong></span> values if there are missing entries. This should only fire if there is missing values between two dates. This is a BOOL, so <span style="color: orange"><strong>0</strong></span> is False and <span style="color: orange"><strong>1</strong></span> is True              |
| max_speed_non_interstate_freeway  | decimal(6,2)   | YES      | NULL    |      |                  |         Highest recorded speed on a non-interstate highway.            |
| percent_speeding_non_interstate_freeway | decimal(5,2) | YES   | NULL    |      |                  |       Percent of incidents on non-interestate highways. This is listed in the csv already, but it looks like they calculate it by dividing incidents / observations              |
| worst_incident_date               | datetime       | YES      | NULL    |      |                  |    Date of the worst incident. SpeedGague only provides us with this single incident. It would be nice to get every incident, but this will have to do  for now.                  |
| incident_location                | text           | YES      | NULL    |      |                  |         Date that corresponds to the URL if there  was an over-speed event.            |
| speed_limit                      | int            | YES      | NULL    |      |                  |             Speed limit at the location of over-speed event.        |
| speed                            | int            | YES      | NULL    |      |                  |       Actuall driver speed at the time of over-speed event.              |
| speed_cap                       | varchar(255)   | YES      | NULL    |      |                  |           idk what this is          |
| custom_speed_restriction          | varchar(255)   | YES      | NULL    |      |                  |          idk what this is. Maybe this is something management does where they know a given road had a different speed limit than what speedGauge thinks it is. This is just speculation though.           |
| distance_driven                 | int            | YES      | NULL    |      |                  |       Total distance driven for the week              |
| url                              | varchar(2048)  | YES      | NULL    |      |                  |        URL for the map at speedGauge that will show a map of the over-speed event.             |
| url_lat                         | decimal(10,8)  | YES      | NULL    |      |                  |        latitude of the url. I extract  this with python wizardy.             |
| url_lon                         | decimal(11,8)  | YES      | NULL    |      |                  |       longitude of the url. I also extract this with python wizardy.              |
| location                        | varchar(255)   | YES      | NULL    |      |                  |        Text  description of where the over-speed even was             |
| percent_speeding_numerator      | decimal(10,2)  | YES      | NULL    |      |                  |       This is total number of incidents recorded. <span style="color: purple">non_interstate</span> <strong>+</strong> <span style="color: green">interstate</span> incidents              |
| percent_speeding_denominator    | decimal(10,2)  | YES      | NULL    |      |                  |      This is totoal number of observations. <span style="color: purple">non_interstate</span> <strong>+</strong> <span style="color: green">interstate.               |
| max_speed_interstate_freeway     | decimal(6,2)   | YES      | NULL    |      |                  |     Highest recorded speed on the interstate                |
| percent_speeding_interstate_freeway | decimal(5,2) | YES    | NULL    |      |                  |      percent_speeding that was on interstate. This is provided in the csv, but is calculated by divinding incidents / observations.             |
| incidents_interstate_freeway    | int            | YES      | NULL    |      |                  |       How many of those pings resulted in an overspeed event              |
| observations_interstate_freeway | int            | YES      | NULL    |      |                  |       how many times speedGague pinged the driver on the interstate              |
| incidents_non_interstate_freeway | int           | YES      | NULL    |      |                  |      how many times speedGauge pinged the driver on non-interstate roads               |
| observations_non_interstate_freeway | int         | YES      | NULL    |      |                  |      how many of those pings resulted in an overspeed event               |
| difference                     | int            | YES      | NULL    |      |                  |        idk what this is             |
| start_date                    | datetime       | YES      | NULL    |      |                  |       Extracted start date from the csv file. It is converted to a datetime object then saved in this column.            |
| end_date                      | datetime       | YES      | NULL    |      |                  |         extracted end date  from the csv file. It is converted to a datetime object then saved in this column           |
| raw_json                      | text           | YES      | NULL    |      |                  |       This is raw json data. I don't actually need it, but I thought it might be helpful to bundle everything up for the record into a json format. Maybe I'll use it later on. idk, maybe it will be easier to sort through if I can just hit the database for this row, then parse though it. Who knows. But it's here if I need it.              |

## Table: users

| Column Name | Type | Nullable | Default | Key | Extra | Description |
|------------ |----- |--------- |-------- |---- | ----- | ----------- |
| id                 | int          | NO          | NULL              | PRIMARY    | auto_increment    |                |
| username           | varchar(255)  | NO          | NULL              | UNIQUE     |                   | User's email address, used for login. |
| password           | varchar(255) | NO          | NULL              |            |                   | Hashed using python crypto magic. Obviously we are not storing actual password in here. |
| creation_timestamp | datetime     | YES         | CURRENT_TIMESTAMP |            | DEFAULT_GENERATED | Python generates a timestamp when the user is first registered into the system. |
| first_name         | varchar(255) | YES         | NULL              |            |                   | User's first name. Not necessesary but nice to  have |
| last_name          | varchar(255) | YES         | NULL              |            |                   | User's last name. Not necessary but nice to have |
| driver_id          | int          | YES         | NULL              |            |                   | Driver number for the company. Currently this is stored as an integer. I might have to play around with this in the futuure. Currently this is used for speedGauge stuff for SWTO so I can store and extract intel based on the employee id number. |


## Table: company_analytics
- Notes
  - Sometimes there are really wild numbers for this data. The average distiance might be 1200, but several people only work one day so the average would get pulled down to 600. Same for percent_speeding. I don't know how it happens, but sometimes there are crazy values like 633%. Girl. That's not even possible.
  - This means that the method we are going to use to generate the statistical information is to get the standard deviation from the mean and filter out everyone who is beyone 1, or maybe 1.5, standard deviations from the mean. Maybe I should include that as part of the schema. I'll put in a column that indicate what the cuttof is as far as filtering outliers.


| Column Name                    | Type   | Nullable | Default | Key | Extra           | Description |
|--------------------------------|--------|----------|---------|-----|------------------|-------------|
| id                             | INT    | NO       | NULL    | PRI | auto_increment   |   Auto-incrementing primary key to keep track of records in an orderly fashion.          |
| start_date                     | DATETIME   | NO       | NULL    |     |              |    The start_data datetime object from the `speedGauge_data` table that we gonna use to run all this statistical analysis.         |
| generated_records_allowed      | INT    | YES      | NULL    |     |                  |    Boolian value: 1, 0. Set to True(1) if the values for this record will include interpolated values. This will help smooth out those odd csv files that don't provide the full dataset. This will also allow me to run the analytic twice, once with and once without interpolated speeds.         |
| records_count                  | INT    | NO       | NULL    |     |                  |    A count of how many records were used to make these statistical caluclations.         |
| std_filter_value              | FLOAT       |    YES      |    NULL     |     |                  |  This column specifies how many standard deviations from the mean I allow to remain in the dataset for analysis. It will probably end up being 1 or 1.5, but I don't know for sure yet. I'lll have this column in so i can run multiple passes of the analysis using different filter values, then just specify what that cutoff standard devation value was in this column.           |
| max_percent_speeding           | FLOAT  | YES      | NULL    |     |                  |    The max percent_speeding taken from <span style="color:red">ONE</span> standard deviation.         |
| min_percent_speeding           | FLOAT  | YES      | NULL    |     |                  |    The minimum percent_speeding taken from <span style="color:red">ONE</span> standard deviation. This will almost always be zero.         |
| avg_percent_speeding           | FLOAT  | YES      | NULL    |     |                  |    The average percent_speeding value         |
| median_percent_speeding        | FLOAT  | YES      | NULL    |     |                  |    The median percent_speeding value.         |
| std_percent_speeding           | FLOAT  | YES      | NULL    |     |                  |    The standard deviation for percent_speeding.         |
| percent_change_percent_speeding | FLOAT | YES      | NULL    |     |                  |    The relative percentage change in percent_speeding from the previous week. This is based on average percent speedig.         |
| abs_change_percent_speeding    | FLOAT  | YES      | NULL    |     |                  |    The absolute change in percent_speeding from the previous week. This is based on average percent_speeding.         |
| max_distance_driven            | FLOAT  | YES      | NULL    |     |                  |    The highest distance driven. This will only take the highest distance from within <span style="color: red">ONE</span> standard deviation from the mean         |
| min_distance_driven            | FLOAT  | YES      | NULL    |     |                  |    The lowest distance driven. This will only take the lowest distance driven from within <span style="color: red">ONE</span> standard deviation of the mean.         |
| avg_distance_driven            | FLOAT  | YES      | NULL    |     |                  |    The average distance driven value        |
| median_distance_driven         | FLOAT  | YES      | NULL    |     |                  |    The median distance driven value        |
| std_distance_driven            | FLOAT  | YES      | NULL    |     |                  |    The standard deviation for the distance driven data points         |
| percent_change_distance_driven | FLOAT  | YES      | NULL    |     |                  |    The relative percentage change in distance driven from last week. This is based on the average distance.         |
| abs_change_distance_driven     | FLOAT  | YES      | NULL    |     |                  |    The absolute change in distance driven from the previous week. This is based on the average distance.        |
| speeding_trend_json            | JSON   | YES      | NULL    |     |                  |    A JSON object containing the speeding trend data for the last year. The key is the start_date and the value is the average percent_speeding.         |
| distance_trend_json            | JSON   | YES      | NULL    |     |                  |    A JSON object containing the distance driven trend data for the last year. The key is the start_date and the value is the average distance_driven.         |


## Table: driver_analytics_table

| Column Name                      | Type     | Nullable | Default | Key | Extra           | Description |
|----------------------------------|----------|----------|---------|-----|------------------|-------------|
| id                               | int      | NO       |         | PRI | auto_increment   | Standard autoincrementing integer used to keep our records nice and organized.            |
| driver_id                        | int      | NO       |         |     |                  | The driver_id of the person we are generating this analysis for.            |
| start_date                       | datetime | NO       |         |     |                  | start_date from the csv file. This is a datetime  object  that should match the one in the csv from the `speedGauge_data` table.            |
| std_filter_threshold             | float    | YES      | NULL    |     |                  | A record of what the standard deviaiton threshold was that I used to filter out outliers in the data.            |
| current_week_percent_speeding    | float    | NO       |         |     |                  | Value of percent_speeding for current week.            |
| previous_week_percent_speeding   | float    | YES      | NULL    |     |                  | Value of percent_speeding last week.            |
| percent_change_percent_speeding  | float    | YES      | NULL    |     |                  | Percentage change in percent_speeding from the previous week.            |
| abs_change_percent_speeding      | float    | YES      | NULL    |     |                  | Absolute change in percent_speeding from the previous available week data.            |
| max_percent_speeding             | float    | YES      | NULL    |     |                  | Historical max value for percent_speeding.            |
| min_percent_speeding             | float    | YES      | NULL    |     |                  | Historical minimum value for percent_speeding. For most people this will be **0**.            |
| avg_percent_speeding             | float    | YES      | NULL    |     |                  | Historical average value for percent_speeding            |
| median_percent_speeding          | float    | YES      | NULL    |     |                  | Historical median value for percent speeding            |
| std_percent_speeding             | float    | YES      | NULL    |     |                  | Standard deviation for the historical data for percent_speeding for the individual driver.            |
| current_week_distance_driven     | float    | NO       |         |     |                  | Current value for distance driven            |
| previous_week_distance_driven    | float    | YES      | NULL    |     |                  | Distance driven previous week            |
| percent_change_distance_driven   | float    | YES      | NULL    |     |                  | relative percentage change in distance from the previous week            |
| abs_change_distance_driven       | float    | YES      | NULL    |     |                  | Absolute change in value for distance from the previous week.            |
| max_distance_driven              | float    | YES      | NULL    |     |                  | Historical max distance driven            |
| min_distance_driven              | float    | YES      | NULL    |     |                  | Historical minimum distance driven            |
| avg_distance_driven              | float    | YES      | NULL    |     |                  | Historical average distance driven            |
| median_distance_driven           | float    | YES      | NULL    |     |                  | Historical median distance for the driver            |
| std_distance_driven              | float    | YES      | NULL    |     |                  | standard deviation of distance driven for the driver            |
| records_count                    | int      | YES      | NULL    |     |                  | A count of how many records were available for calculating the data for this analysis.            |
| speeding_trend_json            | JSON   | YES      | NULL    |     |                  |    A JSON object containing the speeding trend data for the last year. The key is the start_date and the value is the average percent_speeding.         |
| distance_trend_json            | JSON   | YES      | NULL    |     |                  |    A JSON object containing the distance driven trend data for the last year. The key is the start_date and the value is the average distance_driven.         |
