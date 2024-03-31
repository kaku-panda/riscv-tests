import sys
import re
import decoder

class RISCVSimulator:
    def __init__(self):
        self.pc = 0                      # Program Counter
        self.instructions = {}           # Instructions
        self.registers = [0] * 32        # Registers
        self.memory  = bytearray(256)    # Memory
        self.decoder = decoder.Decoder() # decoder

    def load_instructions(self, init_pc, instructions):
        self.pc = init_pc
        self.instructions = instructions

    def fetch_instruction(self):
        instruction = self.instructions.get(hex(self.pc))
        return instruction
    
    def read_memory(self, address, num_bytes, signed=False):
        value = int.from_bytes(self.memory[address:address+num_bytes], byteorder='little', signed=signed)
        return value
    
    def write_memory(self, address, value, num_bytes):
        self.memory[address:address+num_bytes] = value.to_bytes(num_bytes, byteorder='little')

    def read_register(self, index):
        n = self.registers[index] & 0xFFFFFFFF
        return (n ^ 0x80000000) - 0x80000000

    def decode_instruction(self, instruction):
        return self.decoder.decode_instruction(instruction)

    def execute_instruction(self, instruction):

        if instruction.name in ["ADD", "SUB", "SLL", "SLT", "SLTU", "XOR", "SRL", "SRA", "OR", "AND"]:
            if instruction.name == "ADD":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) + self.read_register(instruction.arg3)
            elif instruction.name == "SUB":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) - self.read_register(instruction.arg3)
            elif instruction.name == "SLL":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) << (self.read_register(instruction.arg3) & 0x1F)
            elif instruction.name == "SLT":
                self.registers[instruction.arg1] = int(self.read_register(instruction.arg2) < self.read_register(instruction.arg3))
            elif instruction.name == "SLTU":
                self.registers[instruction.arg1] = int((self.read_register(instruction.arg2) & 0xFFFFFFFF) < (self.read_register(instruction.arg3) & 0xFFFFFFFF))
            elif instruction.name == "XOR":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) ^ self.read_register(instruction.arg3)
            elif instruction.name == "SRL":
                self.registers[instruction.arg1] = (self.read_register(instruction.arg2) & 0xFFFFFFFF) >> (self.read_register(instruction.arg3) & 0x1F)
            elif instruction.name == "SRA":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) >> (self.read_register(instruction.arg3) & 0x1F)
            elif instruction.name == "OR":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) | self.read_register(instruction.arg3)
            elif instruction.name == "AND":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) & self.read_register(instruction.arg3)
        
        # I型命令の処理
        elif instruction.name in ["ADDI", "SLTI", "SLTIU", "XORI", "ORI", "ANDI", "SLLI", "SRLI"]:
            if instruction.name == "ADDI":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) + instruction.arg3
            elif instruction.name == "SLTI":
                self.registers[instruction.arg1] = int(self.read_register(instruction.arg2) < instruction.arg3)
            elif instruction.name == "SLTIU":
                self.registers[instruction.arg1] = int((self.read_register(instruction.arg2) & 0xFFFFFFFF) < (instruction.arg3 & 0xFFFFFFFF))
            elif instruction.name == "XORI":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) ^ instruction.arg3
            elif instruction.name == "ORI":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) | instruction.arg3
            elif instruction.name == "ANDI":
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) & instruction.arg3
            elif instruction.name == "SLLI":
                shamt = instruction.arg3 & 0x1F
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) << shamt
            elif instruction.name == "SRLI":
                shamt = instruction.arg3 & 0x1F 
                self.registers[instruction.arg1] = (self.read_register(instruction.arg2) & 0xFFFFFFFF) >> shamt
            elif instruction.name == "SRAI":
                shamt = instruction.arg3 & 0x1F
                self.registers[instruction.arg1] = self.read_register(instruction.arg2) >> shamt

        elif instruction.name in ["LB", "LH", "LW", "LBU", "LHU"]:
            address = self.read_register(instruction.arg2) + instruction.arg3
            if instruction.name == "LB":
                value = self.read_memory(address, 1, signed=True)
            elif instruction.name == "LH":
                value = self.read_memory(address, 2, signed=True)
            elif instruction.name == "LW":
                value = self.read_memory(address, 4, signed=True)
            elif instruction.name == "LBU":
                value = self.read_memory(address, 1, signed=False)
            elif instruction.name == "LHU":
                value = self.read_memory(address, 2, signed=False)
            self.registers[instruction.arg1] = value

        # S型命令の処理
        elif instruction.name in ["SB", "SH", "SW"]:
            address = self.read_register(instruction.arg2) + instruction.arg3
            value = self.read_register(instruction.arg1)
            if instruction.name == "SB":
                self.write_memory(address, value, 1)
            elif instruction.name == "SH":
                self.write_memory(address, value, 2)
            elif instruction.name == "SW":
                self.write_memory(address, value, 4)
        
        # B型命令の処理
        elif instruction.name in ["BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU"]:
            rs1_val: int = self.read_register(instruction.arg1)
            rs2_val: int = self.read_register(instruction.arg2)
            offset = instruction.arg3

            if instruction.name == "BEQ" and rs1_val == rs2_val:
                self.pc += offset
            elif instruction.name == "BNE" and rs1_val != rs2_val:
                self.pc += offset
            elif instruction.name == "BLT" and rs1_val < rs2_val:
                self.pc += offset
            elif instruction.name == "BGE" and rs1_val >= rs2_val:
                self.pc += offset
            elif instruction.name == "BLTU" and (rs1_val & 0xFFFFFFFF) < (rs2_val & 0xFFFFFFFF):
                self.pc += offset
            elif instruction.name == "BGEU" and (rs1_val & 0xFFFFFFFF) >= (rs2_val & 0xFFFFFFFF):
                self.pc += offset
            else:
                self.pc += 4
        
        # U型命令の処理
        elif instruction.name in ["LUI", "AUIPC"]:
            if instruction.name == "LUI":
                self.registers[instruction.arg1] = instruction.arg2 << 12
            elif instruction.name == "AUIPC":
                self.registers[instruction.arg1] = self.pc + (instruction.arg2 << 12)

        # J型命令の処理
        elif instruction.name in ["JAL", "JALR"]:
            if instruction.name == "JAL":
                self.registers[instruction.arg1] = self.pc + 4
                self.pc += instruction.arg2
            elif instruction.name == "JALR":
                temp_pc = self.pc
                self.pc = (self.read_register(instruction.arg2) + instruction.arg3) & ~1
                self.registers[instruction.arg1] = temp_pc + 4
        
        elif instruction.name in ["FENCE", "FENCE.I", "ECALL", "EBREAK", "MRET", "CSRRW", "CSRRS", "CSRRC", "CSRRWI", "CSRRSI","CSRRCI"]:
            if instruction.name == "CSRRS":
                self.registers[instruction.arg1] = 0x0
        else:
            print(f"Unsupported instruction: {instruction}")

        if instruction.name not in ["BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU", "JAL", "JALR"]:
            self.pc += 4
    
        self.registers[0] = 0

    def run(self):
        while True:
            instruction = self.fetch_instruction()
            if instruction is None:
                break
            decoded_instruction = self.decode_instruction(instruction)
            print(f"PC: {hex(self.pc)}, Instruction: {decoded_instruction} ({hex(instruction)})")
            self.execute_instruction(decoded_instruction)
            
            for i in range(0, len(self.registers), 8):
                reg_line = " ".join(f"x{j:2}:{reg & 0xFFFFFFFF:08x}" for j, reg in enumerate(self.registers[i:i+8]))
                print(reg_line)



        print(self.memory[:32])

def extract_instructions_from_dump(dump_file_path):
    instructions = {}
    pattern = re.compile(r'^\s*([0-9a-f]+):\s*([0-9a-f]+)\s+')

    init_pc = None

    with open(dump_file_path, 'r') as dump_file:
        for line in dump_file:
            match = pattern.match(line)
            if match:
                if init_pc is None:
                    init_pc = int(match.group(1), 16)
                pc = f"0x{match.group(1)}"
                instruction = int(match.group(2), 16)
                instructions |= {pc: instruction}
    
    return init_pc, instructions

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py <dump_file>")
        sys.exit(1)

    dump_file_path = sys.argv[1]
    init_pc, instructions = extract_instructions_from_dump(dump_file_path)

    simulator = RISCVSimulator()
    simulator.load_instructions(init_pc, instructions)
    simulator.run()
