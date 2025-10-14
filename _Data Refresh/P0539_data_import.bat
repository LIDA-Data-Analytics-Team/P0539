@echo off

REM Define and create the location for storage of temporary extraction files. 
REM Create a date stamp string in format 'yyyy-mm-dd'

REM If system date is stored in format '14/10/2025` then use this
set extractDate=%date:~6,4%-%date:~3,2%-%date:~0,2%

REM If system date is stored in format 'Tue 10/14/2025` then use this:
REM set extractDate=%date:~10,4%-%date:~4,2%-%date:~7,2%

set extractPath=I:\P0539\BCP Update\%extractDate%\
if not exist "%extractPath%" mkdir "%extractPath%"

REM Output to a log file, created in same the location as this *.bat file is run from. 
set LOGFILE=CR_BCP_Update_batch_%extractDate%.log
call :LOG > %LOGFILE%
exit /B

:LOG

REM Set schema of tables in source and destination databases. Table names are identical across both. 
set sourceSchema=CR_LIDA
set destinationSchema=dbo

REM List of tables containing data for migration. Names and structure are identical across both databases. 
REM The ordering of the tables in this list is important. 
REM Incorrect ordering will result in foreign key conflicts. 
set tables=Extract_Date Student_Demographics Programme_Details Programme_Specification Module_Details Module_Teaching_Delivery_Types Module_Assessment_Types Module_Evaluation Student_Engagement NSS_Data JISC_Digital_Experience_Survey_Q43 Qualifications_on_Entry

REM The below loop iterates through the `tables` list variable and for each:
REM	- creates a format file to use the string `~~~~~` as column seperator and `^^^^^` as a row seperator
REM	- exports data from source database to a flat file using the format file
REM	- imports data from newly created flat file into destination database
REM	- deletes both format and data files
REM 
REM Odd seperators are needed because the data contains many of the commonly used ones. 
for %%t in (%tables%) do (
	echo Extracting from %sourceSchema%.%%t to %extractPath%%%t.bcp.
	bcp %destinationSchema%.%%t format nul -c -x -f "%extractPath%%%t_format.xml" -S az-lrdp-p0539v01-db.database.windows.net -d vre-p0539v01-db -G -t~~~~~ -r^^^^^^^^^^
	bcp "select * from %sourceSchema%.%%t where [Extract_Date_ID] = (select Extract_Date_ID from [CR_LIDA_Presentation].[CR_LIDA].[Extract_Date] where [Most_recent_Extract] = 1)" queryout "%extractPath%%%t.bcp" -S BIDA1-PE01 -d CR_LIDA_Presentation -T -f "%extractPath%%%t_format.xml"
	echo %sourceSchema%.%%t extracted.
	echo Importing from %extractPath%%%t.bcp to %destinationSchema%.%%t.
	bcp %destinationSchema%.%%t in "%extractPath%%%t.bcp" -S az-lrdp-p0539v01-db.database.windows.net -d vre-p0539v01-db -G -f "%extractPath%%%t_format.xml"
	echo %%t.bcp imported.
	del "%extractPath%%%t_format.xml"
	echo "%extractPath%%%t_format.xml" file deleted.
	del "%extractPath%%%t.bcp"
	echo "%extractPath%%%t.bcp" file deleted.
)

REM Delete the folder used to contain the extraction flat files.
del "%extractPath%"
echo "%extractPath%" folder deleted.