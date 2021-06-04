from calendar import c
from datetime import datetime, date
import time
import socket
from asammdf import MDF, Signal
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from kel103 import Kel103

import mysql.connector
from mysql.connector import Error

"""
bat_test_data = {
            'setting_id': 2,
            'max_current': 30,
            'set_current': 1,
            'voltage_cutoff': 3.5,
            'capacity_cutoff': 10,
            'time_cutoff': 10
        }
kel.set_battery_data(bat_test_data)
"""

try:
    databaseConnect = {'host':'localhost',
        'user': 'root',
        'password' "password123"
        'raise_on_warnings': True,
        'use_pure': False,
        'autocommit': True,
        }


    mydb = mysql.connector.connect(host="localhost",
        user="root",
        password="password123",
        database= "test123",
        autocommit= True
    )

    if mydb.is_connected():
        db_Info = mydb.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        #creating cursor instance
        my_cursor = mydb.cursor()
except Error as e:
    print("Error while connecting to MySQL", e)


#creating a databse
#my_cursor.execute("CREATE DATABASE MMBatteryDB")

#creating a table
#my_cursor.execute("CREATE TABLE batteryDatabase (BatteryID VARCHAR(255) PRIMARY KEY, Status VARCHAR(255) NOT NULL, Capacity INTEGER NOT NULL, DateTested DATE NOT NULL,Machine VARCHAR(255))")
#my_cursor.execute("CREATE TABLE Tests (TestID int PRIMARY KEY AUTO_INCREMENT, BatteryID VARCHAR(255) NOT NULL, FOREIGN KEY(BatteryID) REFERENCES batterydatabase(BatteryID), TestDate DATE NOT NULL, CapacityMeasured int NOT NULL)")
#my_cursor.execute("CREATE TABLE TestData (Time TIME PRIMARY KEY NOT NULL, TestID int NOT NULL, FOREIGN KEY(TestID) REFERENCES Tests(TestID), Voltage decimal NOT NULL, Capacitance decimal NOT NULL)")
sqlInsertion = "INSERT INTO batterydatabase (BatteryID, Status, Capacity, DateTested, Machine) VALUES (%s,%s,%s,%s,%s)"
TestSQLInsertion = "INSERT INTO tests (BatteryID, TestDate, CapacityMeasured) VALUES (%s, %s, %s)"
DataSQLInsertion = "INSERT INTO testdata (Time, TestID, Voltage, Capacitance) VALUES (%s, %s, %s, %s)"


#battery1= ("NSA721512071160", "Good", 4000, date.today(), 8)
#my_cursor.execute(sqlInsertion, battery1)


#test1= ("NSA721512071160", date.today(), 8000)
#my_cursor.execute(TestSQLInsertion, test1)

#testdata= (Time, date.today(), 8000)
#my_cursor.execute(DataSQLInsertion, testdata)

class BatteryTestData(object):
    def __init__(self, cell_id, start_time=datetime.now()):
        self.cell_id = cell_id
        self.start_time = start_time
        self.timestamps = []
        self.data = {'v': [], 'c': [], 'p': [], 'cap':[], 't':[]}

        

        # for now data structure is:
        # test_timestamps - list of python times
        # test_data - list of dictionaries
        #   {'v': voltage, 'c': current, 'p': power, 'cap': capacity, 't': time(from kel)}

    def new_sample(self, data, timestamp=datetime.now()):
        self.timestamps.append(timestamp)
        for i in data:
            self.data[i].append(data[i])

    def export_to_mf4(self):
        print("exporting to mf4")
        timestamps = np.array(self.data['t'])
        voltages = Signal(samples=np.array(self.data['v'], dtype=np.float32),
                 timestamps=timestamps,
                 name='Voltage',
                 unit='V')
        currents = Signal(samples=np.array(self.data['c'], dtype=np.float32),
                 timestamps=timestamps,
                 name='Current',
                 unit='A')
        powers = Signal(samples=np.array(self.data['p'], dtype=np.float32),
                 timestamps=timestamps,
                 name='Power',
                 unit='W')
        capacities = Signal(samples=np.array(self.data['cap'], dtype=np.float32),
                 timestamps=timestamps,
                 name='Capacity',
                 unit='AH')
        
        mdf4 = MDF(version='4.10')
        signals = [voltages, currents, powers, capacities]
        mdf4.start_time = self.start_time
        mdf4.append(signals, comment='Battery test: {}'.format(self.cell_id))
        mdf4.save("test.mf4", overwrite=True)
        return mdf4


class KelBatteryDischargeTest(object):

    def __init__(self, kel_device, measurement_period=1):
        self.kel = kel_device
        self.measurement_period = measurement_period
        self.bat_test_data = {}
        self.test_data = None

    def setup_for_test(self, cell_id, use_rear_voltage_measure, set_current, voltage_cutoff, capacity_cutoff=99, time_cutoff=99):
        if self.test_data == None:
            self.test_data = BatteryTestData(cell_id)
        self.kel.check_device()
        self.bat_test_data = {
            'setting_id': 2,
            'max_current': 30,
            'set_current': set_current,
            'voltage_cutoff': voltage_cutoff,
            'capacity_cutoff': capacity_cutoff,
            'time_cutoff': time_cutoff,
        }
        self.kel.set_battery_data(self.bat_test_data)
        self.use_rear_voltage_measure = use_rear_voltage_measure
        self.kel.set_comp(self.use_rear_voltage_measure)

    def check_end_test(self):
        try:
            if self.kel.get_output() == False or self.kel.measure_voltage() < self.bat_test_data['voltage_cutoff']:
                return True
            return False
        except socket.timeout:
            print("Timeout checking to end test at {}".format(datetime.now()))
            return False

    def get_kel_datapoint(self):
        v = self.kel.measure_voltage()
        c = self.kel.measure_current()
        p = self.kel.measure_power()
        cap = self.kel.get_battery_capacity()
        t = self.kel.get_battery_time()
        testData = mainClass(self) 
        testData.TestsDatabaseEntry(t, v, cap)
        time.sleep(10)
        return {'v': v, 'c': c, 'p': p, 'cap': cap, 't': t}


    def run_test(self):
        try:
            # Confirm settings are correct before test begins!
            if self.kel.get_func() != "BATTERY":
                raise ValueError("KEL Not in BATTERY Mode, can not do test!")
            if self.kel.get_battery_data(self.bat_test_data['setting_id']) != self.bat_test_data:
                print("bat data should be: {}".format(self.bat_test_data))
                print("bat data is: {}".format(self.kel.get_battery_data(self.bat_test_data['setting_id'])))
                raise ValueError("KEL bat data not set properly, can not do test!")
            if self.use_rear_voltage_measure != self.kel.get_comp():
                raise ValueError("KEL voltage measure device not set properly, can not do test!")

            # turn on output and begin test
            print("turning on output and beginning test")
            self.kel.set_output(True)
            
            self.test_data.new_sample(self.get_kel_datapoint())
            while not self.check_end_test():
                try:
                    test_point = self.get_kel_datapoint()
                    print("got test data: {}".format(test_point))
                    self.test_data.new_sample(test_point)
                    time.sleep(self.measurement_period)
                except socket.timeout:
                    print("Missed test data point at: {}".format(datetime.now()))

            if self.check_end_test():
                retData = mainClass()
                retData.DatabaseEntry(self.c)                      ################################################################
            
        except KeyboardInterrupt:
            print("keyboard interrupt encountered, exiting test")
            self.kel.set_output(False)
        except Exception as e:
            print("Other fatal error occrred at {}, shutting down output and ending test.".format(datetime.now))
            self.kel.set_output(False) # set output false multiple times to ensure it works
            time.sleep(1)
            self.kel.set_output(False)
            time.sleep(1)
            self.kel.set_output(False)
            raise e

    def export_results(self):
        mdf4 = self.test_data.export_to_mf4()
        file_name = '{}-cell-{}.mf4'.format(self.test_data.start_time.strftime('%Y-%m-%d'), self.test_data.cell_id)
        print("exporting to filename: {}".format(file_name))
        mdf4.save(file_name, overwrite=True)

class mainClass(object):

    def __init__(self, kel_device, measurement_period=1):
        self.kel = kel_device
        self.measurement_period = measurement_period

    def ScanBarcode(self):
        #Scans barcode data
        BarcodeData = input("Scan a barcode now:")
        print(BarcodeData)

        while len(BarcodeData)!=15:
            print("Wrong barcode Data!!!")
            BarcodeData = input("Scan a barcode now:")
            print(BarcodeData)

        return BarcodeData

    def Home(self):
        print("MinMaster Battery Management Database V1.0: \n\n")

        self.ID = self.ScanBarcode()
        my_cursor.execute("SELECT * FROM batteryDatabase WHERE BatteryID = '{0}'".format(self.ID))
        
        x = my_cursor.fetchall()
        if not x: 
            print('Not Found')
            print('Redirecting to New battery test: ')
            self.TestBattery()
        else:
            my_cursor.execute("SELECT * FROM batteryDatabase WHERE BatteryID = '{0}'".format(self.ID))
            for y in my_cursor:
                print(y)
            
            print("\n ")
            print("Please select one of the following options: ")
            print("1. Update battery Status")
            print("2. Update battery's Vehicle ID")
            print("3. Test Battery Again")
            print("4. Lookup Test Battery")
            print("5. Return to Main Menu")
            #takes user input
            Look = input("Enter a number from 1-4 to select an option")
            print(Look)

            Look = int(Look)

            while Look!=1 and Look!=2 and Look!=3 and Look!=4:
                print("Invalid Entry")
                try:
                    Look = int(input("Enter a number from 1-4 to select an option"))
                except ValueError:
                    print("Not an integer!!!")

            if Look==1:
                print("Select Status options: ")
                print("1. New")
                print("2. Good")
                print("3. Out of Service")
                print("4. Return to Main Menu")
                Status = int(input("Please enter a number from 1-3 to select battery status:  "))
                while Status!=1 and Status!=2 and Status!=3 and Status!=4:
                    print("Invalid Entry")
                    try:
                        Status = int(input("Enter a number from 1-4 to select an option"))
                    except ValueError:
                        print("Not an integer!!!")

                if Status==1:
                    Status = "new"
                elif Status==2:
                    Status = "Good"
                elif Status==3:
                    Status = "Out of Service"
                elif Status ==4:
                    self.Home()

                my_cursor.execute("UPDATE batteryDatabase set Status = '{0}' WHERE BatteryID = '{1}'".format(Status, self.ID))
                print("Battery Status of battery {0} is updated to {1}".format(self.ID, Status))
                self.Home()

            elif Look==2: 
                NewMachine = input("Please enter Machine information : ")
                
                my_cursor.execute("UPDATE batteryDatabase set Machine = '{0}' WHERE BatteryID = '{1}'".format(NewMachine, self.ID))
                print("Battery Capacity of battery '{0}' is updated to '{1}'".format(self.ID, NewMachine))
                self.Home()
            elif Look == 3:
                self.TestBattery()
                self.Home()
            elif Look == 4:
                my_cursor.execute("SELECT * FROM Tests WHERE BatteryID = '{0}'".format(self.ID))
                for y in my_cursor:
                    print(y)
                
                a = input("Press 1 to lookup the graph of preview battery test")
                if a:
                    TestID = 1
                    self.getGraph(TestID)
                self.Home()
            elif Look ==5:
                self.Home()

    def TestBattery(self):
        self.test = KelBatteryDischargeTest(self.kel)
        print("Please select one of the following options: ")
        print("1. Perform standard battery test")
        print("2. Perform custom battery test")
        print("3. Return to Main Menu")
        #takes user input
        tst = input("Enter a number from 1-4 to select an option")
        print(tst)

        tst = int(tst)

        while tst!=1 and tst!=2 and tst!=3:
            print("Invalid Entry")
            try:
                tst = int(input("Enter a number from 1-3 to select an option"))
            except ValueError:
                    print("Not an integer!!!")

        x = "y"
        while x =="y":
            if tst==1:
                cutOffVoltage = 2.6
                cutOffCapacity = 999
                self.dischargeRate = 7
                timeStop = 120
                self.test.setup_for_test(self.ID, True, 7, 2.6, 999, 120)
            elif tst==2:
                confirmParameters= 1
                while confirmParameters:
                    cutOffVoltage = input("Enter Cutt-Off Voltage: ")
                    cutOffCapacity = input("Enter Cutt-Off Capacity: ")
                    self.dischargeRate = input("Enter discharge Current: ")
                    timeStop = input("Enter Stop Time = ")
                    
                self.test.setup_for_test(self.ID, True, self.dischargeRate, cutOffVoltage, cutOffCapacity, timeStop)
            elif tst==3:
                self.Home()
            
            print("Please press Y to confirm the parameters, or press anything to cancel: ")
            print("Cutt-off Voltage = {0}, Cutt-off Capacity = {1}, Discharge Rate = {2}, Time Stop = {3}".format(cutOffVoltage, cutOffCapacity, self.dischargeRate, timeStop))
            x = input()
        
        self.test.run_test()
        self.test.export_results()

    def DatabaseEntry(self, NewCapacity, Status=None):
        my_cursor = mydb.cursor()
        if NewCapacity>=5000 and Status is not None:
            Status = "New"
        elif NewCapacity>=3000 and NewCapacity<5000 and Status is not None:
            Status = "Good"
        elif NewCapacity>3000 and Status is not None:
            Status = "Out of Service"
            print("Press a number from Y to delete '{}' battery data from ALL databases: ".format(self.ID))
            my_cursor.execute("DELETE FROM batteryDatabase WHERE BatteryID= {0}".format(self.ID))
            my_cursor.execute("DELETE FROM tests WHERE BatteryID= {0}".format(self.ID))
        #entry into database
        
        my_cursor.execute("SELECT * FROM batteryDatabase WHERE BatteryID = '{0}'".format(self.ID))
        x = my_cursor.fetchall()
        if not x: #create new entry
            battery1 = (self.ID, 'Status', self.capacity, date.today())
            my_cursor.execute(sqlInsertion, battery1)

            test1= (self.ID, date.today(), self.capacity, self.dischargeRate)
            my_cursor.execute(TestSQLInsertion, test1)
        else:
            my_cursor.execute("UPDATE batteryDatabase set Status = '{0}' WHERE BatteryID = '{1}'".format(Status, self.ID))
            my_cursor.execute("UPDATE batteryDatabase set Capacity = {0} WHERE BatteryID = '{1}'".format(NewCapacity,self.ID))
            my_cursor.execute("UPDATE batteryDatabase set DateTested = {0} WHERE BatteryID = '{1}'".format(date.today(),self.ID))
            
            #add to tests
            test1= (self.ID, date.today(), self.capacity, self.dischargeRate)
            my_cursor.execute(TestSQLInsertion, test1)


    def TestsDatabaseEntry(self, Time, Voltage, Capacity):
        my_cursor.execute("SELECT MAX(TestID)  FROM tests")
        x = my_cursor.fetchall()
        T = str(x).strip('[](),')
        print(Time)
        testdata= (Time, T, Voltage, Capacity)
        my_cursor.execute(DataSQLInsertion, testdata)


    def getGraph(self, TestID):
        Volt = []
        cap = []
        my_cursor.execute("SELECT Voltage, Capacitance FROM testdata WHERE TestID = {} ORDER BY TIME".format(TestID))

        for (Voltage, Capacitance) in my_cursor:
            print("{0}  , {1} ".format(Voltage, Capacitance))
            
            #TimeAsInt = int(Time)
            #TimeArray.append(TimeAsInt)
            Volt.append(Voltage)
            cap.append(Capacitance)
        fig = plt.figure()

        plt.plot(Volt, label='Voltage')
        plt.show()

        plt.plot(cap, label='Capacity')
        plt.show()
