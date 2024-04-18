"""
LDS Module
"""
import csv
import pycountry_convert as pcc
import pytz
import pyodbc

"""
FUNCTIONS
"""

def header(fileIn):
    """ 
    header() function takes as input a csv file and extract if present its header. The function return a dictionary that 
    has as keys the names of the attributes and as values their position/index.
    has_header() method analyzes the sample text and return True if the first row appears to be a series of column headers.
    """
    with open(fileIn, newline='', encoding='utf-8-sig') as csvfile:
        if csv.Sniffer().has_header(csvfile.read()): # return True if the first row appears to be a series of column headers
            csvfile.seek(0) # file method seek() sets the file's current position at the offset 0 -> aboslute file positioning
            reader = csv.reader( csvfile )
            attributes = reader.__next__()  # takes the first line (header)  
            
            return {e:i for i, e in enumerate(attributes)}
        
        else: print('CSV has no header')


def convert(line):
    """
    convert() function takes as input a sequence and try to convert its elements in integer number
    otherwise they remain the original values. Each row read from the csv file is returned as a list of strings 
    by the reader method (no automatic conversion).
    """
    output = []
    for e in line:
        try:
            output.append(int(float(e)))
        except ValueError:
            output.append(e)
    
    return output



def extract(fileIn, attribute, attributesIndex, sur_Key=True):
    """
    extract() function takes as input
    1) fileIn: a csv file
    2) attribute: list of string that correspond to the name of the attributes column that we want to extract from fileIn
    3) attributesIndex: the complete header (fieldnames) of the csv file (i.e. a dictionary that has as key the attributes 
        names and as values their index starting from 0) (retrieved using the header() function)
    The output is a dictionary that has by default (sur_Key=True) as primary key a surrogate key and as values the 
    distinct rows, according to the selected attributes, of the csv file.
    If sur_Key=False the key in the dictionary is the value of the first attribute in the attribute parameter.
    """
    columns = [attributesIndex[e] for e in attribute] # indexes 

    seen = set()
    out = dict()
    
    with open(fileIn, newline='', encoding='utf-8-sig') as fIn:
        reader = csv.reader(fIn, skipinitialspace=True)   
        reader.__next__()    # skip the first line because is the header
        
        if sur_Key:
            surrogateKey = 1
            for row in reader:  # Each row read from the csv file is returned as a list of strings (no automatic conversion)
                line = tuple(convert([row[j] for j in columns])) # set contains only hashable items
                if line in seen: continue
                seen.add(line)
                out[surrogateKey] = list(line)  # convert line that is a tuple into a list
                surrogateKey += 1
        else:
            for row in reader:
                line = tuple(convert([row[j] for j in columns])) 
                if line in seen: continue
                seen.add(line)
                out[line[0]] = [x for i, x in enumerate(line) if i!=0] # line[0] is the first element in the attribute parameter
            
    return out


def addGeoDimension(dicIn, idx_countrycode):
    """
    Add continent and country_name (country_name replace country_code value)
    """
    for key, value in dicIn.items():
        country_code = value[idx_countrycode]
        
        # Given country_code add continent to the list
        try:
            continent = pcc.country_alpha2_to_continent_code(country_code.upper()) # pc.country_alpha2_to_continent_code wants uppercase
        except KeyError:
            if country_code == 'uk':
                continent = 'EU'
            else:
                raise KeyError("Country code not defined")
        value.append(continent)
        
        # Given country_code switched it into country_name
        try:
            value[idx_countrycode] = pytz.country_names[country_code]
        except KeyError: # catch the bug with UK: keep original code if name is not found
            if country_code == 'uk':
                value[idx_countrycode] = 'United Kingdom'
            else:
                raise KeyError("Country code not defined")
                

def cleaner(dictIn, idx_da):   
    """
    cleaner() function discards the hours and keeps only the date (used with DateAnswered were there is also the hour)
    """
    for key, value in dictIn.items():
        new_value = value[idx_da].strip().split()[0] # indexing 0 to take the first element (date)
        dictIn[key][idx_da] = new_value


def addDateDimension(dictIn):
    """
    addDateDimension() function takes as input a dictionary containing dates and return a dictionary adding 
    day, month, quarter and year dimensions, establishing a hierarchy between them.
    """
    out = dict()
    for key, value in dictIn.items():
        date = value[0]
        day = date
        x = date.split('-')
        month = "-".join([x[0],x[1]]) 
        year = "".join(x[0]) 
        temp_month = int(x[1])
        quarter_num = (temp_month-1)//3 + 1
        quarter = year + '-Q' + str(quarter_num)
        out[key] = value + [day,month,quarter, year] 

    return out


def addIsCorrect(dictIn, idx_answer_value, idx_correct_answer):
    """
    addIsCorrect() function compares the variables answer value and correct answer of the answer table and set iscorrect 
    field 1 if they have the same value, 0 otherwise.
    """
    for key, value in dictIn.items():
        if value[idx_answer_value] == value[idx_correct_answer]:
            value.append(1)
        else:
            value.append(0) 


def mapping(dict_1, dict_2, idx_1, idx_2):
    """
    mapping() function takes as inputs two dictionaries. Given an attribute in the dict_1 find the surrogate key 
    of that attribute value in dict_2 and replace the value in dict_1 with that surrogate key
    the value of dict_1 in position idx_1 to the primary key of the value in position idx_2 of dict_2
    """
    def reverse_dict(dictIn, idx_2):
        return {tuple(value[idx_2]):key for key, value in dictIn.items()}
    
    dict_2_new = reverse_dict(dict_2, idx_2)
    
    for key, value in dict_1.items():
        x = tuple(value[idx_1])
        dict_1[key][idx_1] = dict_2_new[x]


def aggregate(dictIn, idx_attributes):
    """
    aggregate() function takes a dictionary and a list of indexes (attributes parameter)
    aggregates into a list the attributes' value for each key, the list is appended as the last element of the 
    values in the dictionary
    """
    for key, value in dictIn.items():
        x = [value[i] for i in idx_attributes]
        dictIn[key] = [value[i] for i, e in enumerate(value) if i not in idx_attributes]
        dictIn[key].append(x)


def addDescription(dict_1, dict_2): # dict_1=temp_subject, dict_2=dict_subject_metadata
    """
    addDescription() takes temp_subject and dict_subject_metadata as inputs. For each list of Subject IDs retrieve 
    the corresponding topics in the subject_metadata dictionary and create "description" which is a string describing 
    the various topics of the question in subject level order.
    Return Subject dictionary as output which has a surrogate key as key and "description" as value.
    """
    
    # convert SubjectId that is a string that has inside a list with the SubjectId values in a real list
    def fun(dictIn):
        return {k:[int(x) for x in v[0].replace("[", "").replace("]", "").split(",")] for k, v in dictIn.items()}
    
    dict_1_new = fun(dict_1)
    
    # Subject -> SubjectId is the string of attributes contained in SubjectId
    dictOut = dict()
    for key, value in dict_1_new.items():
        description = []
        for e in value:
            description.append(dict_2[e])
        description.sort(key=lambda x: (int(x[2])))   # sort on 'level' (third element, index=2)
        dictOut[str(value)] = ", ".join([x[0] for x in description]) # x[0] is the name of the subject (first element)
    
    return dictOut


def mergeDate(dict_1, dict_2): # dict_1=DateAnswered, dict_2=DateOfBirth
    """
    Merge DateOfBirth with DateAnswered (cleaned) adding the latter to the former
    """
    seen = set()
    sk = len(dict_2)+1 
    for key, value in dict_1.items():
        if value[0] in seen: continue
        seen.add(value[0])
        dict_2[sk] = [value[0]]
        sk += 1

def toCsv(dictionary, fOut, fieldnames):
    """
    toCsv() function converts a dictionary (given as input) to a csv file (fOut); 
    fieldnames is a list of string that are the names of the attributes.
    """
    with open(fOut, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if len(fieldnames) > 2:
            for key,value in dictionary.items():
                buffer = dict()
                i = 0
                buffer[fieldnames[i]] = key
                for e in value:
                    i += 1
                    buffer[fieldnames[i]] = e
                writer.writerow(buffer)
        else:
            for key, value in dictionary.items():
                buffer = dict()
                i = 0
                buffer[fieldnames[i]] = key
                buffer[fieldnames[i+1]] = value
                writer.writerow(buffer)



def uploadTable(filename, tablename, cursor):
    """
    uploadTbale() function takes as input filename, tablename, cursor. It performs
    the steps required in the connection protocol to upload the file in the database server.
    
    """
    with open (filename, 'r') as f:
        reader = csv.reader(f)
        columns = next(reader) 
        query = 'insert into {0}({1}) values ({2})'.format(tablename, ','.join(columns), ','.join('?'*len(columns)))
        for i, data in enumerate(reader):
            cursor.execute(query, data)
            if i%5000 == 0:
                cursor.commit()
        cursor.commit()


"""
MAIN
"""

def main():
    file_input = './answerdatasetnew/answerdatacorrect.csv'
    file_input_sm = './answerdatasetnew/subject_metadata.csv'
    index_attr = header(file_input)
    
    # Fieldnames
    fieldnames_geography = ['geoid', 'region','country_name','continent']
    fieldnames_date = ['dateid', 'date', 'day', 'month','quarter', 'year']
    fieldnames_user = ['userid', 'dateid','geoid','gender']
    fieldnames_organization = ['organizationid','groupid','quizid','schemeofworkid']
    fieldnames_subject = ['subjectid', 'description']
    fieldnames_answers = ['answerid', 'questionid','userid','dateid','subjectid','answer_value','correct_answer','confidence', 'iscorrect','organizationid']
    
    # File output
    fOut_geography = './csv/Geography.csv'
    fOut_date = './csv/Date.csv'
    fOut_user = './csv/User.csv'
    fOut_organization = './csv/Organization.csv'
    fOut_subject = './csv/Subject.csv'
    fOut_answers = './csv/Answers.csv'
    
    # GEOGRAPHY TABLE 
    attr_geo = ['Region', 'CountryCode']
    Geography = extract(file_input, attr_geo, index_attr) 
    # Add Continent and CountryName
    idx_countrycode = attr_geo.index('CountryCode')
    addGeoDimension(Geography, idx_countrycode)  
    toCsv(Geography, fOut_geography, fieldnames_geography)
    
    # DATE TABLE 
    attr_db = ['DateOfBirth']
    attr_da = ['DateAnswered']
    DateOfBirth = extract(file_input, attr_db, index_attr) 
    DateAnswered = extract(file_input, attr_da, index_attr)
    idx_da = attr_da.index('DateAnswered')
    cleaner(DateAnswered, idx_da)
    mergeDate(DateAnswered, DateOfBirth)
    Date = addDateDimension(DateOfBirth)
    toCsv(Date, fOut_date, fieldnames_date)
    
    # USER TABLE 
    attr_user =  ['UserId', 'DateOfBirth', 'Region', 'Gender']
    User = extract(file_input, attr_user, index_attr, sur_Key=False)
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
    Organization = extract(file_input, attr_org, index_attr)
    toCsv(Organization, fOut_organization, fieldnames_organization)
    
    # SUBJECT TABLE
    subject_metadata_header = header('./answerdatasetnew/subject_metadata.csv')
    attr_subject_metadata = ['SubjectId', 'Name', 'ParentId', 'Level']
    dict_subject_metadata = extract(file_input_sm, attr_subject_metadata, subject_metadata_header, sur_Key=False)
    attr_subject = ['SubjectId']
    temp_subject = extract(file_input, attr_subject, index_attr)
    Subject = addDescription(temp_subject, dict_subject_metadata)
    toCsv(Subject, fOut_subject, fieldnames_subject)
    
    # ANSWER TABLE 
    attr_answer = ['AnswerId', 'QuestionId', 'UserId', 'GroupId', 'QuizId', 'SchemeOfWorkId', 'DateAnswered', 'SubjectId','AnswerValue', 'CorrectAnswer', 'Confidence']
    Answers = extract(file_input, attr_answer, index_attr, sur_Key=False)
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
    
    #Upload table
    server = 'tcp:131.114.72.230' 
    database = 'Group_13_DB' 
    username = 'Group_13' 
    password = 'TGZ04DUE' 
    connectionString = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password
    cnxn = pyodbc.connect(connectionString)
    cursor = cnxn.cursor()
    uploadTable('./Geography.csv', 'Group_13.Geography', cursor)
    uploadTable('./Date.csv', 'Group_13.Date', cursor)
    uploadTable('./Organization.csv', 'Group_13.Organization', cursor)
    uploadTable('./Subject.csv', 'Group_13.Subject', cursor)
    uploadTable('./User.csv', 'Group_13.Users', cursor)
    uploadTable('./Answers.csv', 'Group_13.Answers', cursor)
    cursor.close()
    cnxn.commit() # non c'era
    cnxn.close() # non c'era

if __name__ == "__main__":
    main()
























