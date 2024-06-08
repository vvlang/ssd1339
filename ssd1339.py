# ssd1339.py
import framebuf
import utime
import gc
import micropython
from drivers.boolpalette import BoolPalette

class SSD1339(framebuf.FrameBuffer):
    @staticmethod
    def rgb(r, g, b):
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    def __init__(self, spi, pincs, pindc, pinrs, height=128, width=128, init_spi=False):
        if height not in (96, 128):
            raise ValueError('Unsupported height {}'.format(height))
        self.spi = spi
        self.spi_init = init_spi
        self.pincs = pincs
        self.pindc = pindc  # 1 = data 0 = cmd
        self.height = height  # Required by Writer class
        self.width = width
        mode = framebuf.RGB565
        self.palette = BoolPalette(mode)
        gc.collect()
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, mode)
        self.mvb = memoryview(self.buffer)
        pinrs(0)  # Pulse the reset line
        utime.sleep_ms(1)
        pinrs(1)
        utime.sleep_ms(1)
        if self.spi_init:  # A callback was passed
            self.spi_init(spi)  # Bus may be shared
        # See above comment to explain this allocation-saving gibberish.
        self._write(b'\xfd\x12\xfd\xb1\xae\xb3\xf1\xca\x7f\xa0\x74'\
        b'\x15\x00\x7f\x75\x00\x7f\xa1\x00\xa2\x00\xb5\x00\xab\x01'\
        b'\xb1\x32\xbe\x05\xa6\xc1\xc8\x80\xc8\xc7\x0f'\
        b'\xb4\xa0\xb5\x55\xb6\x01\xaf', 0)
        self.show()
        gc.collect()
    def _write(self, mv, dc):
        self.pincs(1)
        self.pindc(dc)
        self.pincs(0)
        self.spi.write(bytes(mv))
        self.pincs(1)
    def show(self):
        mvb = self.mvb
        bw = self.width * 2  # Width in bytes
        if self.spi_init:  # A callback was passed
            self.spi_init(self.spi)  # Bus may be shared
        self._write(b'\x5c', 0)  # Enable data write
        if self.height == 128:
            for l in range(128):
                l0 = (95 - l) % 128  # 95 94 .. 1 0 127 126 .. 96
                start = l0 * self.width * 2
                self._write(mvb[start : start + bw], 1)  # Send a line
        else:
            for l in range(128):
                if l < 64:
                    start = (63 -l) * self.width * 2  # 63 62 .. 1 0
                elif l < 96:
                    start = 0
                else:
                    start = (191 - l) * self.width * 2  # 127 126 .. 95
                self._write(mvb[start : start + bw], 1)  # Send a line
    def init_display(self):
        # Sleep mode
        self.write_command(0xAE)

        # Set Re-map / Color Depth
        self.write_commands(0xA0, 0xB4)

        # Set Display Start Line
        self.write_commands(0xA1, 0x00)

        # Set Display Offset
        self.write_commands(0xA2, 0x00)

        # Set Display Mode
        self.write_command(0xA6)

        # Set Master Configuration
        self.write_commands(0xAD, 0x8E)

        # Set Power Saving Mode
        self.write_commands(0xB0, 0x05)

        # Set Reset (Phase1)/Pre-charge (Phase 2) period
        self.write_commands(0xB1, 0x11)

        # Set Oscillator Frequency / Clock Divider
        self.write_commands(0xB3, 0xF0)

        # Set Look Up Table for Gray Scale Pulse width
        self.write_commands(0xB8, *range(1, 125, 5))

        # Set Pre-charge voltage of Color A, B, C
        self.write_commands(0xBB, 0x1C, 0x1C, 0x1C)

        # Set VCOMH
        self.write_commands(0xBE, 0x3F)

        # Set Contrast Current
        self.write_commands(0xC1, 0xDC, 0xD2, 0xFF)

        # Set Master Current
        self.write_commands(0xC7, 0x0A)

        # Set MUX Ratio
        self.write_commands(0xCA, 0x7F)

        # Set Display Mode
        self.write_command(0xAF)
