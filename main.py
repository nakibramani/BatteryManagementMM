import kel103
from kel103 import Kel103
from communication import KoradUdpComm
from BMDatabase import *


comm = KoradUdpComm("10.11.1.97", "10.11.0.200")
kel = Kel103(comm)
test = mainClass(kel)
test.Home()
