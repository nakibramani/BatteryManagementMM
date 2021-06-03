from .communication import KoradUdpComm

class Kel103(object):

    def __init__(self, kel_comm):
        self.device = kel_comm
        self.device.connect()

    def device_info(self):
        return self.device.send_receive('*IDN?')
    
    def check_device(self):
        if 'KEL103' in self.device_info():
            return True
        else:
            return False

    def get_generic_boolean(self, setting_name):
        s = self.device.send_receive(':{}?'.format(setting_name))
        if 'OFF' in s:
            return False
        if 'ON' in s:
            return True

    def set_generic_boolean(self, setting_name, state):
        self.device.send(':{0} {1:d}'.format(setting_name, state))
        if self.get_generic_boolean(setting_name) != state:
            raise ValueError('Caution: {} not set'.format(setting_name))

    def get_output(self):
        return self.get_generic_boolean('INP')

    def set_output(self, state):
        self.set_generic_boolean('INP', state)

    def get_comp(self):
        return self.get_generic_boolean('SYST:COMP')

    def set_comp(self, state):
        self.set_generic_boolean('SYST:COMP', state)

    def shutdown(self):
        ''' Turn off output and end communications '''
        self.set_output(False)
        self.end_comm()
        
    def end_comm(self):
        self.device.close()

    def get_func(self):
        s = self.device.send_receive(':FUNC?')
        return s.strip('\n')

    def set_func(self, func_type):
        ''' func options: 
        CC = Constant Current
        CV = Constant Voltage
        CR = Constant Resistance
        CW = Constant Wattage
        SHORt = ???'''
        self.device.send(':FUNC {}'.format(func_type.upper()))
        if self.get_func() != func_type.upper():
            raise ValueError('Caution: {} not set properly'.format('FUNC'))

    def set_constant_current(self):
        self.set_func('CC')

    def set_constant_power(self):
        self.set_func('CW')
        
    def set_constant_resistance(self):
        self.set_func('CR')

    def get_generic_float(self, setting_name, units=''):
        return float(self.device.send_receive(':{}?'.format(setting_name)).strip('{}\n'.format(units)))

    def measure_voltage(self):
        return self.get_generic_float('MEAS:VOLT', 'V')

    def measure_power(self):
        return self.get_generic_float('MEAS:POW', 'W')

    def measure_current(self):
        return self.get_generic_float('MEAS:CURR', 'A')

    def measure_all_params(self):
        return {"voltage": self.measure_voltage(), "current": self.measure_current(), "power": self.measure_power()}

    def set_generic_float(self, setting_name, value, units, precision=3):
        # tod0: test 3 decimal places!
        self.device.send(':{0} {1:.{prec}f}{2}'.format(setting_name, value, units, prec=precision))
        if self.get_generic_float(setting_name, units) != value:
            raise ValueError('{} set incorectly on the device'.format(setting_name))
        

    def set_current(self, current):
        self.set_generic_float("CURR", current, "A")

    def get_current_setpoint(self):
        return self.get_generic_float('CURR', "A")
    
    def set_power(self, power):
        self.set_generic_float("POW", power, "W")

    def get_power_setpoint(self):
        return self.get_generic_float('POW', "W")

    def set_voltage(self, voltage):
        self.set_generic_float("VOLT", voltage, "V")

    def get_voltage_setpoint(self):
        return self.get_generic_float('VOLT', "V")

    def set_current_max(self, current):
        raise NotImplementedError("Setting max values not yet implemented")

    def set_voltage_max(self, voltage):
        raise NotImplementedError("Setting max values not yet implemented")
        
    def set_power_max(self, Power):
        raise NotImplementedError("Setting max values not yet implemented")

    def get_battery_data(self, setting_id):
        self.device.send(":RCL:BATT {}".format(setting_id))
        list_data = self.device.send_receive(':RCL:BATT?').split(',')

        data = {
            'setting_id': setting_id,
            'max_current': float(list_data[0].replace("A", "")),
            'set_current': float(list_data[1].replace("A", "")),
            'voltage_cutoff': float(list_data[2].replace("V", "")),
            'capacity_cutoff': float(list_data[3].replace("AH", "")),
            'time_cutoff': float(list_data[4].replace("M", "")),
        }
        return data

    def set_battery_data(self, data):
        # NOTE: KEL103 must have battery setting 2 applied first, then battery settings 0 and 1 get "unlocked" and can be used!
        # Note: see get_battery_data for formatting of incomming data dict
        send = ':BATT {setting_id},{max_current}A,{set_current}A,{voltage_cutoff}V,{capacity_cutoff}AH,{time_cutoff}M'.format(**data)
        print(send)
        self.device.send(send)

        if self.get_battery_data(data['setting_id']) != data:
            raise ValueError('Batt data may be set incorrectly on the device'.format(data['setting_id'])) 

    def get_battery_time(self):
        return self.get_generic_float('BATT:TIM', "M")

    def get_battery_capacity(self):
        return self.get_generic_float('BATT:CAP', "AH")

    def set_keyboard_lock(self, locked):
        self.set_generic_boolean('SYST:LOCK', locked)

    def get_keyboard_lock(self):
        return self.get_generic_boolean('SYST:LOCK')

    def set_resistance(self):
        raise NotImplementedError()
