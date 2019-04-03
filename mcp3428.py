import sys
from smbus2 import SMBus

# Get i2C bus
bus = SMBus(1)

# 'i2cdetect -y 1' for address
DEVICE_ADDRESS = 0x60
DEVICE_OFFSET = 0x60
BYTES_TO_READ = 2


def convert_to_12bits(voltage):
    return int(0 + ((voltage / 10) * 4095))


def convert_to_voltage(byte):
    return round(float(0 + ((byte / 255) * 10)), 1)


def clamp_to_unsigned12bit(value):
    if value > 4095:
        value = 4095
    if value < 0:
        value = 0
    return value


def clamp_to_10volts(value):
    if value > 10:
        value = 10
    if value < 0:
        value = 0
    return value


def set_voltage(volts):
    raw_value = clamp_to_unsigned12bit(convert_to_12bits(volts))

    data = [(raw_value >> 4) & 0xFF, (raw_value << 4) & 0xFF]

    # Write a block of len(data) bytes to address from offset
    bus.write_i2c_block_data(DEVICE_ADDRESS, DEVICE_OFFSET, data)

    print("Voltage Set: %d" % volts)


def read_voltage():
    data = bus.read_i2c_block_data(DEVICE_ADDRESS, DEVICE_OFFSET, 2)
    return convert_to_voltage(data[1])


if len(sys.argv) > 1:
    try:
        voltage = float(sys.argv[1])
        set_voltage(clamp_to_10volts(voltage))
    except ValueError:
        print("That isn't a volt!")
else:
    print("Voltage Output: %.1f" % read_voltage())
