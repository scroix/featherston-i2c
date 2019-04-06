"""MCP3428 0-10V Analog Controller"""

# Utilises Process() from the toolkit to run an external Python script for reading and writing to the MCP3428 whilst attached to the Raspberry Pi.

# The board in question.
# https://ncd.io/raspberry-pi-0-10v-analog-output-module/

# The pin configuration on the Raspberry Pi.
# https://pinout.xyz/pinout/i2c#


import os


# Parameters used by this Node
STATUS_CHECK_INTERVAL = 75  # seconds between checking script is running without errors
VOLTAGE_CHECK_INTERVAL = 60 * 5

python = '/usr/bin/python3.5'
script = 'mcp3428.py'

param_disabled = Parameter({'title': 'Disabled', 'schema': {'type': 'boolean'}, 'order': next_seq()})
param_debug = Parameter({'title': 'Debug', 'schema': {'type': 'boolean'}, 'order': next_seq()})


# Local actions this Node provides
@local_action({'title': 'Set Voltage', 'group': 'Basic', 'schema': {'type': 'number', 'min': 0, 'max': 10}})
def set_voltage(arg):
    command = [python, script, str(arg)]
    if param_debug:
        console.info(command)
    proc = quick_process(command, finished = handle_stdout)
    console.info("Voltage set [%s]." % arg)


@local_action({'title': 'Get Voltage', 'group': 'Basic'})
def get_voltage(arg):
    command = [python, script]
    if param_debug:
        console.info(command)
    proc = quick_process(command, finished = handle_stdout)
    console.info("Voltage requested.")


# Functions used by this Node
def handle_stdout(message):
    if "Output" in message.stdout:
        lookup_local_event('CurrentVoltage').emit(float(message.stdout.split()[2])) # expecting "Voltage Output: 0.0"
        lastReceive[0] = system_clock()
        if param_debug:
            console.log("stdout: %s" % message.stdout)
    elif "Set" in message.stdout:
        pass
    else:
        console.error("Unexpected response from script.")


# for comms drop-out
lastReceive = [0]

def statusCheck():
    diff = (system_clock() - lastReceive[0])/1000.0  # (in secs)
    now = date_now()

    if diff > STATUS_CHECK_INTERVAL+15:
        previousContactValue = local_event_LastContactDetect.getArg()

        if previousContactValue == None:
            message = 'Always been missing.'

        else:
            previousContact = date_parse(previousContactValue)
            roughDiff = (now.getMillis() - previousContact.getMillis())/1000/60
            if roughDiff < 60:
                message = 'Missing for approx. %s mins' % roughDiff
            elif roughDiff < (60*24):
                message = 'Missing since %s' % previousContact.toString(
                    'h:mm:ss a')
            else:
                message = 'Missing since %s' % previousContact.toString(
                    'h:mm:ss a, E d-MMM')

        local_event_Status.emit({'level': 2, 'message': message})

    else:
        # update contact info
        local_event_LastContactDetect.emit(str(now))
        local_event_Status.emit({'level': 0, 'message': 'OK'})


# Local events this Node provides
local_event_CurrentVoltage = LocalEvent({'title': 'Current Voltage', 'group': 'Basic', 'order': next_seq(), 'schema': {'type': 'number'}})
local_event_LastContactDetect = LocalEvent({'title': 'Last Contact Timestamp', 'group': 'Status', 'order': 99999+next_seq(), 'schema': {'type': 'string'}})
local_event_Status = LocalEvent({'group': 'Status', 'order': 99999+next_seq(), 'schema': {'type': 'object', 'properties': {
    'level': {'type': 'integer', 'order': 1},
    'message': {'type': 'string', 'order': 2}}}})


# Timers this Node utilises
status_timer = Timer(statusCheck, STATUS_CHECK_INTERVAL)
voltage_poller = Timer(lambda: lookup_local_action('get_voltage').call(), VOLTAGE_CHECK_INTERVAL, VOLTAGE_CHECK_INTERVAL * 0.1, stopped=False)


def main(arg=None):
    console.info("Recipe has begun cooking!")

    if param_disabled:
        console.warn('Recipe disabled.')
    else:
        # All conditions satisfied to begin recipe.
        voltage_poller.start()
