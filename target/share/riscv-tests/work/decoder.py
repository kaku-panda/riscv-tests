class Decoder:
    def __init__(self):
        pass

    def decode_instruction(self, instruction):
        opcode = instruction & 0x7F
        if opcode == 0x33:  # R-type
            return self.decode_r_type(instruction)
        elif opcode in [0x03, 0x13, 0x1B]:  # I-type
            return self.decode_i_type(instruction)
        elif opcode == 0x23:  # S-type
            return self.decode_s_type(instruction)
        elif opcode == 0x63:  # B-type
            return self.decode_b_type(instruction)
        elif opcode in [0x37, 0x17]:  # U-type
            return self.decode_u_type(instruction)
        elif opcode in [0x6F, 0x67]:  # J-type
            return self.decode_j_type(instruction)
        elif opcode == 0x0f:  # FENCE
            return self.decode_fence(instruction)
        elif opcode == 0x73:  # CSR
            return self.decode_system_instruction(instruction)
        else:
            return Instruction(f"Unknown Instruction Type ({hex(instruction)})")
        
    def decode_r_type(self, instruction):
        funct7 = instruction  >> 25
        rs2    = (instruction >> 20) & 0x1F
        rs1    = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rd     = (instruction >> 7) & 0x1F
        
        if funct7 == 0x00:
            if funct3 == 0x0:
                return Instruction("ADD", rd, rs1, rs2)
            elif funct3 == 0x1:
                return Instruction("SLL", rd, rs1, rs2)
            elif funct3 == 0x2:
                return Instruction("SLT", rd, rs1, rs2)
            elif funct3 == 0x3:
                return Instruction("SLTU", rd, rs1, rs2)
            elif funct3 == 0x4:
                return Instruction("XOR", rd, rs1, rs2)
            elif funct3 == 0x5:
                return Instruction("SRL", rd, rs1, rs2)
            elif funct3 == 0x6:
                return Instruction("OR", rd, rs1, rs2)
            elif funct3 == 0x7:
                return Instruction("AND", rd, rs1, rs2)
        elif funct7 == 0x20:
            if funct3 == 0x0:
                return Instruction("SUB", rd, rs1, rs2)
            elif funct3 == 0x5:
                return Instruction("SRA", rd, rs1, rs2)

        return Instruction(f"Unknown R-type Instruction ({hex(instruction)})")

    def decode_i_type(self, instruction):
        imm    = (instruction >> 20)
        rs1    = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rd     = (instruction >>  7) & 0x1F
        opcode = instruction & 0x7F
        
        if imm & 0x800:
            imm = imm | 0xFFFFF000

        if opcode == 0x03:
            load_operations = {
                0x0: "LB",
                0x1: "LH",
                0x2: "LW",
                0x4: "LBU",
                0x5: "LHU"
            }
            return Instruction(load_operations.get(funct3, f"Unknown I-type Instruction ({hex(instruction)})"), rd, rs1, imm)
        elif opcode == 0x13:
            arithmetic_operations = {
                0x0: "ADDI",
                0x2: "SLTI",
                0x3: "SLTIU",
                0x4: "XORI",
                0x6: "ORI",
                0x7: "ANDI",
                0x1: "SLLI",
                0x5: "SRLI" if imm >> 5 == 0x00 else "SRAI"
            }
            return Instruction(arithmetic_operations.get(funct3, f"Unknown I-type Instruction ({hex(instruction)})"), rd, rs1, imm)

        return Instruction(f"Unknown I-type Instruction ({hex(instruction)})")
                

    def decode_s_type(self, instruction):
        imm_11_5 = (instruction >> 25) & 0x7F
        imm_4_0  = (instruction >>  7) & 0x1F
        rs2      = (instruction >> 20) & 0x1F
        rs1      = (instruction >> 15) & 0x1F
        funct3   = (instruction >> 12) & 0x7

        imm = (imm_11_5 << 5) | imm_4_0
        if imm & 0x800:
            imm |= 0xFFFFF000

        store_operations = {
            0x0: "SB",
            0x1: "SH",
            0x2: "SW"
        }

        return Instruction(store_operations.get(funct3, f"Unknown S-type Instruction ({hex(instruction)})"), rs2, rs1, imm)

    def decode_b_type(self, instruction):
        imm_12   = (instruction >> 31) & 0x1
        imm_10_5 = (instruction >> 25) & 0x3F
        imm_4_1  = (instruction >>  8) & 0xF
        imm_11   = (instruction >>  7) & 0x1
        rs2      = (instruction >> 20) & 0x1F
        rs1      = (instruction >> 15) & 0x1F
        funct3   = (instruction >> 12) & 0x7

        imm = (imm_12 << 12) | (imm_11 << 11) | (imm_10_5 << 5) | (imm_4_1 << 1)
        if imm & 0x1000:
            imm = imm - 0x2000

        branch_operations = {
            0x0: "BEQ",
            0x1: "BNE",
            0x4: "BLT",
            0x5: "BGE",
            0x6: "BLTU",
            0x7: "BGEU"
        }

        return Instruction(branch_operations.get(funct3, f"Unknown B-type Instruction ({hex(instruction)})"), rs1, rs2, imm)

    def decode_u_type(self, instruction):
        imm    = (instruction >> 12) & 0xFFFFF
        rd     = (instruction >> 7) & 0x1F
        opcode = instruction & 0x7F

        if opcode == 0x37:
            return Instruction("LUI", rd, imm)
        elif opcode == 0x17:
            return Instruction("AUIPC", rd, imm)

        return Instruction(f"Unknown U-type Instruction ({hex(instruction)})")

    def decode_j_type(self, instruction):
        imm_20    = (instruction >> 31) & 0x1
        imm_10_1  = (instruction >> 21) & 0x3FF
        imm_11    = (instruction >> 20) & 0x1
        imm_19_12 = (instruction >> 12) & 0xFF
        rd        = (instruction >> 7) & 0x1F
        opcode    = instruction & 0x7F

        # オフセット（即値）の組み立てと符号拡張
        imm = (imm_20 << 20) | (imm_19_12 << 12) | (imm_11 << 11) | (imm_10_1 << 1)
        if imm & 0x80000:  # 20ビット目で符号拡張
            imm = imm - 0x1000000

        if opcode == 0x6F:
            return Instruction("JAL", rd, imm)
        if opcode == 0x67:
            return Instruction("JALR", rd, imm)

        return Instruction(f"Unknown J-type Instruction ({hex(instruction)})")
    
    def decode_fence(self, instruction):
        funct3 = (instruction >> 12) & 0x7
        if funct3 == 0x0:
            pred = (instruction >> 24) & 0xF
            succ = (instruction >> 20) & 0xF
            return Instruction("FENCE", pred, succ)
        elif funct3 == 0x1:
            return Instruction("FENCE.I")

        return Instruction(f"Unknown FENCE Instruction ({hex(instruction)})")

    def decode_csr_type(self, instruction):
        csr    = (instruction >> 20) & 0xFFF
        imm    = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rd     = (instruction >> 7) & 0x1F

        csr_operations = {
            0x1: "CSRRW",
            0x2: "CSRRS",
            0x3: "CSRRC",
            0x5: "CSRRWI",
            0x6: "CSRRSI",
            0x7: "CSRRCI"
        }
        operation = csr_operations.get(funct3, f"Unknown CSR Instruction {hex(instruction)}")

        return Instruction(operation, rd, csr, imm)
    
    def decode_system_instruction(self, instruction):
        imm    = (instruction >> 20) & 0xFFF
        funct3 = (instruction >> 12) & 0x7
        if imm == 0x000 and funct3 == 0x0:
            return Instruction("ECALL")
        elif imm == 0x001 and funct3 == 0x0:
            return Instruction("EBREAK")
        elif imm == 0x302 and funct3 == 0x0:
            return Instruction("MRET")
        else:
            return self.decode_csr_type(instruction)

class Instruction:
    def __init__(self, name, arg1=None, arg2=None, arg3=None):
        self.name = name
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3

    def __str__(self):
        args = ', '.join(hex(arg) for arg in [self.arg1, self.arg2, self.arg3] if arg is not None)
        return f"{self.name} {args}"
