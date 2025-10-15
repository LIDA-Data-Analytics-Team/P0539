# Data Refresh

Periodically the BIDA Team will make new data available on their SQL Database and we need to import it to the project database in LASER.  

This import can be achieved using the [BCP utility](https://learn.microsoft.com/en-us/sql/tools/bcp-utility?view=sql-server-ver17&tabs=windows) and a batch file has been created to that end.  

1. Run the script
2. Update latest extraction table

The script needs to be executed from DAT02 so that both databases can be accessed.  
You will need to be granted access to both databases in order to pull data from one to the other.  

## Script execution  

Before executing the script check how your system date is stored in cmd.  
From a `cmd.exe` console run the command:  
```bat
echo %date%
```

If the result is of the format `dd/mm/yyyy` then the script needs to set the `extractDate` variable like so:
```bat
set extractDate=%date:~6,4%-%date:~3,2%-%date:~0,2%
```
If the result is of the format `Day mm/dd/yyyy` then the script needs to set the `extractDate` variable like so:
```bat
set extractDate=%date:~10,4%-%date:~4,2%-%date:~7,2%
```
Edit the *.bat file as appropriate.  

Double click [P0539_data_import.bat](P0539_data_import.bat) or from a `cmd.exe` console navigate to the folder that contains the file and run it.  

The batch file will execute the script that uses `I:\P0539\BCP Update\` as a temporary staging area for flat files generated from the source database, importing them into the destination and deleting them as each table migration completes.  

It will also create a date stamped log file output of the process in the same location as the batch file.  

!! DO NOT CLOSE THE CONSOLE WINDOW DURING EXECUTION !!  
This will interrupt the data migration in an uncontrolled manner, meaning data will be duplicated if the script is rerun. It's really not that sophisticated a script!  

Each table export query uses the latest [Extract_Date_ID] to identify records required for import, i.e.  
```sql
select [Extract_Date_ID]  
from [CR_LIDA_Presentation].[CR_LIDA].[Extract_Date]  
where [Most_recent_Extract] = 1  
```

If the migration is interrupted my suggestioon would be to delete all records with an `[Extract_Date_ID]` of the import before simply starting again. The above query will tell you the [Extract_Date_ID] used for the import.  

## Post script Execution  

Once complete, the `[Extract_Date]` table will need updating, setting the previously `[Most_recent_Extract]` flag to zero.  

To do so you could run the following T-SQL from management studio when connected to the project database in LASER (`vre-p0539v01-db`). 

```sql 
update [dbo].[Extract_Date]
set [Most_recent_Extract] = 0
where [Extract_Date_ID] = <previous Extract_Date_ID>
```

Worth checking that the `[Extract_Date_ID]` matches up between source and destination `[Extract_Date]` tables.  
`[Extract_Date_ID]` is an auto incrementing [identity](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-table-transact-sql-identity-property) field in the `[dbo].[Extract_Date]` table, but not in any of the other tables. If BIDA created failed extracts then the possibility exists that some integers will be absent from the sequence. For example, data will be imported with an `[Extract_Date_ID] = 7` but the next record in the `[dbo].[Extract_Date]` table could be `[Extract_Date_ID] = 4`.  
In this case, we will need to add dummy records until the required `[Extract_Date_ID]` is reached and then delete the unwanted records. The deletion will take some time as foriegn key contraints will need to be checked before the transaction completes.  

## Databases
||Database Server|Database|Authentication type|Table Schema|
|---|---|---|---|---|
|Source|BIDA1-PE01|CR_LIDA_Presentation|Windows Authentication|CR_LIDA|
|Destination|az-lrdp-p0539v01-db.windows.database.net|vre-p0539v01-db|Microsoft Entra authentication|dbo|

## Table order

The ordering of the tables in this list is important.  
Incorrect ordering will result in foreign key conflicts.  
The tables list variable must conatin the table names (without schema) in the following order:  

|Order Number|Table Name|
|--:|:--|
|1|Extract_Date|
|2|Student_Demographics|
|3|Programme_Details|
|4|Programme_Specification|
|5|Module_Details|
|6|Module_Teaching_Delivery_Types|
|7|Module_Assessment_Types|
|8|Module_Evaluation|
|9|Student_Engagement|
|10|NSS_Data|
|11|JISC_Digital_Experience_Survey_Q43|
|12|Qualifications_on_Entry|

## BCP Commands

|Flag|Use|Used in|
|---|---|---|
|-S|Server name|creating format files, exporting data from source, importing data to destination|
|-d|Database name|creating format files, exporting data from source, importing data to destination|
|-f|Specifies path of format file|creating format files, exporting data from source, importing data to destination|
|-c|Use character data type|creating format files|
|-x|Generates an XML-based format file|creating format files|
|-t|Specifies field terminator|creating format files|
|-r|Specifies row terminator|creating format files|
|-G|Use Microsoft Entra authentication|creating format files, importing data to destination|
|-T|Use Integrated Security|exporting data from source|
