#------------------------------------------------------------------------------
# Copyright (c) 2015 Ralph Hempel
# Copyright (c) 2015 Anton Vanhoucke
# Copyright (c) 2015 Denis Demidov
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

#~autogen autogen-header
# Sections of the following code were auto-generated based on spec v0.9.3-pre, rev 2

#~autogen

import os.path
import fnmatch
import numbers
import platform
import fcntl
import array

#------------------------------------------------------------------------------
# Guess platform we are running on
def current_platform():
    machine = platform.machine()
    if machine == 'armv5tejl':
        return 'ev3'
    elif machine == 'armv6l':
        return 'brickpi'
    else:
        return 'unsupported'

#------------------------------------------------------------------------------
# Define the base class from which all other ev3dev classes are defined.

class Device(object):
    """The ev3dev device base class"""

    DEVICE_ROOT_PATH = '/sys/class'

    def __init__(self, class_name, name='*', **kwargs ):
        """Spin through the Linux sysfs class for the device type and find
        a device that matches the provided name and attributes (if any).

        Parameters:
            class_name: class name of the device, a subdirectory of /sys/class.
                For example, 'tacho-motor'.
            name: pattern that device name should match.
                For example, 'sensor*' or 'motor*'. Default value: '*'.
            keyword arguments: used for matching the corresponding device
                attributes. For example, port_name='outA', or
                driver_name=['lego-ev3-us', 'lego-nxt-us']. When argument value
                is a list, then a match against any entry of the list is
                enough.

        Example:
            d = ev3dev.Device('tacho-motor', port_name='outA')
            s = ev3dev.Device('lego-sensor', driver_name=['lego-ev3-us', 'lego-nxt-us'])

        When connected succesfully, the `connected` attribute is set to True.
        """

        classpath = os.path.abspath( Device.DEVICE_ROOT_PATH + '/' + class_name )
        self.filehandle_cache = {}

        for file in os.listdir( classpath ):
            if fnmatch.fnmatch(file, name):
                self._path = os.path.abspath( classpath + '/' + file )

                # See if requested attributes match:
                if all([self._matches(k, kwargs[k]) for k in kwargs]):
                    self.connected = True
                    return

        self._path = ''
        self.connected = False

    def _matches(self, attribute, pattern):
        """Test if attribute value matches pattern (that is, if pattern is a
        substring of attribute value).  If pattern is a list, then a match with
        any one entry is enough.
        """
        value = self._get_attribute(attribute)
        if isinstance(pattern, list):
            return any([value.find(pat) >= 0 for pat in pattern])
        else:
            return value.find(pattern) >= 0

    def _attribute_file( self, attribute, mode, reopen=False ):
        """Manages the file handle cache and opening the files in the correct mode"""

        attribute_name = os.path.abspath( self._path + '/' + attribute )

        if attribute_name not in self.filehandle_cache:
            f = open( attribute_name, mode )
            self.filehandle_cache[attribute_name] = f
        elif reopen == True:
            self.filehandle_cache[attribute_name].close()
            f = open( attribute_name, mode )
            self.filehandle_cache[attribute_name] = f
        else:
            f = self.filehandle_cache[attribute_name]
        return f

    def _get_attribute( self, attribute ):
        """Device attribute getter"""
        f = self._attribute_file( attribute, 'r' )
        try:
            f.seek(0)
            value = f.read()
        except IOError:
            f = self._attribute_file( attribute, 'w+', True )
            value = f.read()
        return value.strip()

    def _set_attribute( self, attribute, value ):
        """Device attribute setter"""
        f = self._attribute_file( attribute, 'w' )
        try:
            f.seek(0)
            f.write( value )
            f.flush()
        except IOError:
            f = self._attribute_file( attribute, 'w+', True )
            f.write( value )
            f.flush()

    def get_attr_int( self, attribute ):
        return int( self._get_attribute( attribute ) )

    def set_attr_int( self, attribute, value ):
        self._set_attribute( attribute, '{0:d}'.format( int(value) ) )

    def get_attr_string( self, attribute ):
        return self._get_attribute( attribute )

    def set_attr_string( self, attribute, value ):
        self._set_attribute( attribute, "{0}".format(value) )

    def get_attr_line( self, attribute ):
        return self._get_attribute( attribute )

    def get_attr_set( self, attribute ):
        return [v.strip('[]') for v in self.get_attr_line( attribute ).split()]

    def get_attr_from_set( self, attribute ):
        for a in self.get_attr_line( attribute ).split():
            v = a.strip( '[]' )
            if v != a:
                return v
        return ""

#~autogen generic-class classes.motor>currentClass

class Motor(Device):

    """
    The motor class provides a uniform interface for using motors with
    positional and directional feedback such as the EV3 and NXT motors.
    This feedback allows for precise control of the motors. This is the
    most common type of motor, so we just call it `motor`.
    """

    SYSTEM_CLASS_NAME = 'tacho-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

#~autogen
#~autogen generic-get-set classes.motor>currentClass


    @property
    def command(self):
        """
        Sends a command to the motor controller. See `commands` for a list of
        possible values.
        """
        raise Exception( "command is a write-only property!" )

    @command.setter
    def command(self, value):
        self.set_attr_string( 'command', value )

    @property
    def commands(self):
        """
        Returns a list of commands that are supported by the motor
        controller. Possible values are `run-forever`, `run-to-abs-pos`, `run-to-rel-pos`,
        `run-timed`, `run-direct`, `stop` and `reset`. Not all commands may be supported.
        `run-forever` will cause the motor to run until another command is sent.
        `run-to-abs-pos` will run to an absolute position specified by `position_sp`
        and then stop using the command specified in `stop_command`.
        `run-to-rel-pos` will run to a position relative to the current `position` value.
        The new position will be current `position` + `position_sp`. When the new
        position is reached, the motor will stop using the command specified by `stop_command`.
        `run-timed` will run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the command specified by `stop_command`.
        `run-direct` will run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        `stop` will stop any of the run commands before they are complete using the
        command specified by `stop_command`.
        `reset` will reset all of the motor parameter attributes to their default value.
        This will also have the effect of stopping the motor.
        """
        return self.get_attr_set( 'commands' )

    @property
    def count_per_rot(self):
        """
        Returns the number of tacho counts in one rotation of the motor. Tacho counts
        are used by the position and speed attributes, so you can use this value
        to convert rotations or degrees to tacho counts. In the case of linear
        actuators, the units here will be counts per centimeter.
        """
        return self.get_attr_int( 'count_per_rot' )

    @property
    def driver_name(self):
        """
        Returns the name of the driver that provides this tacho motor device.
        """
        return self.get_attr_string( 'driver_name' )

    @property
    def duty_cycle(self):
        """
        Returns the current duty cycle of the motor. Units are percent. Values
        are -100 to 100.
        """
        return self.get_attr_int( 'duty_cycle' )

    @property
    def duty_cycle_sp(self):
        """
        Writing sets the duty cycle setpoint. Reading returns the current value.
        Units are in percent. Valid values are -100 to 100. A negative value causes
        the motor to rotate in reverse. This value is only used when `speed_regulation`
        is off.
        """
        return self.get_attr_int( 'duty_cycle_sp' )

    @duty_cycle_sp.setter
    def duty_cycle_sp(self, value):
        self.set_attr_int( 'duty_cycle_sp', value )

    @property
    def encoder_polarity(self):
        """
        Sets the polarity of the rotary encoder. This is an advanced feature to all
        use of motors that send inversed encoder signals to the EV3. This should
        be set correctly by the driver of a device. It You only need to change this
        value if you are using a unsupported device. Valid values are `normal` and
        `inversed`.
        """
        return self.get_attr_string( 'encoder_polarity' )

    @encoder_polarity.setter
    def encoder_polarity(self, value):
        self.set_attr_string( 'encoder_polarity', value )

    @property
    def polarity(self):
        """
        Sets the polarity of the motor. With `normal` polarity, a positive duty
        cycle will cause the motor to rotate clockwise. With `inversed` polarity,
        a positive duty cycle will cause the motor to rotate counter-clockwise.
        Valid values are `normal` and `inversed`.
        """
        return self.get_attr_string( 'polarity' )

    @polarity.setter
    def polarity(self, value):
        self.set_attr_string( 'polarity', value )

    @property
    def port_name(self):
        """
        Returns the name of the port that the motor is connected to.
        """
        return self.get_attr_string( 'port_name' )

    @property
    def position(self):
        """
        Returns the current position of the motor in pulses of the rotary
        encoder. When the motor rotates clockwise, the position will increase.
        Likewise, rotating counter-clockwise causes the position to decrease.
        Writing will set the position to that value.
        """
        return self.get_attr_int( 'position' )

    @position.setter
    def position(self, value):
        self.set_attr_int( 'position', value )

    @property
    def position_p(self):
        """
        The proportional constant for the position PID.
        """
        return self.get_attr_int( 'hold_pid/Kp' )

    @position_p.setter
    def position_p(self, value):
        self.set_attr_int( 'hold_pid/Kp', value )

    @property
    def position_i(self):
        """
        The integral constant for the position PID.
        """
        return self.get_attr_int( 'hold_pid/Ki' )

    @position_i.setter
    def position_i(self, value):
        self.set_attr_int( 'hold_pid/Ki', value )

    @property
    def position_d(self):
        """
        The derivative constant for the position PID.
        """
        return self.get_attr_int( 'hold_pid/Kd' )

    @position_d.setter
    def position_d(self, value):
        self.set_attr_int( 'hold_pid/Kd', value )

    @property
    def position_sp(self):
        """
        Writing specifies the target position for the `run-to-abs-pos` and `run-to-rel-pos`
        commands. Reading returns the current value. Units are in tacho counts. You
        can use the value returned by `counts_per_rot` to convert tacho counts to/from
        rotations or degrees.
        """
        return self.get_attr_int( 'position_sp' )

    @position_sp.setter
    def position_sp(self, value):
        self.set_attr_int( 'position_sp', value )

    @property
    def speed(self):
        """
        Returns the current motor speed in tacho counts per second. Not, this is
        not necessarily degrees (although it is for LEGO motors). Use the `count_per_rot`
        attribute to convert this value to RPM or deg/sec.
        """
        return self.get_attr_int( 'speed' )

    @property
    def speed_sp(self):
        """
        Writing sets the target speed in tacho counts per second used when `speed_regulation`
        is on. Reading returns the current value.  Use the `count_per_rot` attribute
        to convert RPM or deg/sec to tacho counts per second.
        """
        return self.get_attr_int( 'speed_sp' )

    @speed_sp.setter
    def speed_sp(self, value):
        self.set_attr_int( 'speed_sp', value )

    @property
    def ramp_up_sp(self):
        """
        Writing sets the ramp up setpoint. Reading returns the current value. Units
        are in milliseconds. When set to a value > 0, the motor will ramp the power
        sent to the motor from 0 to 100% duty cycle over the span of this setpoint
        when starting the motor. If the maximum duty cycle is limited by `duty_cycle_sp`
        or speed regulation, the actual ramp time duration will be less than the setpoint.
        """
        return self.get_attr_int( 'ramp_up_sp' )

    @ramp_up_sp.setter
    def ramp_up_sp(self, value):
        self.set_attr_int( 'ramp_up_sp', value )

    @property
    def ramp_down_sp(self):
        """
        Writing sets the ramp down setpoint. Reading returns the current value. Units
        are in milliseconds. When set to a value > 0, the motor will ramp the power
        sent to the motor from 100% duty cycle down to 0 over the span of this setpoint
        when stopping the motor. If the starting duty cycle is less than 100%, the
        ramp time duration will be less than the full span of the setpoint.
        """
        return self.get_attr_int( 'ramp_down_sp' )

    @ramp_down_sp.setter
    def ramp_down_sp(self, value):
        self.set_attr_int( 'ramp_down_sp', value )

    @property
    def speed_regulation_enabled(self):
        """
        Turns speed regulation on or off. If speed regulation is on, the motor
        controller will vary the power supplied to the motor to try to maintain the
        speed specified in `speed_sp`. If speed regulation is off, the controller
        will use the power specified in `duty_cycle_sp`. Valid values are `on` and
        `off`.
        """
        return self.get_attr_string( 'speed_regulation' )

    @speed_regulation_enabled.setter
    def speed_regulation_enabled(self, value):
        self.set_attr_string( 'speed_regulation', value )

    @property
    def speed_regulation_p(self):
        """
        The proportional constant for the speed regulation PID.
        """
        return self.get_attr_int( 'speed_pid/Kp' )

    @speed_regulation_p.setter
    def speed_regulation_p(self, value):
        self.set_attr_int( 'speed_pid/Kp', value )

    @property
    def speed_regulation_i(self):
        """
        The integral constant for the speed regulation PID.
        """
        return self.get_attr_int( 'speed_pid/Ki' )

    @speed_regulation_i.setter
    def speed_regulation_i(self, value):
        self.set_attr_int( 'speed_pid/Ki', value )

    @property
    def speed_regulation_d(self):
        """
        The derivative constant for the speed regulation PID.
        """
        return self.get_attr_int( 'speed_pid/Kd' )

    @speed_regulation_d.setter
    def speed_regulation_d(self, value):
        self.set_attr_int( 'speed_pid/Kd', value )

    @property
    def state(self):
        """
        Reading returns a list of state flags. Possible flags are
        `running`, `ramping` `holding` and `stalled`.
        """
        return self.get_attr_set( 'state' )

    @property
    def stop_command(self):
        """
        Reading returns the current stop command. Writing sets the stop command.
        The value determines the motors behavior when `command` is set to `stop`.
        Also, it determines the motors behavior when a run command completes. See
        `stop_commands` for a list of possible values.
        """
        return self.get_attr_string( 'stop_command' )

    @stop_command.setter
    def stop_command(self, value):
        self.set_attr_string( 'stop_command', value )

    @property
    def stop_commands(self):
        """
        Returns a list of stop modes supported by the motor controller.
        Possible values are `coast`, `brake` and `hold`. `coast` means that power will
        be removed from the motor and it will freely coast to a stop. `brake` means
        that power will be removed from the motor and a passive electrical load will
        be placed on the motor. This is usually done by shorting the motor terminals
        together. This load will absorb the energy from the rotation of the motors and
        cause the motor to stop more quickly than coasting. `hold` does not remove
        power from the motor. Instead it actively try to hold the motor at the current
        position. If an external force tries to turn the motor, the motor will 'push
        back' to maintain its position.
        """
        return self.get_attr_set( 'stop_commands' )

    @property
    def time_sp(self):
        """
        Writing specifies the amount of time the motor will run when using the
        `run-timed` command. Reading returns the current value. Units are in
        milliseconds.
        """
        return self.get_attr_int( 'time_sp' )

    @time_sp.setter
    def time_sp(self, value):
        self.set_attr_int( 'time_sp', value )


#~autogen
#~autogen generic-property-value classes.motor>currentClass

    # Run the motor until another command is sent.
    COMMAND_RUN_FOREVER = 'run-forever'

    # Run to an absolute position specified by `position_sp` and then
    # stop using the command specified in `stop_command`.
    COMMAND_RUN_TO_ABS_POS = 'run-to-abs-pos'

    # Run to a position relative to the current `position` value.
    # The new position will be current `position` + `position_sp`.
    # When the new position is reached, the motor will stop using
    # the command specified by `stop_command`.
    COMMAND_RUN_TO_REL_POS = 'run-to-rel-pos'

    # Run the motor for the amount of time specified in `time_sp`
    # and then stop the motor using the command specified by `stop_command`.
    COMMAND_RUN_TIMED = 'run-timed'

    # Run the motor at the duty cycle specified by `duty_cycle_sp`.
    # Unlike other run commands, changing `duty_cycle_sp` while running *will*
    # take effect immediately.
    COMMAND_RUN_DIRECT = 'run-direct'

    # Stop any of the run commands before they are complete using the
    # command specified by `stop_command`.
    COMMAND_STOP = 'stop'

    # Reset all of the motor parameter attributes to their default value.
    # This will also have the effect of stopping the motor.
    COMMAND_RESET = 'reset'

    # Sets the normal polarity of the rotary encoder.
    ENCODER_POLARITY_NORMAL = 'normal'

    # Sets the inversed polarity of the rotary encoder.
    ENCODER_POLARITY_INVERSED = 'inversed'

    # With `normal` polarity, a positive duty cycle will
    # cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    # With `inversed` polarity, a positive duty cycle will
    # cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    # The motor controller will vary the power supplied to the motor
    # to try to maintain the speed specified in `speed_sp`.
    SPEED_REGULATION_ON = 'on'

    # The motor controller will use the power specified in `duty_cycle_sp`.
    SPEED_REGULATION_OFF = 'off'

    # Power will be removed from the motor and it will freely coast to a stop.
    STOP_COMMAND_COAST = 'coast'

    # Power will be removed from the motor and a passive electrical load will
    # be placed on the motor. This is usually done by shorting the motor terminals
    # together. This load will absorb the energy from the rotation of the motors and
    # cause the motor to stop more quickly than coasting.
    STOP_COMMAND_BRAKE = 'brake'

    # Does not remove power from the motor. Instead it actively try to hold the motor
    # at the current position. If an external force tries to turn the motor, the motor
    # will ``push back`` to maintain its position.
    STOP_COMMAND_HOLD = 'hold'


#~autogen
#~autogen motor_commands classes.motor>currentClass

    def run_forever( self, **kwargs ):
        """Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-forever'

    def run_to_abs_pos( self, **kwargs ):
        """Run to an absolute position specified by `position_sp` and then
        stop using the command specified in `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-to-abs-pos'

    def run_to_rel_pos( self, **kwargs ):
        """Run to a position relative to the current `position` value.
        The new position will be current `position` + `position_sp`.
        When the new position is reached, the motor will stop using
        the command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-to-rel-pos'

    def run_timed( self, **kwargs ):
        """Run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-timed'

    def run_direct( self, **kwargs ):
        """Run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-direct'

    def stop( self, **kwargs ):
        """Stop any of the run commands before they are complete using the
        command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'stop'

    def reset( self, **kwargs ):
        """Reset all of the motor parameter attributes to their default value.
        This will also have the effect of stopping the motor.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'reset'


#~autogen
#~autogen generic-class classes.largeMotor>currentClass

class LargeMotor(Motor):

    """
    EV3 large servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Motor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-l-motor'], **kwargs)

#~autogen
#~autogen generic-class classes.mediumMotor>currentClass

class MediumMotor(Motor):

    """
    EV3 medium servo motor
    """

    SYSTEM_CLASS_NAME = Motor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Motor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-m-motor'], **kwargs)

#~autogen
#~autogen generic-class classes.dcMotor>currentClass

class DcMotor(Device):

    """
    The DC motor class provides a uniform interface for using regular DC motors
    with no fancy controls or feedback. This includes LEGO MINDSTORMS RCX motors
    and LEGO Power Functions motors.
    """

    SYSTEM_CLASS_NAME = 'dc-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

#~autogen
#~autogen generic-get-set classes.dcMotor>currentClass


    @property
    def command(self):
        """
        Sets the command for the motor. Possible values are `run-forever`, `run-timed` and
        `stop`. Not all commands may be supported, so be sure to check the contents
        of the `commands` attribute.
        """
        raise Exception( "command is a write-only property!" )

    @command.setter
    def command(self, value):
        self.set_attr_string( 'command', value )

    @property
    def commands(self):
        """
        Returns a list of commands supported by the motor
        controller.
        """
        return self.get_attr_set( 'commands' )

    @property
    def driver_name(self):
        """
        Returns the name of the motor driver that loaded this device. See the list
        of [supported devices] for a list of drivers.
        """
        return self.get_attr_string( 'driver_name' )

    @property
    def duty_cycle(self):
        """
        Shows the current duty cycle of the PWM signal sent to the motor. Values
        are -100 to 100 (-100% to 100%).
        """
        return self.get_attr_int( 'duty_cycle' )

    @property
    def duty_cycle_sp(self):
        """
        Writing sets the duty cycle setpoint of the PWM signal sent to the motor.
        Valid values are -100 to 100 (-100% to 100%). Reading returns the current
        setpoint.
        """
        return self.get_attr_int( 'duty_cycle_sp' )

    @duty_cycle_sp.setter
    def duty_cycle_sp(self, value):
        self.set_attr_int( 'duty_cycle_sp', value )

    @property
    def polarity(self):
        """
        Sets the polarity of the motor. Valid values are `normal` and `inversed`.
        """
        return self.get_attr_string( 'polarity' )

    @polarity.setter
    def polarity(self, value):
        self.set_attr_string( 'polarity', value )

    @property
    def port_name(self):
        """
        Returns the name of the port that the motor is connected to.
        """
        return self.get_attr_string( 'port_name' )

    @property
    def ramp_down_sp(self):
        """
        Sets the time in milliseconds that it take the motor to ramp down from 100%
        to 0%. Valid values are 0 to 10000 (10 seconds). Default is 0.
        """
        return self.get_attr_int( 'ramp_down_sp' )

    @ramp_down_sp.setter
    def ramp_down_sp(self, value):
        self.set_attr_int( 'ramp_down_sp', value )

    @property
    def ramp_up_sp(self):
        """
        Sets the time in milliseconds that it take the motor to up ramp from 0% to
        100%. Valid values are 0 to 10000 (10 seconds). Default is 0.
        """
        return self.get_attr_int( 'ramp_up_sp' )

    @ramp_up_sp.setter
    def ramp_up_sp(self, value):
        self.set_attr_int( 'ramp_up_sp', value )

    @property
    def state(self):
        """
        Gets a list of flags indicating the motor status. Possible
        flags are `running` and `ramping`. `running` indicates that the motor is
        powered. `ramping` indicates that the motor has not yet reached the
        `duty_cycle_sp`.
        """
        return self.get_attr_set( 'state' )

    @property
    def stop_command(self):
        """
        Sets the stop command that will be used when the motor stops. Read
        `stop_commands` to get the list of valid values.
        """
        raise Exception( "stop_command is a write-only property!" )

    @stop_command.setter
    def stop_command(self, value):
        self.set_attr_string( 'stop_command', value )

    @property
    def stop_commands(self):
        """
        Gets a list of stop commands. Valid values are `coast`
        and `brake`.
        """
        return self.get_attr_set( 'stop_commands' )

    @property
    def time_sp(self):
        """
        Writing specifies the amount of time the motor will run when using the
        `run-timed` command. Reading returns the current value. Units are in
        milliseconds.
        """
        return self.get_attr_int( 'time_sp' )

    @time_sp.setter
    def time_sp(self, value):
        self.set_attr_int( 'time_sp', value )


#~autogen
#~autogen generic-property-value classes.dcMotor>currentClass

    # Run the motor until another command is sent.
    COMMAND_RUN_FOREVER = 'run-forever'

    # Run the motor for the amount of time specified in `time_sp`
    # and then stop the motor using the command specified by `stop_command`.
    COMMAND_RUN_TIMED = 'run-timed'

    # Run the motor at the duty cycle specified by `duty_cycle_sp`.
    # Unlike other run commands, changing `duty_cycle_sp` while running *will*
    # take effect immediately.
    COMMAND_RUN_DIRECT = 'run-direct'

    # Stop any of the run commands before they are complete using the
    # command specified by `stop_command`.
    COMMAND_STOP = 'stop'

    # With `normal` polarity, a positive duty cycle will
    # cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    # With `inversed` polarity, a positive duty cycle will
    # cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'

    # Power will be removed from the motor and it will freely coast to a stop.
    STOP_COMMAND_COAST = 'coast'

    # Power will be removed from the motor and a passive electrical load will
    # be placed on the motor. This is usually done by shorting the motor terminals
    # together. This load will absorb the energy from the rotation of the motors and
    # cause the motor to stop more quickly than coasting.
    STOP_COMMAND_BRAKE = 'brake'


#~autogen

#~autogen motor_commands classes.dcMotor>currentClass

    def run_forever( self, **kwargs ):
        """Run the motor until another command is sent.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-forever'

    def run_timed( self, **kwargs ):
        """Run the motor for the amount of time specified in `time_sp`
        and then stop the motor using the command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-timed'

    def run_direct( self, **kwargs ):
        """Run the motor at the duty cycle specified by `duty_cycle_sp`.
        Unlike other run commands, changing `duty_cycle_sp` while running *will*
        take effect immediately.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run-direct'

    def stop( self, **kwargs ):
        """Stop any of the run commands before they are complete using the
        command specified by `stop_command`.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'stop'


#~autogen
#~autogen generic-class classes.servoMotor>currentClass

class ServoMotor(Device):

    """
    The servo motor class provides a uniform interface for using hobby type
    servo motors.
    """

    SYSTEM_CLASS_NAME = 'servo-motor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'motor*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

#~autogen
#~autogen generic-get-set classes.servoMotor>currentClass


    @property
    def command(self):
        """
        Sets the command for the servo. Valid values are `run` and `float`. Setting
        to `run` will cause the servo to be driven to the position_sp set in the
        `position_sp` attribute. Setting to `float` will remove power from the motor.
        """
        raise Exception( "command is a write-only property!" )

    @command.setter
    def command(self, value):
        self.set_attr_string( 'command', value )

    @property
    def driver_name(self):
        """
        Returns the name of the motor driver that loaded this device. See the list
        of [supported devices] for a list of drivers.
        """
        return self.get_attr_string( 'driver_name' )

    @property
    def max_pulse_sp(self):
        """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the maximum (clockwise) position_sp. Default value is 2400.
        Valid values are 2300 to 2700. You must write to the position_sp attribute for
        changes to this attribute to take effect.
        """
        return self.get_attr_int( 'max_pulse_sp' )

    @max_pulse_sp.setter
    def max_pulse_sp(self, value):
        self.set_attr_int( 'max_pulse_sp', value )

    @property
    def mid_pulse_sp(self):
        """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the mid position_sp. Default value is 1500. Valid
        values are 1300 to 1700. For example, on a 180 degree servo, this would be
        90 degrees. On continuous rotation servo, this is the 'neutral' position_sp
        where the motor does not turn. You must write to the position_sp attribute for
        changes to this attribute to take effect.
        """
        return self.get_attr_int( 'mid_pulse_sp' )

    @mid_pulse_sp.setter
    def mid_pulse_sp(self, value):
        self.set_attr_int( 'mid_pulse_sp', value )

    @property
    def min_pulse_sp(self):
        """
        Used to set the pulse size in milliseconds for the signal that tells the
        servo to drive to the miniumum (counter-clockwise) position_sp. Default value
        is 600. Valid values are 300 to 700. You must write to the position_sp
        attribute for changes to this attribute to take effect.
        """
        return self.get_attr_int( 'min_pulse_sp' )

    @min_pulse_sp.setter
    def min_pulse_sp(self, value):
        self.set_attr_int( 'min_pulse_sp', value )

    @property
    def polarity(self):
        """
        Sets the polarity of the servo. Valid values are `normal` and `inversed`.
        Setting the value to `inversed` will cause the position_sp value to be
        inversed. i.e `-100` will correspond to `max_pulse_sp`, and `100` will
        correspond to `min_pulse_sp`.
        """
        return self.get_attr_string( 'polarity' )

    @polarity.setter
    def polarity(self, value):
        self.set_attr_string( 'polarity', value )

    @property
    def port_name(self):
        """
        Returns the name of the port that the motor is connected to.
        """
        return self.get_attr_string( 'port_name' )

    @property
    def position_sp(self):
        """
        Reading returns the current position_sp of the servo. Writing instructs the
        servo to move to the specified position_sp. Units are percent. Valid values
        are -100 to 100 (-100% to 100%) where `-100` corresponds to `min_pulse_sp`,
        `0` corresponds to `mid_pulse_sp` and `100` corresponds to `max_pulse_sp`.
        """
        return self.get_attr_int( 'position_sp' )

    @position_sp.setter
    def position_sp(self, value):
        self.set_attr_int( 'position_sp', value )

    @property
    def rate_sp(self):
        """
        Sets the rate_sp at which the servo travels from 0 to 100.0% (half of the full
        range of the servo). Units are in milliseconds. Example: Setting the rate_sp
        to 1000 means that it will take a 180 degree servo 2 second to move from 0
        to 180 degrees. Note: Some servo controllers may not support this in which
        case reading and writing will fail with `-EOPNOTSUPP`. In continuous rotation
        servos, this value will affect the rate_sp at which the speed ramps up or down.
        """
        return self.get_attr_int( 'rate_sp' )

    @rate_sp.setter
    def rate_sp(self, value):
        self.set_attr_int( 'rate_sp', value )

    @property
    def state(self):
        """
        Returns a list of flags indicating the state of the servo.
        Possible values are:
        * `running`: Indicates that the motor is powered.
        """
        return self.get_attr_set( 'state' )


#~autogen
#~autogen generic-property-value classes.servoMotor>currentClass

    # Drive servo to the position set in the `position_sp` attribute.
    COMMAND_RUN = 'run'

    # Remove power from the motor.
    COMMAND_FLOAT = 'float'

    # With `normal` polarity, a positive duty cycle will
    # cause the motor to rotate clockwise.
    POLARITY_NORMAL = 'normal'

    # With `inversed` polarity, a positive duty cycle will
    # cause the motor to rotate counter-clockwise.
    POLARITY_INVERSED = 'inversed'


#~autogen

#~autogen motor_commands classes.servoMotor>currentClass

    def run( self, **kwargs ):
        """Drive servo to the position set in the `position_sp` attribute.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'run'

    def float( self, **kwargs ):
        """Remove power from the motor.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.command = 'float'


#~autogen

#~autogen generic-class classes.sensor>currentClass

class Sensor(Device):

    """
    The sensor class provides a uniform interface for using most of the
    sensors available for the EV3. The various underlying device drivers will
    create a `lego-sensor` device for interacting with the sensors.
    
    Sensors are primarily controlled by setting the `mode` and monitored by
    reading the `value<N>` attributes. Values can be converted to floating point
    if needed by `value<N>` / 10.0 ^ `decimals`.
    
    Since the name of the `sensor<N>` device node does not correspond to the port
    that a sensor is plugged in to, you must look at the `port_name` attribute if
    you need to know which port a sensor is plugged in to. However, if you don't
    have more than one sensor of each type, you can just look for a matching
    `driver_name`. Then it will not matter which port a sensor is plugged in to - your
    program will still work.
    """

    SYSTEM_CLASS_NAME = 'lego-sensor'
    SYSTEM_DEVICE_NAME_CONVENTION = 'sensor*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

#~autogen
#~autogen generic-get-set classes.sensor>currentClass


    @property
    def command(self):
        """
        Sends a command to the sensor.
        """
        raise Exception( "command is a write-only property!" )

    @command.setter
    def command(self, value):
        self.set_attr_string( 'command', value )

    @property
    def commands(self):
        """
        Returns a list of the valid commands for the sensor.
        Returns -EOPNOTSUPP if no commands are supported.
        """
        return self.get_attr_set( 'commands' )

    @property
    def decimals(self):
        """
        Returns the number of decimal places for the values in the `value<N>`
        attributes of the current mode.
        """
        return self.get_attr_int( 'decimals' )

    @property
    def driver_name(self):
        """
        Returns the name of the sensor device/driver. See the list of [supported
        sensors] for a complete list of drivers.
        """
        return self.get_attr_string( 'driver_name' )

    @property
    def mode(self):
        """
        Returns the current mode. Writing one of the values returned by `modes`
        sets the sensor to that mode.
        """
        return self.get_attr_string( 'mode' )

    @mode.setter
    def mode(self, value):
        self.set_attr_string( 'mode', value )

    @property
    def modes(self):
        """
        Returns a list of the valid modes for the sensor.
        """
        return self.get_attr_set( 'modes' )

    @property
    def num_values(self):
        """
        Returns the number of `value<N>` attributes that will return a valid value
        for the current mode.
        """
        return self.get_attr_int( 'num_values' )

    @property
    def port_name(self):
        """
        Returns the name of the port that the sensor is connected to, e.g. `ev3:in1`.
        I2C sensors also include the I2C address (decimal), e.g. `ev3:in1:i2c8`.
        """
        return self.get_attr_string( 'port_name' )

    @property
    def units(self):
        """
        Returns the units of the measured value for the current mode. May return
        empty string
        """
        return self.get_attr_string( 'units' )


#~autogen

    def value(self, n=0):
        if True == isinstance( n, numbers.Integral ):
            n = '{0:d}'.format( n )
        elif True == isinstance( n, numbers.Real ):
            n = '{0:.0f}'.format( n )

        if True == isinstance( n, str ):
            return self.get_attr_int( 'value'+n )
        else:
            return 0

#~autogen generic-class classes.i2cSensor>currentClass

class I2cSensor(Sensor):

    """
    A generic interface to control I2C-type EV3 sensors.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['nxt-i2c-sensor'], **kwargs)

#~autogen
#~autogen generic-get-set classes.i2cSensor>currentClass


    @property
    def fw_version(self):
        """
        Returns the firmware version of the sensor if available. Currently only
        I2C/NXT sensors support this.
        """
        return self.get_attr_string( 'fw_version' )

    @property
    def poll_ms(self):
        """
        Returns the polling period of the sensor in milliseconds. Writing sets the
        polling period. Setting to 0 disables polling. Minimum value is hard
        coded as 50 msec. Returns -EOPNOTSUPP if changing polling is not supported.
        Currently only I2C/NXT sensors support changing the polling period.
        """
        return self.get_attr_int( 'poll_ms' )

    @poll_ms.setter
    def poll_ms(self, value):
        self.set_attr_int( 'poll_ms', value )


#~autogen
#~autogen generic-class classes.colorSensor>currentClass

class ColorSensor(Sensor):

    """
    LEGO EV3 color sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-color'], **kwargs)

#~autogen
#~autogen generic-property-value classes.colorSensor>currentClass

    # Reflected light. Red LED on.
    MODE_COL_REFLECT = 'COL-REFLECT'

    # Ambient light. Red LEDs off.
    MODE_COL_AMBIENT = 'COL-AMBIENT'

    # Color. All LEDs rapidly cycling, appears white.
    MODE_COL_COLOR = 'COL-COLOR'

    # Raw reflected. Red LED on
    MODE_REF_RAW = 'REF-RAW'

    # Raw Color Components. All LEDs rapidly cycling, appears white.
    MODE_RGB_RAW = 'RGB-RAW'


#~autogen
#~autogen generic-class classes.ultrasonicSensor>currentClass

class UltrasonicSensor(Sensor):

    """
    LEGO EV3 ultrasonic sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-us', 'lego-nxt-us'], **kwargs)

#~autogen
#~autogen generic-property-value classes.ultrasonicSensor>currentClass

    # Continuous measurement in centimeters.
    # LEDs: On, steady
    MODE_US_DIST_CM = 'US-DIST-CM'

    # Continuous measurement in inches.
    # LEDs: On, steady
    MODE_US_DIST_IN = 'US-DIST-IN'

    # Listen.  LEDs: On, blinking
    MODE_US_LISTEN = 'US-LISTEN'

    # Single measurement in centimeters.
    # LEDs: On momentarily when mode is set, then off
    MODE_US_SI_CM = 'US-SI-CM'

    # Single measurement in inches.
    # LEDs: On momentarily when mode is set, then off
    MODE_US_SI_IN = 'US-SI-IN'


#~autogen
#~autogen generic-class classes.gyroSensor>currentClass

class GyroSensor(Sensor):

    """
    LEGO EV3 gyro sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-gyro'], **kwargs)

#~autogen
#~autogen generic-property-value classes.gyroSensor>currentClass

    # Angle
    MODE_GYRO_ANG = 'GYRO-ANG'

    # Rotational speed
    MODE_GYRO_RATE = 'GYRO-RATE'

    # Raw sensor value
    MODE_GYRO_FAS = 'GYRO-FAS'

    # Angle and rotational speed
    MODE_GYRO_G_A = 'GYRO-G&A'

    # Calibration ???
    MODE_GYRO_CAL = 'GYRO-CAL'


#~autogen
#~autogen generic-class classes.infraredSensor>currentClass

class InfraredSensor(Sensor):

    """
    LEGO EV3 infrared sensor.
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-ir'], **kwargs)

#~autogen
#~autogen generic-property-value classes.infraredSensor>currentClass

    # Proximity
    MODE_IR_PROX = 'IR-PROX'

    # IR Seeker
    MODE_IR_SEEK = 'IR-SEEK'

    # IR Remote Control
    MODE_IR_REMOTE = 'IR-REMOTE'

    # IR Remote Control. State of the buttons is coded in binary
    MODE_IR_REM_A = 'IR-REM-A'

    # Calibration ???
    MODE_IR_CAL = 'IR-CAL'


#~autogen


#~autogen generic-class classes.soundSensor>currentClass

class SoundSensor(Sensor):

    """
    LEGO NXT Sound Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-nxt-sound'], **kwargs)

#~autogen
#~autogen generic-property-value classes.soundSensor>currentClass

    # Sound pressure level. Flat weighting
    MODE_DB = 'DB'

    # Sound pressure level. A weighting
    MODE_DBA = 'DBA'


#~autogen
#~autogen generic-class classes.lightSensor>currentClass

class LightSensor(Sensor):

    """
    LEGO NXT Light Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-nxt-light'], **kwargs)

#~autogen
#~autogen generic-property-value classes.lightSensor>currentClass

    # Reflected light. LED on
    MODE_REFLECT = 'REFLECT'

    # Ambient light. LED off
    MODE_AMBIENT = 'AMBIENT'


#~autogen
#~autogen generic-class classes.touchSensor>currentClass

class TouchSensor(Sensor):

    """
    Touch Sensor
    """

    SYSTEM_CLASS_NAME = Sensor.SYSTEM_CLASS_NAME
    SYSTEM_DEVICE_NAME_CONVENTION = Sensor.SYSTEM_DEVICE_NAME_CONVENTION

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, driver_name=['lego-ev3-touch', 'lego-nxt-touch'], **kwargs)

#~autogen
#~autogen generic-class classes.led>currentClass

class Led(Device):

    """
    Any device controlled by the generic LED driver.
    See https://www.kernel.org/doc/Documentation/leds/leds-class.txt
    for more details.
    """

    SYSTEM_CLASS_NAME = 'leds'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

#~autogen
#~autogen generic-get-set classes.led>currentClass


    @property
    def max_brightness(self):
        """
        Returns the maximum allowable brightness value.
        """
        return self.get_attr_int( 'max_brightness' )

    @property
    def brightness(self):
        """
        Sets the brightness level. Possible values are from 0 to `max_brightness`.
        """
        return self.get_attr_int( 'brightness' )

    @brightness.setter
    def brightness(self, value):
        self.set_attr_int( 'brightness', value )

    @property
    def triggers(self):
        """
        Returns a list of available triggers.
        """
        return self.get_attr_set( 'trigger' )

    @property
    def trigger(self):
        """
        Sets the led trigger. A trigger
        is a kernel based source of led events. Triggers can either be simple or
        complex. A simple trigger isn't configurable and is designed to slot into
        existing subsystems with minimal additional code. Examples are the `ide-disk` and
        `nand-disk` triggers.
        
        Complex triggers whilst available to all LEDs have LED specific
        parameters and work on a per LED basis. The `timer` trigger is an example.
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` and `off` time can
        be specified via `delay_{on,off}` attributes in milliseconds.
        You can change the brightness value of a LED independently of the timer
        trigger. However, if you set the brightness value to 0 it will
        also disable the `timer` trigger.
        """
        return self.get_attr_from_set( 'trigger' )

    @trigger.setter
    def trigger(self, value):
        self.set_attr_string( 'trigger', value )

    @property
    def delay_on(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `on` time can
        be specified via `delay_on` attribute in milliseconds.
        """
        return self.get_attr_int( 'delay_on' )

    @delay_on.setter
    def delay_on(self, value):
        self.set_attr_int( 'delay_on', value )

    @property
    def delay_off(self):
        """
        The `timer` trigger will periodically change the LED brightness between
        0 and the current brightness setting. The `off` time can
        be specified via `delay_off` attribute in milliseconds.
        """
        return self.get_attr_int( 'delay_off' )

    @delay_off.setter
    def delay_off(self, value):
        self.set_attr_int( 'delay_off', value )


#~autogen

    @property
    def brightness_pct(self):
        """
        Returns led brightness as a fraction of max_brightness
        """
        return float(self.brightness) / self.max_brightness

    @brightness_pct.setter
    def brightness_pct(self, value):
        self.brightness = value * self.max_brightness

if current_platform() == 'ev3':
#~autogen led-colors platforms.ev3.led>currentClass

    Led.red_left = Led(name='ev3-left0:red:ev3dev')
    Led.red_right = Led(name='ev3-right0:red:ev3dev')
    Led.green_left = Led(name='ev3-left1:green:ev3dev')
    Led.green_right = Led(name='ev3-right1:green:ev3dev')

    @staticmethod
    def Led_mix_colors(red, green):
        Led.red_left.brightness_pct = red
        Led.red_right.brightness_pct = red
        Led.green_left.brightness_pct = green
        Led.green_right.brightness_pct = green
    Led.mix_colors = Led_mix_colors

    @staticmethod
    def Led_set_red(pct):
        Led.mix_colors(red=1*pct, green=0*pct)
    Led.set_red = Led_set_red

    @staticmethod
    def Led_red_on():
        Led.set_red(1)
    Led.red_on = Led_red_on

    @staticmethod
    def Led_set_green(pct):
        Led.mix_colors(red=0*pct, green=1*pct)
    Led.set_green = Led_set_green

    @staticmethod
    def Led_green_on():
        Led.set_green(1)
    Led.green_on = Led_green_on

    @staticmethod
    def Led_set_amber(pct):
        Led.mix_colors(red=1*pct, green=1*pct)
    Led.set_amber = Led_set_amber

    @staticmethod
    def Led_amber_on():
        Led.set_amber(1)
    Led.amber_on = Led_amber_on

    @staticmethod
    def Led_set_orange(pct):
        Led.mix_colors(red=1*pct, green=0.5*pct)
    Led.set_orange = Led_set_orange

    @staticmethod
    def Led_orange_on():
        Led.set_orange(1)
    Led.orange_on = Led_orange_on

    @staticmethod
    def Led_set_yellow(pct):
        Led.mix_colors(red=0.5*pct, green=1*pct)
    Led.set_yellow = Led_set_yellow

    @staticmethod
    def Led_yellow_on():
        Led.set_yellow(1)
    Led.yellow_on = Led_yellow_on

    @staticmethod
    def Led_all_off():
        Led.red_left.brightness = 0
        Led.red_right.brightness = 0
        Led.green_left.brightness = 0
        Led.green_right.brightness = 0
    Led.all_off = Led_all_off


#~autogen
elif current_platform() == 'brickpi':
#~autogen led-colors platforms.brickpi.led>currentClass

    Led.blue_one = Led(name='brickpi1:blue:ev3dev')
    Led.blue_two = Led(name='brickpi2:blue:ev3dev')

    @staticmethod
    def Led_mix_colors(blue):
        Led.blue_one.brightness_pct = blue
        Led.blue_two.brightness_pct = blue
    Led.mix_colors = Led_mix_colors

    @staticmethod
    def Led_set_blue(pct):
        Led.mix_colors(blue=1*pct)
    Led.set_blue = Led_set_blue

    @staticmethod
    def Led_blue_on():
        Led.set_blue(1)
    Led.blue_on = Led_blue_on

    @staticmethod
    def Led_all_off():
        Led.blue_one.brightness = 0
        Led.blue_two.brightness = 0
    Led.all_off = Led_all_off


#~autogen
#~autogen button-class classes.button>currentClass

import fcntl
import array

class Button(object):

    """
    Provides a generic button reading mechanism that can be adapted
    to platform specific implementations. Each platform's specific
    button capabilites are enumerated in the 'platforms' section
    of this specification

    This implementation depends on the availability of the EVIOCGKEY ioctl
    to be able to read the button state buffer. See Linux kernel source
    in /include/uapi/linux/input.h for details.
    """

    KEY_MAX = 0x2FF
    KEY_BUF_LEN = int((KEY_MAX + 7) / 8)
    EVIOCGKEY = (2 << (14 + 8 + 8) | KEY_BUF_LEN << (8 + 8) | ord('E') << 8 | 0x18)

    def __init__(self):
        self.buffer_cache = {}
        self.filehandle_cache = {}
        for b in self._buttons:
            self._button_file( self._buttons[b]['name'] )
            self._button_buffer( self._buttons[b]['name'] )

    def _button_file(self, name):
        if name not in self.filehandle_cache:
            f = open( name, 'r' )
            self.filehandle_cache[name] = f
        else:
            f = self.filehandle_cache[name]
        return f

    def _button_buffer(self, name):
        if name not in self.buffer_cache:
            self.buffer_cache[name] = array.array( 'B', [0] * self.KEY_BUF_LEN )
        return self.buffer_cache[name]

    def read_buttons(self):
        for b in self.buffer_cache:
            fcntl.ioctl(self.filehandle_cache[b], self.EVIOCGKEY, self.buffer_cache[b])

    def check_buttons(self):
        pressed = []
        self.read_buttons()
        for k,v in self._buttons.items():
            buf = self.buffer_cache[v['name']]
            bit = v['value']
            if not bool(buf[int(bit / 8)] & 1 << bit % 8):
                pressed += [k]
        return pressed

    @property
    def any(self):
        return bool(len(self.check_buttons()) != 0)

    @property
    def which(self):
        return self.check_buttons()

    def these(self,buttons={}):
        if len(buttons) == 0:
            return False
        s = self.check_buttons()
        if len(s) == 0:
            return False
        for b in buttons:
            if b not in s:
                return False
        return True

#~autogen
    if current_platform() == 'ev3':
#~autogen button-property platforms.ev3.button>currentClass
        _buttons = { 
            'up' : { 'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 103 },
            'down' : { 'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 108 },
            'left' : { 'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 105 },
            'right' : { 'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 106 },
            'enter' : { 'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 28 },
            'backspace' : { 'name': '/dev/input/by-path/platform-gpio-keys.0-event', 'value': 14 },
        }

        @property
        def up(self):
            return 'up' in self.check_buttons()

        @property
        def down(self):
            return 'down' in self.check_buttons()

        @property
        def left(self):
            return 'left' in self.check_buttons()

        @property
        def right(self):
            return 'right' in self.check_buttons()

        @property
        def enter(self):
            return 'enter' in self.check_buttons()

        @property
        def backspace(self):
            return 'backspace' in self.check_buttons()


#~autogen
#~autogen generic-class classes.powerSupply>currentClass

class PowerSupply(Device):

    """
    A generic interface to read data from the system's power_supply class.
    Uses the built-in legoev3-battery if none is specified.
    """

    SYSTEM_CLASS_NAME = 'power_supply'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

#~autogen
#~autogen generic-get-set classes.powerSupply>currentClass


    @property
    def measured_current(self):
        """
        The measured current that the battery is supplying (in microamps)
        """
        return self.get_attr_int( 'current_now' )

    @property
    def measured_voltage(self):
        """
        The measured voltage that the battery is supplying (in microvolts)
        """
        return self.get_attr_int( 'voltage_now' )

    @property
    def max_voltage(self):
        """
        """
        return self.get_attr_int( 'voltage_max_design' )

    @property
    def min_voltage(self):
        """
        """
        return self.get_attr_int( 'voltage_min_design' )

    @property
    def technology(self):
        """
        """
        return self.get_attr_string( 'technology' )

    @property
    def type(self):
        """
        """
        return self.get_attr_string( 'type' )


#~autogen

    @property
    def measured_amps(self):
        """
        The measured current that the battery is supplying (in amps)
        """
        return self.measured_current / 1e6

    @property
    def measured_volts(self):
        """
        The measured voltage that the battery is supplying (in volts)
        """
        return self.measured_voltage / 1e6

#~autogen generic-class classes.legoPort>currentClass

class LegoPort(Device):

    """
    The `lego-port` class provides an interface for working with input and
    output ports that are compatible with LEGO MINDSTORMS RCX/NXT/EV3, LEGO
    WeDo and LEGO Power Functions sensors and motors. Supported devices include
    the LEGO MINDSTORMS EV3 Intelligent Brick, the LEGO WeDo USB hub and
    various sensor multiplexers from 3rd party manufacturers.
    
    Some types of ports may have multiple modes of operation. For example, the
    input ports on the EV3 brick can communicate with sensors using UART, I2C
    or analog validate signals - but not all at the same time. Therefore there
    are multiple modes available to connect to the different types of sensors.
    
    In most cases, ports are able to automatically detect what type of sensor
    or motor is connected. In some cases though, this must be manually specified
    using the `mode` and `set_device` attributes. The `mode` attribute affects
    how the port communicates with the connected device. For example the input
    ports on the EV3 brick can communicate using UART, I2C or analog voltages,
    but not all at the same time, so the mode must be set to the one that is
    appropriate for the connected sensor. The `set_device` attribute is used to
    specify the exact type of sensor that is connected. Note: the mode must be
    correctly set before setting the sensor type.
    
    Ports can be found at `/sys/class/lego-port/port<N>` where `<N>` is
    incremented each time a new port is registered. Note: The number is not
    related to the actual port at all - use the `port_name` attribute to find
    a specific port.
    """

    SYSTEM_CLASS_NAME = 'lego_port'
    SYSTEM_DEVICE_NAME_CONVENTION = '*'

    def __init__(self, port=None, name=SYSTEM_DEVICE_NAME_CONVENTION, **kwargs):
        if port is not None:
            kwargs['port_name'] = port
        Device.__init__(self, self.SYSTEM_CLASS_NAME, name, **kwargs)

#~autogen
#~autogen generic-get-set classes.legoPort>currentClass


    @property
    def driver_name(self):
        """
        Returns the name of the driver that loaded this device. You can find the
        complete list of drivers in the [list of port drivers].
        """
        return self.get_attr_string( 'driver_name' )

    @property
    def modes(self):
        """
        Returns a list of the available modes of the port.
        """
        return self.get_attr_set( 'modes' )

    @property
    def mode(self):
        """
        Reading returns the currently selected mode. Writing sets the mode.
        Generally speaking when the mode changes any sensor or motor devices
        associated with the port will be removed new ones loaded, however this
        this will depend on the individual driver implementing this class.
        """
        return self.get_attr_string( 'mode' )

    @mode.setter
    def mode(self, value):
        self.set_attr_string( 'mode', value )

    @property
    def port_name(self):
        """
        Returns the name of the port. See individual driver documentation for
        the name that will be returned.
        """
        return self.get_attr_string( 'port_name' )

    @property
    def set_device(self):
        """
        For modes that support it, writing the name of a driver will cause a new
        device to be registered for that driver and attached to this port. For
        example, since NXT/Analog sensors cannot be auto-detected, you must use
        this attribute to load the correct driver. Returns -EOPNOTSUPP if setting a
        device is not supported.
        """
        raise Exception( "set_device is a write-only property!" )

    @set_device.setter
    def set_device(self, value):
        self.set_attr_string( 'set_device', value )

    @property
    def status(self):
        """
        In most cases, reading status will return the same value as `mode`. In
        cases where there is an `auto` mode additional values may be returned,
        such as `no-device` or `error`. See individual port driver documentation
        for the full list of possible values.
        """
        return self.get_attr_string( 'status' )


#~autogen

