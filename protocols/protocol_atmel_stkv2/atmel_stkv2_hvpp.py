'''
            GDP - The Generic Device Programmer.

    By Dean Camera (dean [at] fourwalledcubicle [dot] com)
'''

from core import *
from protocols import *
from protocols.protocol_atmel_stkv2.atmel_stkv2_base import *


class ProtocolAtmelSTKV2_HVPP(ProtocolAtmelSTKV2_Base):
    def set_interface_frequency(self, target_frequency):
        pass


    def enter_session(self):
        packet = [AtmelSTKV2Defs.commands["ENTER_PROGMODE_PP"]]
        packet.append(self.device.get_param("pp_interface", "PpEnterProgMode_stabDelay"))
        packet.append(self.device.get_param("pp_interface", "PpEnterProgMode_progModeDelay"))
        packet.append(self.device.get_param("pp_interface", "PpEnterProgMode_latchCycles"))
        packet.append(self.device.get_param("pp_interface", "PpEnterProgMode_toggleVtg"))
        packet.append(self.device.get_param("pp_interface", "PpEnterProgMode_powoffDelay"))
        packet.append(self.device.get_param("pp_interface", "PpEnterProgMode_resetDelayMs"))
        packet.append(self.device.get_param("pp_interface", "PpEnterProgMode_resetDelayUs"))
        self._trancieve(packet)


    def exit_session(self):
        packet = [AtmelSTKV2Defs.commands["LEAVE_PROGMODE_PP"]]
        packet.append(self.device.get_param("pp_interface", "PpLeaveProgMode_stabDelay"))
        packet.append(self.device.get_param("pp_interface", "PpLeaveProgMode_resetDelay"))
        self._trancieve(packet)


    def erase_memory(self, memory_space):
        if memory_space is None:
            packet = [AtmelSTKV2Defs.commands["CHIP_ERASE_PP"]]
            packet.append(self.device.get_param("pp_interface", "PpChipErase_pulseWidth"))
            packet.append(self.device.get_param("pp_interface", "PpChipErase_pollTimeout"))
            self._trancieve(packet)
        else:
            raise ProtocolError("The specified tool cannot erase the requested memory space.")


    def read_memory(self, memory_space, offset, length):
        mem_contents = []

        if memory_space is None:
            raise ProtocolError("Read failed as memory space not set.")
        elif memory_space in ["signature", "lockbits", "fuses"]:
            mem_command_map = {
                "signature" : AtmelSTKV2Defs.commands["READ_SIGNATURE_PP"],
                "lockbits"  : AtmelSTKV2Defs.commands["READ_LOCK_PP"],
                "fuses"     : AtmelSTKV2Defs.commands["READ_FUSE_PP"]
            }

            for x in xrange(length):
                packet = [mem_command_map[memory_space]]
                packet.append(offset + x)

                resp = self._trancieve(packet)
                mem_contents.append(resp[2])
        elif memory_space in ["eeprom", "flash"]:
            blocksize = self.device.get_param("pp_interface", "PpRead%s_blockSize" % memory_space.capitalize())

            for (address, chunklen) in Util.chunk_address(length, blocksize, offset):
                if memory_space == "eeprom":
                    self._set_address(address)

                    packet = [AtmelSTKV2Defs.commands["READ_EEPROM_PP"]]
                    packet.extend([chunklen >> 8, chunklen & 0xFF])
                else:
                    self._set_address(address >> 1)

                    packet = [AtmelSTKV2Defs.commands["READ_FLASH_PP"]]
                    packet.extend([chunklen >> 8, chunklen & 0xFF])

                resp = self._trancieve(packet)

                page_data = resp[2 : -1]
                mem_contents.extend(page_data[0 : chunklen])

            mem_contents = mem_contents[0 : length]
        else:
            raise NotImplementedError()

        return mem_contents


    def write_memory(self, memory_space, offset, data):
        if memory_space is None:
            raise ProtocolError("Write failed as memory space not set.")
        elif memory_space == "lockbits":
            packet = [AtmelSTKV2Defs.commands["PROGRAM_LOCK_PP"]]
            packet.append(offset)
            packet.append(data[0])
            packet.append(self.device.get_param("pp_interface", "PpProgramLock_pulseWidth"))
            packet.append(self.device.get_param("pp_interface", "PpProgramLock_pollTimeout"))
            self._trancieve(packet)
        elif memory_space == "fuses":
            for x in xrange(length):
                packet = [AtmelSTKV2Defs.commands["PROGRAM_FUSE_PP"]]
                packet.append(offset)
                packet.append(data[offset + x])
                packet.append(self.device.get_param("pp_interface", "PpProgramFuse_pulseWidth"))
                packet.append(self.device.get_param("pp_interface", "PpProgramFuse_pollTimeout"))
                self._trancieve(packet)
        elif memory_space in ["eeprom", "flash"]:
            blocksize = self.device.get_param("pp_interface", "PpProgram%s_blockSize" % memory_space.capitalize())

            for (address, chunk) in Util.chunk_data(data, blocksize, offset):
                if memory_space == "eeprom":
                    self._set_address(address)
                    packet = [AtmelSTKV2Defs.commands["PROGRAM_EEPROM_PP"]]
                else:
                    self._set_address(address >> 1)
                    packet = [AtmelSTKV2Defs.commands["PROGRAM_FLASH_PP"]]

                packet.extend([blocksize >> 8, blocksize & 0xFF])
                packet.append(self.device.get_param("pp_interface", "PpProgram%s_mode" % memory_space.capitalize()) | 0x80)
                packet.append(self.device.get_param("pp_interface", "PpProgram%s_pollTimeout" % memory_space.capitalize()))
                packet.extend(chunk)

                self._trancieve(packet)
        else:
            raise NotImplementedError()
