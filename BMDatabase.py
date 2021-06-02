from datetime import datetime
import time
import socket
from asammdf import MDF, Signal
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

bat_test_data = {
            'setting_id': 2,
            'max_current': 30,
            'set_current': 1,
            'voltage_cutoff': 3.5,
            'capacity_cutoff': 10,
            'time_cutoff': 10
        }
kel.set_battery_data(bat_test_data)


import mysql.connector
from mysql.connector import Error
try:
    databaseConnect = {'host':'localhost',
        'user': 'root',
        'password' "password123"
        'database': 'Electronics',
        'raise_on_warnings': True,
        'use_pure': False,
        'autocommit': True,}


    mydb = mysql.connector.connect(**databaseConnect)

    if mydb.is_connected():
        db_Info = mydb.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        #creating cursor instance
        my_cursor = mydb.cursor()
except Error as e:
    print("Error while connecting to MySQL", e)

#creating a databse
my_cursor.execute("CREATE DATABASE test123")

#creating a table
my_cursor.execute("CREATE TABLE batteryDatabase (BatteryID VARCHAR(255) PRIMARY KEY, Status VARCHAR(255) NOT NULL, Capacity INTEGER NOT NULL, DateTested DATE NOT NULL,Machine VARCHAR(255))")
my_cursor.execute("show tables")

#one-time use only


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
        ID = self.ScanBarcode()
        my_cursor.execute("SELECT * FROM batteryDatabase WHERE BatteryID = '{0}'".format(ID))
        x = my_cursor.fetchall()
        if not x: 
            print('Not Found')
            print('Redirecting to New battery test ')
            self.TestBattery()
        else:
            my_cursor.execute("SELECT * FROM batteryDatabase WHERE BatteryID = '{0}'".format(ID))
            for y in my_cursor:
                print(y)
            
            print("\n ")
            print("Please select one of the following options: ")
            print("1. Update battery status")
            print("2. Update battery Capacity")
            print("3. Update battery's Machine")
            print("4. Test Battery Again & Update")
            #takes user input
            Look = input("Enter a number from 1-4 to select an option")
            print(Look)

            Look = int(Look)

            while Look!=1 and Look!=2 and Look!=3 and Look!=4:
                print("Invalid Entry")
                Look = input("Enter a number from 1-3 to select an option")

            if Look==1:
                print("Select Status options: ")
                print("1. New")
                print("2. Good")
                Status = input("3. Out of Service   ")
                if Status=='1':
                    Status = "new"
                elif Status=='2':
                    Status = "Good"
                elif Status=='3':
                    Status = "Out of Service"

                my_cursor.execute("UPDATE batteryDatabase set Status = '{0}' WHERE BatteryID = '{1}'".format(Status, ID))
                print("Battery Status of battery {0} is updated to {1}".format(ID, Status))

            elif Look==2: 
                NewCapacity = input("Please enter new battery capacity: ")
                #NewCapacity = int (NewCapacity)
                
                my_cursor.execute("UPDATE batteryDatabase set Capacity = {0} WHERE BatteryID = '{1}'".format(NewCapacity,ID))
                print("Battery Capacity of battery '{0}' is updated to {1}".format(ID, NewCapacity))
            elif Look==3: 
                NewMachine = input("Please enter Machie information : ")
                
                my_cursor.execute("UPDATE batteryDatabase set Machine = '{0}' WHERE BatteryID = '{1}'".format(NewMachine, ID))
                print("Battery Capacity of battery '{0}' is updated to '{1}'".format(ID, NewMachine))
            elif Look == 4:
                self.TestBattery()

    def TestBattery(self):
        #declaring all the variables refer Kel103 lib to modify (currently only done for CC)
        cutOffVoltage = input("Enter Cutt-Off Voltage: ")
        cutOffCapacity = input("Enter Cutt-Off Capacity: ")
        dischargeRate = input("Enter discharge Current: ")
        timeStop = input("Enter Stop Time = ")
        maxCurrent = input("Enter max current = ")
        data = {"setting_id":"2", "max_current":maxCurrent, "set_current":dischargeRate, "voltage_cutoff":cutOffVoltage, "capacity_cutoff":cutOffCapacity, "time_cutoff":timeStop}


        kel.setOutput(False)
        print(kel.measure_all_params)
        StartTest = input("Enter anything to begin the test, or press 0 to reselect")

