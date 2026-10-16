@echo off
SetLocal EnableDelayedExpansion

REM Define and create the location for storage of temporary extraction files. 
REM Create a date stamp string in format 'yyyy-mm-dd'

REM If system date is stored in format '14/10/2025` then use this
REM set extractDate=%date:~6,4%-%date:~3,2%-%date:~0,2%

REM If system date is stored in format 'Tue 10/14/2025` then use this:
set extractDate=%date:~10,4%-%date:~4,2%-%date:~7,2%

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
	set table=%%t
	echo INFO: Attempting to extract from !sourceSchema!.!table! to !extractPath!!table!.bcp

	Set /a format_success=1
	if exist !extractPath!!table!_format.xml (	REM Skip format file creation if file already exists
		set /a format_success=0
		echo INFO: Format file already exists, skipping creation of !table!_format.xml
		)	
	for /L %%w in (1,1,5) do ( 				REM retry five times
		REM Create format file from destination table
		if !format_success! NEQ 0 (
			bcp !destinationSchema!.!table! format nul -c -x -f "!extractPath!!table!_format.xml" -S az-lrdp-p0539v01-db.database.windows.net -d vre-p0539v01-db -G -t~~~~~ -r^^^^^^^^^^
			if !ERRORLEVEL! EQU 0 (
				set /a format_success=0
				echo INFO: Format file created from destination table: !destinationSchema!.!table!
				)
			)
		)
	if !format_success! NEQ 0 (
		echo ERROR: Failed to create format file from destination table: !destinationSchema!.!table!
		)

	Set /a export_success=1
	if !format_success! EQU 0 (			REM Only attempt if previous step successful
		if exist !extractPath!!table!.bcp (	REM Skip export if temp file already exists
			set /a export_success=0
			echo INFO: Temp extract file already exists, skipping data export to !table!.bcp
			)
		for /L %%w in (1,1,5) do ( 		REM retry five times
			REM Export from Source table to temp file using format file
			if !export_success! NEQ 0 (
				bcp "select * from !sourceSchema!.!table! where [Extract_Date_ID] = (select Extract_Date_ID from [CR_LIDA_Presentation].[CR_LIDA].[Extract_Date] where [Most_recent_Extract] = 1)" queryout "!extractPath!!table!.bcp" -S BIDA1-PE01 -d CR_LIDA_Presentation -T -f "!extractPath!!table!_format.xml"
				if !ERRORLEVEL! EQU 0 (
					set /a export_success=0
					echo INFO: Exported from Source table to temp file using format file: !table!.bcp created
					)
				)
			)
		if !export_success! NEQ 0 (
			echo ERROR: Failed to export from Source table to temp file using format file: !table!.bcp NOT created
			)
		)
	else (
		echo INFO: Not attempting to export from Source table to temp file as previous step failed
		)

	Set /a import_success=1
	if !export_success! EQU 0 (			REM Only attempt if previous step successful
		echo INFO: Attempting to import from !extractPath!!table!.bcp to !destinationSchema!.!table!
		for /L %%w in (1,1,5) do ( 		REM retry five times
			REM Import from temp file to destination table
			if !import_success! NEQ 0 (
				bcp !destinationSchema!.!table! in "!extractPath!!table!.bcp" -S az-lrdp-p0539v01-db.database.windows.net -d vre-p0539v01-db -G -E -f "!extractPath!!table!_format.xml"
				if !ERRORLEVEL! EQU 0 (
					set /a import_success=0
					echo INFO: Imported from temp file to destination table: !destinationSchema!.!table!
					)
				)
			)
		if !import_success! NEQ 0 (
			echo ERROR: Failed to import from temp file to destination table: !destinationSchema!.!table!
			)
		)
	else (
		echo INFO: Not attempting to Import from temp file to destination table as previous step failed
		)

	if !import_success! EQU 0 (			REM Only attempt if previous step successful
		del "!extractPath!!table!_format.xml"
		echo INFO: !extractPath!!table!_format.xml file deleted.
		del "!extractPath!!table!.bcp"
		echo INFO: !extractPath!!table!.bcp file deleted.
		)
	else (
		echo INFO: Not deleting format or temp extract files as previous step failed
		)
	)

REM Delete the folder used to contain the extraction flat files. Will fail if not empty. 
rmdir "!extractPath!" 
if not exist "!extractPath!" (
	echo !extractPath! folder deleted
	)

EndLocal