"""
LDS main program
"""
### IMPORTING LIBRARIES
import csv
import pycountry_convert as pcc
import pytz
import pyodbc

### IMPORTING FUNCTIONS FROM LDS_module.py
from LDS_module import header, convert, extract, addGeoDimension, cleaner, addDateDimension, addIsCorrect, mapping, addDescription, mergeDate, aggregate, toCsv, uploadTable

################### MAIN ##############################
def main():
    
    file_input = '.\\answerdatacorrect.csv'
    file_input_sm = '.\\subject_metadata.csv'
    index_attr = header(file_input)
    
    # Fieldnames
    fieldnames_geography = ['geoid', 'region','country_name','continent']
    fieldnames_date = ['dateid', 'date', 'day', 'month','quarter', 'year']
    fieldnames_user = ['userid', 'dateid','geoid','gender']
    fieldnames_organization = ['organizationid','groupid','quizid','schemeofworkid']
    fieldnames_subject = ['subjectid', 'description']
    fieldnames_answers = ['answerid', 'questionid','userid','dateid','subjectid','answer_value', 'correct_answer','confidence', 'iscorrect','organizationid']
    
    # File output
    fOut_geography = '.\\Geography.csv'
    fOut_date = '.\\Date.csv'
    fOut_user = '.\\User.csv'
    fOut_organization = '.\\Organization.csv'
    fOut_subject = '.\\Subject.csv'
    fOut_answers = '.\\Answers.csv'
    
    # GEOGRAPHY TABLE 
    attr_geo = ['Region', 'CountryCode']
    Geography = extract(file_input, attr_geo, index_attr, sur_Key = True) 
    # Add Continent and CountryName
    idx_countrycode = attr_geo.index('CountryCode')
    addGeoDimension(Geography, idx_countrycode)  
    toCsv(Geography, fOut_geography, fieldnames_geography)
    
    # DATE TABLE 
    attr_db = ['DateOfBirth']
    attr_da = ['DateAnswered']
    DateOfBirth = extract(file_input, attr_db, index_attr, sur_Key = True) 
    DateAnswered = extract(file_input, attr_da, index_attr, sur_Key = True)
    idx_da = attr_da.index('DateAnswered')
    cleaner(DateAnswered, idx_da)
    mergeDate(DateAnswered, DateOfBirth)
    Date = addDateDimension(DateOfBirth)
    toCsv(Date, fOut_date, fieldnames_date)
    
    # USER TABLE 
    attr_user =  ['UserId', 'DateOfBirth', 'Region', 'Gender']
    User = extract(file_input, attr_user, index_attr, sur_Key = False)
    # Mapping User->Date
    idx_db = attr_user.index('DateOfBirth')-1 # -1 because UserId will be key, 'DateOfBirth' is shifted one position backward
    idx_date = 0 # index of Date in the dictionary Date (dict_date)
    mapping(User, Date, idx_db, idx_date )
    # Mapping User->Geography 
    idx_region = attr_user.index('Region')-1
    idx_geoid = 0 # Index of Region in Geography
    mapping(User, Geography, idx_region, idx_geoid)
    toCsv(User, fOut_user, fieldnames_user)
     
    # ORGANIZATION TABLE
    attr_org = ['GroupId', 'QuizId','SchemeOfWorkId']
    Organization = extract(file_input, attr_org, index_attr, sur_Key = True)
    toCsv(Organization, fOut_organization, fieldnames_organization)
    
    #SUBJECT TABLE
    subject_metadata_header = header('.\\subject_metadata.csv')
    attr_subject_metadata = ['SubjectId', 'Name', 'ParentId', 'Level']
    dict_subject_metadata = extract(file_input_sm, attr_subject_metadata, subject_metadata_header, sur_Key = False)
    attr_subject = ['SubjectId']
    temp_subject = extract(file_input, attr_subject, index_attr, sur_Key = True)
    Subject = addDescription(temp_subject, dict_subject_metadata)
    toCsv(Subject, fOut_subject, fieldnames_subject)
    
    # ANSWER TABLE 
    attr_answer = ['AnswerId', 'QuestionId', 'UserId', 'GroupId', 'QuizId', 'SchemeOfWorkId', 'DateAnswered', 'SubjectId',
                  'AnswerValue', 'CorrectAnswer', 'Confidence']
    Answers = extract(file_input, attr_answer, index_attr, sur_Key= False)
    # Add IsCorrect
    idx_answervalue = attr_answer.index('AnswerValue')-1 
    idx_correctanswer = attr_answer.index('CorrectAnswer')-1 
    addIsCorrect(Answers, idx_answervalue, idx_correctanswer)
    # Clean DateAnswered
    idx_da = attr_answer.index('DateAnswered')-1  
    cleaner(Answers, idx_da)
    # Mapping Answers->Date
    idx_da = attr_answer.index('DateAnswered')-1 
    idx_date = 0 # index of Date in the dictionary Date (dict_date)
    mapping(Answers, Date, idx_da, idx_date)
    # Mapping Answer -> Organization
    idx_GroupId = attr_answer.index('GroupId')-1 
    idx_QuizId = attr_answer.index('QuizId')-1 
    idx_SchemeOfWorkId = attr_answer.index('SchemeOfWorkId')-1 
    aggregate(Answers, [idx_GroupId, idx_QuizId, idx_SchemeOfWorkId])
    aggregate(Organization, [0,1,2] ) #0,1,2 indices in Organization
    idx_aggregated = -1 # [idx_GroupId, idx_QuizId, idx_SchemeOfWorkId] is in position -1 (last position)
    idx_org = 0 #  [idx_GroupId, idx_QuizId, idx_SchemeOfWorkId] in table dic_org_aggregatted
    mapping(Answers, Organization, idx_aggregated, idx_org )
    toCsv(Answers, fOut_answers, fieldnames_answers)
    
    # Upload table
    server = 'tcp:131.114.72.230' 
    database = 'Group_13_DB' 
    username = 'Group_13' 
    password = 'TGZ04DUE' 
    connectionString = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password
    cnxn = pyodbc.connect(connectionString)
    cursor = cnxn.cursor()

    uploadTable('.\\Geography.csv', 'Group_13.Geography', cursor)
    uploadTable('.\\Date.csv', 'Group_13.Date', cursor)
    uploadTable('.\\Organization.csv', 'Group_13.Organization', cursor)
    uploadTable('.\\Subject.csv', 'Group_13.Subject', cursor)
    uploadTable('.\\User.csv', 'Group_13.Users', cursor)
    uploadTable('.\\Answers.csv', 'Group_13.Answers', cursor)
    cursor.close()

    
if __name__ == "__main__":
    main()             
