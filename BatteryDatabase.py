import datetime
from datetime import date
import time
import mysql.connector
from mysql.connector import Error


sqlInsertion = "INSERT INTO batteryDatabase (BatteryID, Status, Capacity, DateTested, Machine) VALUES (%s,%s,%s,%s,%s)"
TestSQLInsertion = "INSERT INTO Tests (BatteryID, TestDate, CapacityMeasured, Current) VALUES (%s, %s, %s, %s)"
DataSQLInsertion = "INSERT INTO TestData (Time, TestID, Voltage, Capacitance) VALUES (%s, %s, %s, %s)"


try:
    databaseConnect = {'host':'localhost',
        'user': 'root',
        'password' "password123"
        'raise_on_warnings': True,
        'use_pure': False,
        'autocommit': True,
        }
    """

    mydb = mysql.connector.connect(host="localhost",
        user="root",
        password="password123",
        database= "test123",
        autocommit= True
    )
    """
    mydb = mysql.connector.connect(host= '10.11.0.117',
        port = 3307,
        user="battery_db_user",
        password="test123",
        database= "battery_data",
        autocommit= True,
        buffered = True
    )

    if mydb.is_connected():
        db_Info = mydb.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        #creating cursor instance
        my_cursor = mydb.cursor()
except Error as e:
    print("Error while connecting to MySQL", e)


class database(object):
    def _init_(self):
        x = 1
    
    def create_database():
        #my_cursor.execute("CREATE TABLE batteryDatabase (BatteryID VARCHAR(255) PRIMARY KEY, Status VARCHAR(255) NOT NULL, Capacity INTEGER NOT NULL, DateTested DATE NOT NULL,Machine VARCHAR(255))")
        #my_cursor.execute("CREATE TABLE Tests (TestID int PRIMARY KEY AUTO_INCREMENT, BatteryID VARCHAR(255) NOT NULL, FOREIGN KEY(BatteryID) REFERENCES batterydatabase(BatteryID), TestDate DATE NOT NULL, CapacityMeasured int NOT NULL)")
        #my_cursor.execute("CREATE TABLE TestData (Time TIME PRIMARY KEY NOT NULL, TestID int NOT NULL, FOREIGN KEY(TestID) REFERENCES Tests(TestID), Voltage decimal NOT NULL, Capacitance decimal NOT NULL)"
        #my_cursor.execute("ALTER TABLE TestData DROP PRIMARY KEY")
        #my_cursor.execute("ALTER TABLE TestData ADD RecordID INT NOT NULL AUTO_INCREMENT PRIMARY KEY")
        #my_cursor.execute("ALTER TABLE TestData MODIFY Capacitance float(7,3) NOT NULL")
        x = 1

    def batteryDatabase_entry(self, ID):
        battery1 = (ID, 'none', 0, date.today(), None)
        my_cursor.execute(sqlInsertion, battery1)

    def TestData_entry(self, ID):
        test1= (ID, date.today(), 0, 0)
        my_cursor.execute(TestSQLInsertion, test1)

    def Test_Entry():
        print("this is empty")


    def batteryDatabase_Fetch(self, ID): 
        my_cursor.execute("SELECT * FROM batteryDatabase WHERE BatteryID = '{0}'".format(ID))
        return my_cursor.fetchall()

    def Tests_Fetch(self, ID):
        my_cursor.execute("SELECT * FROM Tests WHERE BatteryID = '{0}'".format(ID))
        return my_cursor.fetchall()

    def testData_Fetch(self, TestID): 
        my_cursor.execute("SELECT Voltage, Capacitance FROM TestData WHERE TestID = {} ORDER BY TIME".format(TestID))
        return my_cursor.fetchall()

    def batteryDatabase_Update(self, ID, Status=None, NewCapacity=None):
        if Status != None:
            my_cursor.execute("UPDATE batteryDatabase set Status = '{0}' WHERE BatteryID = '{1}'".format(Status, ID))
        if NewCapacity!= None:
            my_cursor.execute("UPDATE batteryDatabase set Capacity = {0} WHERE BatteryID = '{1}'".format(NewCapacity, ID))
        my_cursor.execute("UPDATE batteryDatabase set DateTested = CURRENT_DATE() WHERE BatteryID = '{0}'".format(ID))

    def Tests_Update(self, ID, NewCapacity, dischargeRate):
        my_cursor.execute("UPDATE Tests set CapacityMeasured = {0} WHERE BatteryID = '{1}'".format(NewCapacity, ID))
        my_cursor.execute("UPDATE Tests set Current = {0} WHERE BatteryID = '{1}'".format(dischargeRate, ID))

    def batteryDatabase_UpdateMachine(self, ID, NewMachine):
        my_cursor.execute("UPDATE batteryDatabase set Machine = '{0}' WHERE BatteryID = '{1}'".format(NewMachine, ID))

    def TestData_Entry(self, Time, Voltage, Capacity):

        my_cursor.execute("SELECT MAX(TestID) FROM Tests")
        x = my_cursor.fetchall()
        T = str(x).strip('[](),')
        
        Time = Time*60
        print(Time)
        #Time = my_cursor.execute("SELECT SEC_TO_TIME({})".format(Time))
        Time = str(datetime.timedelta(seconds=Time
        ))
        print(Time)
        ##############################Check format of time recieved from battery############################################
        testdata= (Time, T , Voltage, Capacity)
        my_cursor.execute(DataSQLInsertion, testdata)

    def deleteAll(self, ID):  
        my_cursor.execute("SELECT TestID FROM Tests WHERE BatteryID = '{}'".format(ID))
        y = my_cursor.fetchone()
        y = str(y).strip('[](),')  
        y = int(y)
        print(y)


        while y is not None:
            my_cursor.execute("SELECT * FROM TestData WHERE TestID = {} ORDER BY TIME".format(y))
            x = my_cursor.fetchall()
            if not x:
                print("Already Deleted for TestID = {}".format(y))
                my_cursor.execute("DELETE FROM Tests WHERE TestID= {0}".format(y))
            else:
                my_cursor.execute("DELETE FROM battery_data.TestData WHERE TestID= {0}".format(y))
                my_cursor.execute("DELETE FROM Tests WHERE TestID= {0}".format(y))
            my_cursor.execute("SELECT TestID FROM Tests WHERE BatteryID = '{}'".format(ID))
            y = my_cursor.fetchone()
            
            if y is not None: 
                y = str(y).strip('[](),') 
                y = int(y)

        """
        for y in my_cursor:
            y = str(y).strip('[](),')
            
            y = int(y)
            
            print(y)
            
            my_cursor.execute("SELECT * FROM TestData WHERE TestID = {} ORDER BY TIME".format(y))
            x = my_cursor.fetchall()
            if not x:
                print("Already Deleted for TestID = {}".format(y))
                my_cursor.execute("DELETE FROM Tests WHERE TestID= {0}".format(y))
            else:
                my_cursor.execute("DELETE FROM battery_data.TestData WHERE TestID= {0}".format(y))
                my_cursor.execute("DELETE FROM Tests WHERE TestID= {0}".format(y))
        """
        
        my_cursor.execute("DELETE FROM batteryDatabase WHERE BatteryID= '{0}'".format(ID))
