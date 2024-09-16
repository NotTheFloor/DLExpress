DOCUMENT_TYPES_QUERY = "SELECT DocumentTypeId, Name, AIEnabled, RIEnabled, RIMethod FROM [dbo].[DocumentTypes]"

ENABLE_AI_QUERY = """
UPDATE [dbo].[DocumentTypes]
Set
    Modified = GETDATE(),
    AIEnabled = 1
WHERE DocumentTypeId = {DOC_TYPE_ID};
"""

DISABLE_AI_QUERY = """
UPDATE [dbo].[DocumentTypes]
Set
    Modified = GETDATE(),
    AIEnabled = 0
WHERE DocumentTypeId = {DOC_TYPE_ID};
"""

ENABLE_RI_QUERY = """
UPDATE [dbo].[DocumentTypes]
Set
    Modified = GETDATE(),
    RIEnabled = 1,
    RIMethod = {RI_METHOD}
WHERE DocumentTypeId = {DOC_TYPE_ID};
"""

REVERT_RI_QUERY = """
UPDATE [dbo].[DocumentTypes]
Set
    Modified = GETDATE(),
    RIEnabled = {RI_ENABLED},
    RIMethod = {RI_METHOD}
WHERE DocumentTypeId = {DOC_TYPE_ID};
"""

GET_SPROC_TEXT_QUERY = "EXEC sp_helptext {SPROC_NAME}"

GET_RI_SCHEDULE_QUERY = """
SELECT * FROM [dbo].[RISchedules] WHERE ParentId = {DOC_TYPE_ID};
"""

INSERT_RI_SCHEDULE_QUERY = """
INSERT INTO [dbo].[RISchedules]
( Created , Modified , ParentId , ModifiedBy , TimeToRun , LastTimeRun , 
DeferDays , DaysInQueue , ReportFailures , UpdateRIQueue , ScheduleType , 
ProcessingInterval , ProcessingIntervalType , ProcessNow , 
PriorityProcessNewDocs , PriorityProcessDelay)
VALUES
( GETDATE() , GETDATE() , {DOC_TYPE_ID} , -1 , NULL , NULL ,
0 , 3 , 0 , NULL , 2 ,
{PROCESSING_INTERVAL} , {PROCESSING_INTERVAL_TYPE} , 0 , 
0 , 0 );
"""

DELETE_RI_SCHEDULE_QUERY = """
DELETE FROM [dbo].[RISchedules] WHERE ParentId = {DOC_TYPE_ID};
"""

UPDATE_RI_SCHEDULE_QUERY = """
UPDATE [dbo].[RISchedules]
Set
    Modified = GETDATE(),
    ScheduleType = 2,
    ProcessingInterval = {PROCESSING_INTERVAL},
    ProcessingIntervalType = {PROCESSING_INTERVAL_TYPE}
WHERE ParentId = {DOC_TYPE_ID};
"""

GET_DIST_STAMPS = "SELECT * FROM DynamicUI"
GET_DIST_STAMP_FIELDS = "SELECT * FROM DynamicUIField"

GET_PROPERTIES = """
SELECT
PropertyId, Created, Modified, ParentId, ModifiedBy, PropertyName, UserPrompt, 
DataType, PropertyTag, DecimalPlaces, HasLookup, SystemLookupId, 
DisplayFieldName as FieldName, ShowLookupButton, UseHotKey, CausesValidation, ValidationSql, 
ControlType, EditWidth, HiddenProperty
FROM [dbo].[Propertys]"""
GET_DOCUMENT_TYPES = """
SELECT 
DocumentTypeId, Created, Modified, ParentID, ModifiedBy, Name, Description, 
KeyDocumentTypePropertyGUID, DocumentTypeGUID, DocumentTypeTag, AIEnabled, 
AIObjectProgID, RIEnabled, RIMethod, AIMethod, Active, AIAfterManualIndexAction, 
FTEnabled as FullTextEnabled 
FROM [dbo].[DocumentTypes];
"""
GET_WORKFLOWS_QUERY = "SELECT * from [dbo].[Workflows]"
GET_WORKFLOW_ACTIVITIES_QUERY = "SELECT * from [dbo].[WorkflowActivities]"

GET_DOCUMENT_TYPE_PROPERTY = "SELECT * FROM [dbo].[DocumentTypePropertys]"


DOC_PROPS_QUERY = """
SELECT
	dtp.PropertyId
	, replace(replace(p.UserPrompt,' ',''),'#','No') AS UserPrompt
	, CASE p.DataType WHEN 0 THEN '[varchar](250) NULL'
					WHEN 1 THEN '[int] NULL'
					WHEN 2 THEN '[datetime] NULL'
					WHEN 3 THEN '[int] NULL'
					WHEN 4 THEN '[decimal](18, 2) NULL'
					END AS DataType
    , p.DataType AS DataTypeID
    , dtp.PropertyType
    , dtp.DocumentTypePropertyGUID
    , dtp.ParentDocumentTypePropertyGUID
FROM DocumentTypes dt with (nolock)
 INNER JOIN DocumentTypePropertys dtp with (nolock) on dt.DocumentTypeId = dtp.ParentId
 INNER JOIN Propertys p with (nolock) on dtp.PropertyId = p.PropertyId
WHERE dt.DocumentTypeId = {doc_type_id}
ORDER BY SequenceNumber
"""

WORKFLOWS_AND_ACTIVITY_QUERY = """
SELECT wf.Title as workflow, wf.WorkflowID as WorkflowID, wfa.Title as ActivityTitle, wfa.WorkflowActivityID
FROM [dbo].workflows as wf
INNER JOIN [dbo].WorkflowActivities as wfa on wf.WorkflowID = wfa.WorkflowID
"""

# TODO: Need to validate DataSourceID; %DocumentID%?
# Returns AIProfileID
EXPORT_SPROC_SCRIPT = (
    "exec {SPROC_NAME} ''%DocumentID%'', ''{SUCCESS_WF}'', ''{FAILED_WF}''"
)

INDEX_SPROC_AI_SCRIPT = "exec {SPROC_NAME} @DocId=%DocumentID%"

ADD_AI_QUERY = """
SET NOCOUNT ON; 
INSERT into AIProfiles ( Created , Modified , ModifiedBy , ProfileName , DataSourceID , SourceTable , QueryText , SingleTable , PropsInNotReq) 
VALUES ( GETDATE() , GETDATE() , -1 , '{AI_NAME}' , 10000 , NULL , '{AI_SCRIPT}', 0 , 1 );
"""

COUNT_AI_PROFILES_QUERY = (
    "SELECT COUNT(*) from DocTypeAIProfiles where ParentId = '{DOC_TYPE_ID}'"
)

COUNT_TASK_WITH_ACTIVITY_QUERY = "SELECT COUNT(*) from EventAutomatedTasks where WorkflowActivityID = '{ACTIVITY_ID}'"

COUNT_TASKS_WITH_ACTIVITY_QUERY = "SELECT COUNT(*) from EventAutomatedTasks where WorkflowActivityID = '{ACTIVITY_ID}'"

# Returns DocTypeProfileId
ADD_DOC_TYPE_AI_QUERY = """
SET NOCOUNT ON; 
INSERT INTO [dbo].[DocTypeAIProfiles]([Created],[Modified],[ParentId],[ModifiedBy],[FolderID],[Sequence],[AIProfileID]
    ,[ExitOnSuccess],[ExecutionContext],[SkipOnDocTypeProperty],[SkipOnDocTypePropID])
VALUES (GETDATE(),GETDATE(),{DOC_TYPE_ID},-1,-1,{SEQ_COUNT},{AI_PROFILE_ID},0,{EXECUTION_CONTEXT},0,NULL);
"""

UPDATE_WF_AI_QUERY = """
UPDATE Workflows 
Set Modified= GETDATE(), 
    ModifiedBy= -1
WHERE WorkflowID = {WF_ID};
UPDATE WorkflowActivities 
Set Modified= GETDATE(), 
    ModifiedBy= -1, 
    EnableAutoIndex= 1
WHERE WorkflowActivityID = {WF_ACTIVITY_ID};
SET NOCOUNT ON; 
INSERT into WorkflowActivityAIProfiles ( WorkflowActivityID , DocTypeAIProfileID , Created , Modified , ModifiedBy) 
VALUES ( {WF_ACTIVITY_ID} , {DOC_TYPE_AI_ID} , GETDATE() , GETDATE() , -1 );
"""

ADD_EVENT_CONFIG_QUERY = """
SET NOCOUNT ON; 
--- Add Event Configuration (Sequence should be 0 as not tied to WF)
INSERT INTO EventAutomatedTasks 
    (Created, Modified, ModifiedBy, Name, Description, AppEventID, WorkflowActivityID, RuleXml, RuleSet, Enabled, Seq, ExitCode, EventConfigurationID) 
VALUES 
    (GETDATE(), GETDATE(), -1, N'{TASK_NAME}', NULL, 12, NULL, NULL, NULL, {START_ACTIVE}, 0, 0, NEWID())
"""

GET_EVENT_CNF_ID_FROM_TASK_ID = "SELECT EventConfigurationID FROM EventAutomatedTasks WHERE EventAutomatedTaskID = {TASK_ID}"

ADD_TRIGGER_EVENT_QUERY = """
SET NOCOUNT ON; 
--- Add Event Configuration (Sequence should be 0 as not tied to WF)
INSERT INTO EventAutomatedTasks 
    (Created, Modified, ModifiedBy, Name, Description, AppEventID, WorkflowActivityID, RuleXml, RuleSet, Enabled, Seq, ExitCode, EventConfigurationID) 
VALUES 
    (GETDATE(), GETDATE(), -1, N'{TASK_NAME}', NULL, 5, {STATUS_ID}, NULL, NULL, {START_ACTIVE}, {SEQ}, 0, NEWID())
"""

ADD_DATABASE_ACTION_QUERY = """
SET NOCOUNT ON; 
INSERT INTO EventDatabaseActions 
    (Created, Modified, ModifiedBy, EventAutomatedTaskID, Name, ProcedureName, RuleXml, RuleSet, Seq, ExitCode, ParentCondition, ExecutionTimeOut) 
VALUES 
    (GETDATE(), GETDATE(), -1, {EVENT_TASK_ID}, N'{DB_ACTION_NAME}', N'{SPROC_NAME}', NULL, NULL, 1, 0, 1, 60);
"""

ADD_DB_ACTION_PARAMETERS_QUERY = """
SET NOCOUNT ON; 
INSERT INTO EventDatabaseActionParameters 
    (Created, Modified, ModifiedBy, EventDatabaseActionID, Name, DataType, ValueToken) 
VALUES 
    (GETDATE(), GETDATE(), -1, {EVENT_DB_ACTION_ID}, N'@Staged', N'number', N'{STAGED_ID}');
--- 2nd parameter
INSERT INTO EventDatabaseActionParameters 
    (Created, Modified, ModifiedBy, EventDatabaseActionID, Name, DataType, ValueToken) 
VALUES 
    (GETDATE(), GETDATE(), -1, {EVENT_DB_ACTION_ID}, N'@ImportSuccess', N'number', N'{IMPORT_SUCCESS_ID}');
--- 3nd parameter
INSERT INTO EventDatabaseActionParameters 
    (Created, Modified, ModifiedBy, EventDatabaseActionID, Name, DataType, ValueToken) 
VALUES 
    (GETDATE(), GETDATE(), -1, {EVENT_DB_ACTION_ID}, N'@ImportFailed', N'number', N'{IMPORT_FAILED_ID}');
"""

ADD_DB_ACTION_PARAMETER_QUERY = """
SET NOCOUNT ON; 
INSERT INTO EventDatabaseActionParameters 
    (Created, Modified, ModifiedBy, EventDatabaseActionID, Name, DataType, ValueToken) 
VALUES 
    (GETDATE(), GETDATE(), -1, {EVENT_DB_ACTION_ID}, N'{PARAM_NAME}', N'number', N'{PARAM_VALUE}');
"""

ADD_EVENT_SCHEDULE_QUERY = """
SET NOCOUNT ON; 
INSERT INTO EventSchedules 
    (Created, Modified, ModifiedBy, IntervalType, StartTime, EndTime, ScheduleInterval, WeekDaysSelected, RecurrenceIntervalType, RecurrenceInterval, RecurrenceDay, MonthsSelected, DailyTimePeriod, EventConfigurationID, EnforceMaxRunTime, MaxRunTimeInterval, MaxRunTimeIntervalType) 
VALUES 
    (GETDATE(), GETDATE(), -1, 0, NULL, NULL, {INTERVAL_PERIOD}, 0, 0, 0, 0, 0, {INTERVAL_TYPE}, '{EVENT_CONFIG_ID}', 0, 60, 0);
"""

ADD_RETURN_PROP_TO_AI_QUERY = """
SET NOCOUNT ON; 
INSERT into AIOutputProperties ( Created , Modified , ParentId , ModifiedBy , Sequence , PropertyID , SourceColName , ScriptText , ReplaceExistingValues) 
VALUES (GETDATE(), GETDATE(), {AI_PROFILE_ID} , -1 , 0 , {PROP_ID}, '{COLUMN_NAME}' , NULL , NULL );
"""

GET_AI_PROFILE_NAMES = "SELECT ProfileName FROM AIProfiles"

GET_EVENT_TASK_NAMES = "SELECT Name FROM EventAutomatedTasks"

DROP_STAGING_TABLES_QUERY = """
IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Custom_StagingTable_Header' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    DROP TABLE Custom_StagingTable_Header, Custom_StagingTable_Details;
END
IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Custom_StagingTable_Details' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    DROP TABLE Custom_StagingTable_Details;
END
"""

DELETE_ALWAYS_RUN = """
-- Always run scripts installed - uninstalled
IF EXISTS (SELECT 1 FROM sys.procedures WHERE name = 'Custom_DocumentExportFromPropertys' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    DROP PROCEDURE dbo.Custom_DocumentExportFromPropertys;
END
IF EXISTS (SELECT 1 FROM sys.procedures WHERE name = 'Custom_DocumentExport_MonitorTable' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    DROP PROCEDURE dbo.Custom_DocumentExport_MonitorTable;
END
IF EXISTS (SELECT 1 FROM sys.procedures WHERE name = 'Custom_DocumentExport_AI_IndexProperties' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    DROP PROCEDURE dbo.Custom_DocumentExport_AI_IndexProperties;
END

IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Custom_StagingTable_Header' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    DROP TABLE Custom_StagingTable_Header, Custom_StagingTable_Details;
END
IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Custom_StagingTable_Details' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    DROP TABLE Custom_StagingTable_Details;
END
"""

DELETE_STAGING_WF_AI = """
-- Delete staging WF AI
DELETE FROM dbo.WorkflowActivityAIProfiles 
WHERE WorkflowActivityAIProfileID = {STAGING_WF_AI_ID};
"""

DELETE_STAGED_WF_AI = """
-- Delete staged WF AI
DELETE FROM dbo.WorkflowActivityAIProfiles 
WHERE WorkflowActivityAIProfileID = {STAGED_WF_AI_ID};
"""

DELETE_EVENT_DBA = """
DELETE FROM dbo.EventDatabaseActionParameters 
WHERE EventDatabaseActionID = {EVENT_DB_ACTION_ID};
DELETE FROM  dbo.EventDatabaseActions 
WHERE EventDatabaseActionID = {EVENT_DB_ACTION_ID};
"""

DELETE_EVENT_TASK = """
DELETE FROM [dbo].[EventAutomatedTasks] 
WHERE EventAutomatedTaskID = {EVENT_TASK_ID};
"""

DELETE_EVENT_CONFIG = """
DELETE FROM EventSchedules 
WHERE EventConfigurationID = '{EVENT_CONFIG_ID}';
"""

DELETE_INDEX_AI = """
-- Delete Index AI related table rows
DELETE FROM AIOutputProperties where ParentID = {INDEX_PROP_AI_ID};
DELETE FROM [dbo].[DocTypeAIProfiles] where AIProfileID = {INDEX_PROP_AI_ID};
DELETE FROM [dbo].[AIProfiles] where AIProfileID = {INDEX_PROP_AI_ID};
"""

DELETE_EXPORT_AI = """
-- Delete Export AI related table rows
DELETE FROM AIOutputProperties where ParentID = {EXPORT_AI_ID};
DELETE FROM [dbo].[DocTypeAIProfiles] where AIProfileID = {EXPORT_AI_ID};
DELETE FROM [dbo].[AIProfiles] where AIProfileID = {EXPORT_AI_ID};
"""

GET_WORKFLOW_QUEUES_QUERY = "SELECT * FROM [dbo].[WorkflowQueues]"
GET_WORKFLOW_NEXT_ACTIVITY_QUERY = "SELECT * FROM [dbo].[WorkflowNextActivity]"
GET_WORKFLOW_PLACEMENT_QUERY = "SELECT * FROM [dbo].[WorkflowPlacements]"
