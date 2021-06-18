# ARCv3 ELF ABI specification

## Table of Contents
1. [Register Convention](#register-convention)
	* [Integer Register Convention](#integer-register-convention)
	* [Floating-point Register Convention](#floating-point-register-convention)
2. [Procedure Calling Convention](#procedure-calling-convention)
	* [Integer Calling Convention](#integer-calling-convention)
	* [Hardware Floating-point Calling Convention](#hardware-floating-point-calling-convention)
	* [Default ABIs and C type sizes](#default-abis-and-c-type-sizes)
	* [va_list, va_start, and va_arg](#va-list-va-start-and-va-arg)
3. [ELF Object Files](#elf-object-file)
	* [File Header](#file-header)
	* [Sections](#sections)
	* [String Tables](#string-tables)
	* [Symbol Table](#symbol-table)
	* [Relocations](#relocations)
	* [Thread Local Storage](#thread-local-storage)
	* [Program Header Table](#program-header-table)
	* [Note Sections](#note-sections)
	* [Dynamic Table](#dynamic-table)
	* [Hash Table](#hash-table)
4. [DWARF](#dwarf)
	* [Dwarf Register Numbers](#dwarf-register-numbers)

## Copyright and license information

This ARCv3 ELF ABI specification document is

 &copy; 2020 Synopsys, Claudiu Zissulescu <claziss@synopsys.com>


# <a name=register-convention></a> Register Convention

Integer Register Convention <a name=integer-register-convention>
-------------------------------------------------------------------------
Name    | ABI Mnemonic | Meaning                | Available across calls?
--------|--------------|------------------------|------------------------
r0      | r0           | Argument 1/Return 1    | No
r1      | r1           | Argument 2/Return 2    | No
r2      | r2           | Argument 3/Return 3    | No
r3      | r3           | Argument 4/Return 4    | No
r4      | r4           | Argument 5             | No
r5      | r5           | Argument 6             | No
r6      | r6           | Argument 7             | No
r7      | r7           | Argument 8             | No
r8-r13  | r8-r13       | Temporary registers    | No
r14-r26 | r14-r26      | Callee-saved registers | Yes
r27     | fp           | Temp reg/Frame Pointer | Yes
r28     | sp           | Stack pointer          | Yes
r29     | ilink        | Interrupt link reg     | Yes
r30     | gp           | Global/Thread pointer  | Yes (can be used as GPR)
r31     | blink        | Return address         | No
r32-r57 | r32-r57      | Extension registers    | No
r31     | blink        | Return address         | No
r58     | accl         | Accumulator low        | No
r59     | acch         | Accumulator high       | No
r60     | slimm        | Signed-extended LIMM   | -- (Unallocatable)
r61     | N.A.         | Reserved               | -- (Unallocatable)
r60     | zlimm        | Zero-extended LIMM     | -- (Unallocatable)
r63     | pcl          | Program counter        | -- (Unallocatable)


In the standard ABI, procedures should not modify the integer
register tb, because signal handlers may rely upon their values.

Floating-point Register Convention <a name=floating-point-register-convention>
-------------------------------------------------------------------------
Name    | ABI Mnemonic | Meaning                | Available across calls?
--------|--------------|------------------------|------------------------
f0      | f0           | Argument 1/Return 1    | No
f1      | f1           | Argument 2             | No
f2      | f2           | Argument 3             | No
f3      | f3           | Argument 4             | No
f4      | f4           | Argument 5             | No
f5      | f5           | Argument 6             | No
f6      | f6           | Argument 7             | No
f7      | f7           | Argument 8             | No
f20-f31 | f20-f31      | Temporary registers    | Yes?

# <a name=procedure-calling-convention></a> Procedure Calling Convention
## <a name=integer-calling-convention></a> Integer Calling Convention

The base integer calling convention provides eight argument registers,
r0-r7, the first four of which are also used to return values.

Scalars that are at most 64 bits wide are passed in a single argument
register, or on the stack by value if none is available.  When passed
in registers, scalars narrower than 64 bits are widened according to
the sign of their type up to 32 bits, then sign-extended to 64 bits.

Scalars that are 2x64 bits wide are passed in a pair of argument
registers, or on the stack by value if none are available.  If exactly
one register is available, the low-order 64 bits are passed in the
register and the high-order 64 bits are passed on the stack.

Scalars wider than 2x64 are passed by reference and are replaced in
the argument list with the address.

Aggregates whose total size is no more than 64 bits are passed in a
register, with the fields laid out as though they were passed in
memory. If no register is available, the aggregate is passed on the
stack.  Aggregates whose total size is no more than 2x64 bits are
passed in a pair of registers; if only one register is available, the
first half is passed in a register and the second half is passed on
the stack. If no registers are available, the aggregate is passed on
the stack. Bits unused due to padding, and bits past the end of an
aggregate whose size in bits is not divisible by 64, are undefined.

Aggregates or scalars passed on the stack are aligned to the minimum
of the object alignment and the stack alignment.

Aggregates larger than 2x64 bits are passed by reference and are
replaced in the argument list with the address, as are C++ aggregates
with nontrivial copy constructors, destructors, or vtables.

Empty structs or union arguments or return values are ignored by C
compilers which support them as a non-standard extension.  This is not
the case for C++, which requires them to be sized types.

Bitfields are packed in little-endian fashion. A bitfield that would
span the alignment boundary of its integer type is padded to begin at
the next alignment boundary. For example, `struct { int x : 10; int y
: 12; }` is a 32-bit type with `x` in bits 9-0, `y` in bits 21-10, and
bits 31-22 undefined.  By contrast, `struct { short x : 10; short y :
12; }` is a 32-bit type with `x` in bits 9-0, `y` in bits 27-16, and
bits 31-28 and 15-10 undefined.

Arguments passed by reference may be modified by the callee.

Floating-point reals are passed the same way as aggregates of the same
size, complex floating-point numbers are passed the same way as a
struct containing two floating-point reals.

In the base integer calling convention, variadic arguments are passed
in the same manner as named arguments. After a variadic argument has
been passed on the stack, all future arguments will also be passed on
the stack.

Values are returned in the same manner as a first named argument of
the same type would be passed.  If such an argument would have been
passed by reference, the caller allocates memory for the return value,
and passes the address as an implicit first parameter.

The stack grows towards negative addresses and the stack pointer shall
be aligned to a 128-bit? boundary upon procedure entry.  In the
standard ABI, the stack pointer must remain aligned throughout
procedure execution. Non-standard ABI code must realign the stack
pointer prior to invoking standard ABI procedures.  The operating
system must realign the stack pointer prior to invoking a signal
handler; hence, POSIX signal handlers need not realign the stack
pointer.  In systems that service interrupts using the interruptee's
stack, the interrupt service routine must realign the stack pointer if
linked with any code that uses a non-standard stack-alignment
discipline, but need not realign the stack pointer if all code adheres
to the standard ABI.

Procedures must not rely upon the persistence of stack-allocated data
whose addresses lie below the stack pointer.

No floating-point registers, if present, are preserved across calls.

## <a name=hardware-floating-point-calling-convention></a> Hardware Floating-point Calling Convention


## <a name=default-abis-and-c-type-sizes></a> Default ABIs and C type sizes

While various different ABIs are technically possible, for software
compatibility reasons it is strongly recommended to use the following
default ABIs:

    Type        | Size (Bytes)  | Alignment (Bytes)
    ------------|---------------|------------------
    bool/_Bool  |  1            |  1
    char        |  1            |  1
    short       |  2            |  2
    int         |  4            |  4
    wchar_t     |  4            |  4
    wint_t      |  4            |  4
    long        |  8            |  8
    long long   |  8            |  8
    __int128    | 16            | 16
    void *      |  8            |  8
    float       |  4            |  4
    double      |  8            |  8
    long double | 16            | 16

`char` is unsigned.  `wchar_t` is signed.  `wint_t` is unsigned.

`_Complex` types have the alignment and layout of a struct containing two
fields of the corresponding real type (`float`, `double`, or `long double`),
with the first field holding the real part and the second field holding
the imaginary part.

## <a name=va-list-va-start-and-va-arg></a> va_list, va_start, and va_arg

The `va_list` type is `void*`. A callee with variadic arguments is responsible
for copying the contents of registers used to pass variadic arguments to the
vararg save area, which must be contiguous with arguments passed on the stack.
The `va_start` macro initializes its `va_list` argument to point to the start
of the vararg save area.  The `va_arg` macro will increment its `va_list`
argument according to the size of the given type, taking into account the
rules about 2x64 aligned arguments being passed in "aligned" register pairs.

## <a name=stack-frame></a> Stack Frame

ARC64 stack frame generated by GNU compiler looks like this:

	+-------------------------------+
	|                               |
	|  incoming stack arguments     |
	|                               |
	+-------------------------------+ <-- incoming stack pointer (aligned)
	|                               |
	|  callee-allocated save area   |
	|  for register varargs         |
	|                               |
	+-------------------------------+ <-- arg_pointer_rtx
	|                               |
	|  GPR save area                |
	|                               |
	+-------------------------------+
	|  Return address register      |
	|  (if required)                |
	+-------------------------------+
	|  FP (if required)             |
	+-------------------------------+ <-- (hard) frame_pointer_rtx
	|                               |
	|  Local variables              |
	|                               |
	+-------------------------------+
	|  outgoing stack arguments     |
	|                               |
	+-------------------------------+ <-- stack_pointer_rtx (aligned)

Dynamic stack allocations such as alloca insert data after local variables.
  
# <a name=elf-object-file></a> ELF Object Files

## <a name=file-header></a> File Header

* e_ident
  * EI_CLASS: Specifies the base ISA:
    * ELFCLASS64: ELF-64 Object File

* e_type: Nothing ARCv3 specific.

* e_machine: Identifies the machine this ELF file targets. Always contains:
  * EM_ARC_COMPACT3_64 (253) for Synopsys ARCv3 64-bit
  * EM_ARC_COMPACT3 (255) for Synopsys ARCv3 32-bit

* e_flags: Describes the format of this ELF file.  These flags are used by the
  linker to disallow linking ELF files with incompatible ABIs together.

## <a name=sections></a>Sections

## <a name=string-tables></a>String Tables

## <a name=symbol-table></a>Symbol Table

## <a name=relocations></a>Relocations

ARCv3 is a classical RISC architecture that has densely packed
non-word sized instruction immediate values. While the linker can make
relocations on arbitrary memory locations, many of the RISC-V
relocations are designed for use with specific instructions or
instruction sequences. RISC-V has several instruction specific
encodings for PC-Relative address loading, jumps, branches and the RVC
compressed instruction set.

The purpose of this section is to describe the ARCv3 specific
instruction sequences with their associated relocations in addition to
the general purpose machine word sized relocations that are used for
symbol addresses in the Global Offset Table or DWARF meta data.

The following table provides details of the ARCv3 ELF relocations
(instruction specific relocations show the instruction type in the
Details column):

Enum  | Hex | ELF Reloc Type       | Description               | Details
:---  |:--- | :------------------  | :---------------          | :-----------
0     |0x00 | R_ARC_NONE           | None                      |
1     |0x01 | R_ARC_8              | Runtime relocation        | word8 = S + A
2     |0x02 | R_ARC_16             | Runtime relocation        | word16 = S + A
3     |0x03 | R_ARC_24             | Runtime relocation        | word24 = S + A
4     |0x04 | R_ARC_32             | Runtime relocation        | word32 = S + A
5     |0x05 | R_ARC_64             | Runtime relocation        | like R_ARC_32 but 64-bit
6     |0x06 | R_ARC_B22_PCREL      | PC-relative               | disp22 = (S + A - P) >> 2
7     |0x07 | R_ARC_H30            | Runtime relocation        | word32 = (S + A) >> 2
8     |0x08 | R_ARC_N8             | Runtime relocation        | word8 = A - S
9     |0x09 | R_ARC_N16            | Runtime relocation        | word16 = A - S
10    |0x0a | R_ARC_N24            | Runtime relocation        | word24 = A - S
11    |0x0b | R_ARC_N32            | Runtime relocation        | word32 = A - S
12    |0x0c | R_ARC_SDA            | SDA relocation            | disp9 = ME ((S+A)-\_SDA\_BASE\_)
13    |0x0d | R_ARC_SECTOFF        |                           | word32 = S - SECTSTART + A
14    |0x0e | R_ARC_S21H_PCREL     | PC-relative               | disp21h = ME ((S+A-P)>>1)
15    |0x0f | R_ARC_S21W_PCREL     | PC-relative               | disp21w = ME ((S+A-P)>>2)
16    |0x10 | R_ARC_S25H_PCREL     | PC-relative               | disp25h = ME ((S+A-P)>>1)
17    |0x11 | R_ARC_S25W_PCREL     | PC-relative               | disp25w = ME ((S+A-P)>>2)
18    |0x12 | R_ARC_SDA32          | SDA relocation            | word32 = ME ((S+A)-\_SDA\_BASE\_)
19    |0x13 | R_ARC_SDA_LDST       | SDA relocation            | disp9ls = ME ((S+A)-\_SDA\_BASE\_)
20    |0x14 | R_ARC_SDA_LDST1      | SDA relocation            | disp9ls = ME (((S+A)-\_SDA\_BASE\_)>>1)
21    |0x15 | R_ARC_SDA_LDST2      | SDA relocation            | disp9ls = ME (((S+A)-\_SDA\_BASE\_)>>2)
22    |0x16 | R_ARC_SDA16_LD       | SDA relocation            | disp9s = ((S+A)-\_SDA\_BASE\_)
23    |0x17 | R_ARC_SDA_LD1        | SDA relocation            | disp9s = (((S+A)-\_SDA\_BASE\_)>>1)
24    |0x18 | R_ARC_SDA_LD2        | SDA relocation            | disp9s = (((S+A)-\_SDA\_BASE\_)>>2)
25    |0x19 | R_ARC_S13_PCREL      | PC-relative               | disp13s = ME ((S+A-P)>>2)
26    |0x1a | R_ARC_W              | Runtime relocation        | word32 = (S+A) AND (0x03)
27    |0x1b | R_ARC_32_ME          | Runtime relocation        | word32 = ME (S + A)
28    |0x1c | R_ARC_N32_ME         | Runtime relocation        | word32 = ME (A - S)
29    |0x1d | R_ARC_SECTOFF_ME     |                           | word32 = ME (S - SECTSTART + A)
30    |0x1e | R_ARC_SDA32_ME       | SDA relocation            | word32 = ME ((S+A)-\_SDA\_BASE\_)
31    |0x1f | R_ARC_W_ME           | Runtime relocation        | word32 = ME ((S+A) AND (0x03))
32    |0x20 | R_ARC_H30_ME         | Runtime relocation        | word32 = ME ((S + A) >> 2)
33    |0x21 | R_ARC_SECTOFF_U8     | Runtime relocation        | disp9 = ME (S - SECTSTART + A)
34    |0x22 | R_ARC_SECTOFF_S9     | Runtime relocation        | disp9 = ME ((S - SECTSTART + A) - 256)
35    |0x23 | R_AC_SECTOFF_U8      |                           | disp9ls = ME (S - SECTSTART + A)
36    |0x24 | R_AC_SECTOFF_U8_1    |                           | disp9ls = ME ((S - SECTSTART + A)>>1)
37    |0x25 | R_AC_SECTOFF_U8_2    |                           | disp9ls = ME ((S - SECTSTART + A)>>2)
38    |0x26 | R_AC_SECTOFF_S9      |                           | disp9ls = ME ((S - SECTSTART + A) - 256)
39    |0x27 | R_AC_SECTOFF_S9_1    |                           | disp9ls = ME ((S - SECTSTART + A - 256)>>1)
40    |0x28 | R_AC_SECTOFF_S9_2    |                           | disp9ls = ME ((S - SECTSTART + A - 256)>>2)
41    |0x29 | R_ARC_SECTOFF_ME_1   |                           | word32 = ME ((S - SECTSTART + A)>>1)
42    |0x2a | R_ARC_SECTOFF_ME_2   |                           | word32 = ME ((S - SECTSTART + A)>>2)
43    |0x2b | R_ARC_SECTOFF_1      |                           | word32 = (S - SECTSTART + A)>>1
44    |0x2c | R_ARC_SECTOFF_2      |                           | word32 = (S - SECTSTART + A)>>2
45    |0x2d | R_ARC_SDA_12         | SDA relocation            | disp12s = ME ((S+A)-\_SDA\_BASE\_)
46    |0x2e | R_ARC_LDI_SECTOFF1   | Runtime relocation        | u7 = (S - SECTSTART + A)>>1
47    |0x2f | R_ARC_LDI_SECTOFF2   | Runtime relocation        | s12 = (S - SECTSTART + A)>>2
48    |0x30 | R_ARC_SDA16_ST2      | SDA relocation            | disp9s1 = ((S+A)-\_SDA\_BASE\_)>>2
49    |0x31 | R_ARC_32_PCREL       | PC-relative (data)        | word32 = (S+A-PDATA)
50    |0x32 | R_ARC_PC32           | PC-relative               | word32 = ME (S+A-P)
51    |0x33 | R_ARC_GOTPC32        | PC-relative GOT reference | word32 = ME (GOT + G + A - P)
52    |0x34 | R_ARC_PLT32          | PC-relative (PLT)         | word32 = ME (L+A-P)
53    |0x35 | R_ARC_COPY           | Runtime relocation        | must be in executable
54    |0x36 | R_ARC_GLOB_DAT       | GOT relocation            | word32= S
55    |0x37 | R_ARC_JMP_SLOT       | Runtime relocation        | word32 = ME(S)
56    |0x38 | R_ARC_RELATIVE       | Runtime relocation        | word32 = ME(B+A)
57    |0x39 | R_ARC_GOTOFF         | GOT relocation            | word32 = ME(S+A-GOT)
58    |0x3a | R_ARC_GOTPC          | PC-relative (GOT)         | word32 = ME(GOT\_BEGIN - P)
59    |0x3b | R_ARC_GOT32          | GOT relocation            | word32 = (G + A)
60    |0x3c | R_ARC_S21W_PCREL_PLT | PC-relative (PLT)         | disp21w = ME ((L+A-P)>>2)
61    |0x3d | R_ARC_S25H_PCREL_PLT | PC-relative (PLT)         | disp25h = ME ((L+A-P)>>1)
62    |0x3e | R_ARC_SPE_SECTOFF    | Unknown                   | u11 = ((S - <start section> + A) >> 2)
63    |0x3f | R_ARC_JLI_SECTOFF    | JLI relocation            | jli = ((S-JLI)>>2)
64    |0x40 | R_ARC_AON_TOKEN_ME   | Automatic Overlay Manager |
65    |0x41 | R_ARC_AON_TOKEN      | Automatic Overlay Manager |
66    |0x42 | R_ARC_TLS_DTPMOD     | TLS relocation (dynamic)  | word32
67    |0x43 | R_ARC_TLS_DTPOFF     | TLS relocation            | word32 = ME (S - FINAL\_SECTSTART + A)
68    |0x44 | R_ARC_TLS_TPOFF      | TLS relocation (dynamic)  | word32
69    |0x45 | R_ARC_TLS_GD_GOT     | TLS relocation            | word32 = ME(G + GOT - P)
70    |0x46 | R_ARC_TLS_GD_LD      | TLS relocation            | Legacy
71    |0x47 | R_ARC_TLS_GD_CALL    | TLS relocation            | Legacy
72    |0x48 | R_ARC_TLS_IE_GOT     | TLS reloaction            | word32 = ME (G+GOT-P)
73    |0x49 | R_ARC_TLS_DTPOFF_S9  | TLS relocation            | Legacy
74    |0x4a | R_ARC_TLS_LE_S9      | TLS relocation            | Legacy
75    |0x4b | R_ARC_TLS_LE_32      | TLS relocation            | word32 = ME(S+A+TLS\_TBSS-TLS\_REL)
76    |0x4c | R_ARC_S25W_PCREL_PLT | PC-relative (PLT)         | disp25w = ME ((L+A-P)>>2)
77    |0x4d | R_ARC_S21H_PCREL_PLT | PC-relative (PLT)         | disp21h = ME ((L+A-P)>>1)
78    |0x4e | R_ARC_NPS_CMEM16     | NPS relocation            | bits16 = ME (S+A)
79    |0x4f | R_ARC_S9H_PCREL      | PC-relative               | bits9 = ME ( ( ( ( S + A ) - P ) >> 1 ) ) )
80    |0x50 | R_ARC_S7H_PCREL      | PC-relative               | bits7 = (( S + A ) - P ) >> 1
81    |0x51 | R_ARC_S8H_PCREL      | PC-relative               | disp8h = (( S + A ) - P ) >> 1
82    |0x52 | R_ARC_S10H_PCREL     | PC-relative               | bits10 = (( S + A ) - P ) >> 1
83    |0x53 | R_ARC_S13H_PCREL     | PC-relative               | bits13 = ME ( ( ( ( S + A ) - P ) >> 1 ) ) )
84    |0x54 | R_ARC_ALIGN          | Alignment statement       |
85    |0x55 | R_ARC_ADD8           | 8-bit label addition      | word8 = S + A
86    |0x56 | R_ARC_ADD16          | 16-bit label addition     | word16 = S + A
87    |0x57 | R_ARC_SUB8           | 8-bit label subtraction   | word8 = S - A
88    |0x58 | R_ARC_SUB16          | 16-bit label subtraction  | word16 = S - A
89    |0x59 | R_ARC_SUB32          | 32-bit label subtraction  | word32 = S - A
90    |0x5a | R_ARC_LO32           | Absolute address          | word32 = (S + A) & 0xffffffff
91    |0x5b | R_ARC_HI32           | Absolute address          | word32 = (S + A) >> 32
92    |0x5c | R_ARC_LO32_ME        | Absolute address          | word32 = ME ((S + A) & 0xffffffff)
93    |0x5d | R_ARC_HI32_ME        | Absolute address          | word32 = ME ((S + A) >> 32)
94    |0x5e | R_ARC_N64            | Absolute address          | word64 = *P - (S + A)
95    |0x5f | R_ARC_SDA_LDST3      | SDA relocation            | disp9ls = (S + A - \_SDA\_BASE\_) >> 3
96    |0x60 | R_ARC_NLO32          | Absolute address          | word32 = *P - ((S+A) & 0xffffffff) 
97    |0x61 | R_ARC_NLO32_ME       | Absolute address          | word32 = ME(*P - ((S+A) & 0xffffffff))
98    |0x62 | R_ARC_PCLO32_ME_2    | PC-relative address       | word32 = ME ((S + A - P ) >> 2)
99    |0x63 | R_ARC_PLT34          | PC-relative (PLT)         | word32 = ME ((L + A - P ) >> 2)
100   |0x64 | R_ARC_JLI64_SECTOFF  | JLI offset                | u10 = ((S - <start of section>) + A) >> 2 
101   |0x65 | R_ARC_S25W_PCREL_WCALL | PC-relative (weak)      | disp25w = (S + A - P) >> 2
102   |0x66 | R_ARC_S32_PCREL_ME   | PC-relative               | word32 = (S + A) - ((P-4) & ~3)
103   |0x67 | R_ARC_N32W           | Absolute address          |
104   |0x68 | R_ARC_N32W_ME        | Absolute address          |
105   |0x69 | R_ARC_NLO32W         | Absolute address          |
106   |0x6a | R_ARC_NLO32W_ME      | Absolute address          |
192-255 |     | *Reserved*         | Reserved for nonstandard ABI extensions |

* **ARCv3**: Conflicting or duplicated relocations, needs to be resolved.

Nonstandard extensions are free to use relocation numbers 192-255 for any
purpose.  These relocations may conflict with other nonstandard extensions.

### Address Calculation Symbols

The following table provides details on the variables used in address calculation:

Variable       | Description
:------------- | :----------------
A              | Addend field in the relocation entry associated with the symbol
S              | Base address of a shared object loaded into memory
GOT            | Offset of the symbol into the GOT (Global Offset Table)
S              | Value of the symbol in the symbol table


### Absolute Addresses

64-bit absolute addresses are loaded with a pair of instructions which
have an associated pair of relcations:
`R_ARC_LO32_ME` and `R_ARC_HI32_ME`.

The `R_ARC_HI32_ME` refers to `MOVHL` or `ADDHL` instructions
containing the high 32-bits fo be reloacted to an absoute symbol
address. The `movhl` instruction is followed by any 64-bit type
instruction which accepts zero extension of the 32-bits immediate
field with an `R_ARC_LO32_ME` relocation. The address of pair of
reloactions are calculated like this:

- `hi32 = (symbol_address >> 32);`
- `lo32 = (symbol_address & 0xffffffff);`

The following assemby and relocations show loading an absolute address:

```asm
   movhl_s  r0,@symbol     # R_ARC_HI32_ME (symbol)
   orl_s    r0,r0,@symbol  # R_ARC_LO32_ME (symbol)
```
or alternatively:

```asm
   movhl_s  r0,@symbol@hi     # R_ARC_HI32_ME (symbol)
   orl_s    r0,r0,@symbol@lo  # R_ARC_LO32_ME (symbol)
```

### Global Offset Table

For position independent code in dynamically linked objects, each
shared object contains a GOT (Global Offset Table) which contains
addresses of global symbols (objects and functions) referred to by the
dynamically linked shared object. The GOT in each shared library is
filled in by the dynamic linker during program loading, or on the
first call to extern functions.

To avoid runtime relocations within the text segment of position
independent code the GOT is used for indirection. Instead of code
loading virtual addresses directly, as can be done in static code,
addresses are loaded from the GOT.  The allows runtime binding to
external objects and functions at the expense of a slightly higher
runtime overhead for access to extern objects and functions.


### Program Linkage Table

The PLT (Program Linkage Table) exists to allow function calls between
dynamically linked shared objects. Each dynamic object has its own GOT
(Global Offset Table) and PLT (Program Linkage Table).

The first entry of a shared object PLT is a special entry that calls
`_dl_runtime_resolve` to resolve the GOT offset for the called
function.  The `_dl_runtime_resolve` function in the dynamic loader
resolves the GOT offsets lazily on the first call to any function,
except when `LD_BIND_NOW` is set in which case the GOT entries are
populated by the dynamic linker before the executable is started. Lazy
resolution of GOT entries is intended to speed up program loading by
deferring symbol resolution to the first time the function is
called. The first entry in the PLT is:

```
1:   ld     r11,[pcl, _DYNAMIC@GOTPC+4]
     ld     r10,[pcl, _DYNAMIC@GOTPC+8]
     j      [r10]
```

Subsequent function entry stubs in the PLT load a function pointer
from the GOT. On the first call to a function, the entry redirects to
the first PLT entry which calls `_dl_runtime_resolve` and fills in the
GOT entry for subsequent calls to the function:

```
1:   ld     r12,[pcl,func@gotpc]
     j.d    [r12]
     mov    r12,pcl
```


### Procedure Calls


### PC-Relative Jumps and Branches


### PC-Relative Symbol Addresses

64-bit PC-relative relocations for symbol for symbol addresses on
sequences of instructions such as the `ADDHL+ADDL` instruction pair,
and have an associated pair of relocations: `R_ARC_PCREL_HI32_ME` plus
`R_ARC_PCREL_LO323_ME` relocations.

The `R_ARC_PCREL_HI32_ME` relocation referes to an `ADDHL` instruction
containing the high 32-bits to be relocated to a symbol relative to
the program counter address of the `ADDHL` instruction. This
instruction is followed by any instruction working on 64-bit datum and
sign-extending the 32-bit immediate field such as `ADDL` instruction
with an `R_ARC_PCREL_LO32_ME` relocation.

The `R_ARC_PCREL_LO32_ME` relocation needs to resolve the lower 32-bit
of the symbol relative to the program counter address of the `ADDHL`
instruction which holds the higher 32-bits. Resolving the lower part
needs to know the relative offset between the `ADDL` instruction and
`ADDHL` instruction which will be used for correcting the lower
value. The addresses for pair of relocations are calculated like this:

- `hi32 = (symbol_address - PCL) >> 32 + ((symbol_address - PCL) >> 31 & 1);`
- `lo32 = (symbol_address + hi32_off - PCL) & 0xffffffff;`
- `hi32_off = lo32_reloc_address - hi32_reloc_address;`

Here is an example assembler showing the relocation types:

```asm
label:
   addhl_s r0,PCL,@symbol@pcl              # R_ARC_PCREL_HI32 (symbol)
   ...
   addl_s r0,r0,@symbol@pcl + (. - @label) # R_ARC_PCREL_LO32 (symbol)
```

For the case when the linker relaxation is in place the
`R_ARC_PCREL_OFFSET` relocation to go in pair with `R_ARC_PCREL_LO32`
reloc to resolve `hi32_off` at link-time:

- `hi32_off = (@label_address & -3 + 2) - PCL;`

Here is an example assembler showing the all three relocation types:

```asm
label:
   addhl_s r0,PCL,@symbol@pcl            # R_ARC_PCREL_HI32 (symbol)
   ...
   addl_s r0,r0,@symbol@pcl - @label@off # R_ARC_PCREL_LO32 (symbol)
                                         # R_ARC_PCREL_OFFSET (label)
```

## <a name=thread-local-storage></a>Thread Local Storage

ARCv3 adopts the ELF Thread Local Storage Model in which ELF objects
define `.tbss` and `.tdata` sections and `PT_TLS` program headers that
contain the TLS "initialization images" for new threads. The `.tbss`
and `.tdata` sections are not referenced directly like regular
segments, rather they are copied or allocated to the thread local
storage space of newly created threads.  See
[https://www.akkadia.org/drepper/tls.pdf](https://www.akkadia.org/drepper/tls.pdf).

In The ELF Thread Local Storage Model, TLS offsets are used instead of
pointers.  The ELF TLS sections are initialization images for the
thread local variables of each new thread. A TLS offset defines an
offset into the dynamic thread vector which is pointed to by the TCB
(Thread Control Block) held in the `gp` register.

There are various thread local storage models for statically allocated
or dynamically allocated thread local storage. The following table
lists the thread local storage models:

Mnemonic | Model          | Compiler flags
:------- | :---------     | :-------------------
TLS LE   | Local Exec     | `-ftls-model=local-exec`
TLS IE   | Initial Exec   | `-ftls-model=initial-exec`
TLS LD   | Local Dynamic  | `-ftls-model=local-dynamic`
TLS GD   | Global Dynamic | `-ftls-model=global-dynamic`

The program linker in the case of static TLS or the dynamic linker in
the case of dynamic TLS allocate TLS offsets for storage of thread
local variables.


### Local Exec

Local exec is a form of static thread local storage. This model is
used when static linking as the TLS offsets are resolved during
program linking.

- Compiler flag `-ftls-model=local-exec`
- Variable attribute: `__thread int i __attribute__((tls_model("local-exec")));`


### Initial Exec

Initial exec is is a form of static thread local storage that can be
used in shared libraries that use thread local storage. TLS
relocations are performed at load time. `dlopen` calls to libraries
that use thread local storage may fail when using the initial exec
thread local storage model as TLS offsets must all be resolved at load
time. This model uses the GOT to resolve TLS offsets.

- Compiler flag `-ftls-model=initial-exec`
- Variable attribute: `__thread int i __attribute__((tls_model("initial-exec")));`

### Global Dynamic

ARCv3 local dynamic and global dynamic TLS models generate equivalent
object code.  The Global dynamic thread local storage model is used
for PIC Shared libraries and handles the case where more than one
library uses thread local variables, and additionally allows libraries
to be loaded and unloaded at runtime using `dlopen`.  In the global
dynamic model, application code calls the dynamic linker function
`__tls_get_addr` to locate TLS offsets into the dynamic thread vector
at runtime.

- Compiler flag `-ftls-model=global-dynamic`
- Variable attribute: `__thread int i __attribute__((tls_model("global-dynamic")));`

Example assembler load and store of a thread local variable `i` using the
`la.tls.gd` pseudoinstruction, with the emitted TLS relocations in comments:

In the Global Dynamic model, the runtime library provides the `__tls_get_addr` function:

```
extern void *__tls_get_addr (tls_index *ti);
```

where the type tls index are defined as:

```
typedef struct
{
  unsigned long int ti_module;
  unsigned long int ti_offset;
} tls_index;
```

## <a name=program-header-table></a>Program Header Table

## <a name=note-sections></a>Note Sections

## <a name=dynamic-table></a>Dynamic Table

## <a name=hash-table></a>Hash Table

# <a name=dwarf></a>DWARF

Dwarf Register Numbers <a name=dwarf-register-numbers>
-------------------------------------------------------------------------
Dwarf Number  | Register Name | Description
--------------|---------------|-----------------------------------------
