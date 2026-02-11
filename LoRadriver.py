import spidev
import time
import RPi.GPIO as GPIO

PIN_RESET = 17
PIN_DIO0  = 25

REG_FIFO = 0x00
REG_OP_MODE = 0x01
REG_FRF_MSB = 0x06
REG_FRF_MID = 0x07
REG_FRF_LSB = 0x08
REG_PA_CONFIG = 0x09
REG_LNA = 0x0C
REG_FIFO_ADDR_PTR = 0x0D
REG_FIFO_TX_BASE_ADDR = 0x0E
REG_FIFO_RX_BASE_ADDR = 0x0F
REG_FIFO_RX_CURRENT_ADDR = 0x10
REG_IRQ_FLAGS = 0x12
REG_RX_NB_BYTES = 0x13
REG_MODEM_CONFIG_1 = 0x1D
REG_MODEM_CONFIG_2 = 0x1E
REG_MODEM_CONFIG_3 = 0x26
REG_PAYLOAD_LENGTH = 0x22
REG_VERSION = 0x42

MODE_LONG_RANGE = 0x80
MODE_SLEEP = 0x00
MODE_STDBY = 0x01
MODE_TX = 0x03
MODE_RX_CONTINUOUS = 0x05


class LoRa:
    def __init__(self, freq=915e6):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 5000000
        self.spi.mode = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_RESET, GPIO.OUT)
        GPIO.setup(PIN_DIO0, GPIO.IN)

        GPIO.output(PIN_RESET, 0)
        time.sleep(0.01)
        GPIO.output(PIN_RESET, 1)
        time.sleep(0.01)

        if self.read(REG_VERSION) != 0x12:
            raise Exception("SX1276 tidak terdeteksi")

        print("SX1276 OK")

        self.write(REG_OP_MODE, MODE_LONG_RANGE | MODE_SLEEP)
        time.sleep(0.01)
        self.write(REG_OP_MODE, MODE_LONG_RANGE | MODE_STDBY)

        self.set_frequency(freq)
        self.set_long_range()

        self.write(REG_FIFO_TX_BASE_ADDR, 0)
        self.write(REG_FIFO_RX_BASE_ADDR, 0)

        self.write(REG_OP_MODE, MODE_LONG_RANGE | MODE_RX_CONTINUOUS)
        print("LoRa LONG RANGE siap")

    #LOW LEVEL
    def read(self, addr):
        return self.spi.xfer2([addr & 0x7F, 0x00])[1]

    def write(self, addr, val):
        self.spi.xfer2([addr | 0x80, val])

    #CONFIG
    def set_frequency(self, freq):
        frf = int((freq / 32e6) * (1 << 19))
        self.write(REG_FRF_MSB, (frf >> 16) & 0xFF)
        self.write(REG_FRF_MID, (frf >> 8) & 0xFF)
        self.write(REG_FRF_LSB, frf & 0xFF)
        print(f"Frequency {freq/1e6:.1f} MHz")

    def set_long_range(self):
        # BW 125 kHz, Coding Rate 4/5
        self.write(REG_MODEM_CONFIG_1, 0x72)

        # SF12 + CRC ON
        self.write(REG_MODEM_CONFIG_2, (12 << 4) | 0x04)

        # Low Data Rate Optimize
        self.write(REG_MODEM_CONFIG_3, 0x0C)

        # TX power MAX (~17 dBm)
        self.write(REG_PA_CONFIG, 0x8F)

        # RX gain MAX
        self.write(REG_LNA, 0x23)

        print("Mode LONG RANGE aktif")

    #TX
    def send(self, data: bytes):
        self.write(REG_OP_MODE, MODE_LONG_RANGE | MODE_STDBY)
        self.write(REG_FIFO_ADDR_PTR, 0)

        for b in data:
            self.write(REG_FIFO, b)

        self.write(REG_PAYLOAD_LENGTH, len(data))
        self.write(REG_OP_MODE, MODE_LONG_RANGE | MODE_TX)

        while GPIO.input(PIN_DIO0) == 0:
            time.sleep(0.001)

        self.write(REG_IRQ_FLAGS, 0xFF)
        self.write(REG_OP_MODE, MODE_LONG_RANGE | MODE_RX_CONTINUOUS)

        print("TX:", data.decode(errors="ignore"))

    #RX
    def receive(self):
        irq = self.read(REG_IRQ_FLAGS)

        if not (irq & 0x40):
            return None

        self.write(REG_IRQ_FLAGS, 0xFF)

        addr = self.read(REG_FIFO_RX_CURRENT_ADDR)
        self.write(REG_FIFO_ADDR_PTR, addr)

        length = self.read(REG_RX_NB_BYTES)
        payload = bytes(self.read(REG_FIFO) for _ in range(length))

        return payload