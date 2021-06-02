from BatteryManagementMM import Kel103, KoradUdpComm, BMDatabase
comm = KoradUdpComm("10.11.1.16", "10.11.0.200")
kel = Kel103(comm)
test = mainClass(kel)
test.Home()
