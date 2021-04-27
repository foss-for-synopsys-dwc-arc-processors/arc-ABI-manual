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

<!-- below from MWDT //dwarc/TechPubs/UserDocs/Source/4091_ARCv3_ABI/RST/source/low_lvl.rst#17 -->

 Low-Level System Information {#low_lvl}
============================

Processor Architecture
----------------------

Programs intended to execute on ARCv3-based processors use the ARCv3
instruction set and the instruction encoding and semantics of the
architecture.

Assume that all instructions defined by the architecture are neither
privileged nor exist optionally and work as documented.

To conform to ARCv3 System V ABI, the processor must do the following:

> -   implement the instructions of the architecture,
> -   perform the specified operations,
> -   produce the expected results.

The ABI neither places performance constraints on systems nor specifies
what instructions must be implemented in hardware. A software emulation
of the architecture can conform to the ABI.

::: {.caution}
::: {.admonition-title}
Caution
:::

Some processors might support optional or additional instructions or
capabilities that do not conform to the ARCv3 ABI. Executing programs
that use such instructions or capabilities on hardware that does not
have the required additional capabilities results in undefined behavior.
:::

Data Representation
-------------------

### Byte Ordering

The architecture defines an eight-bit byte, a 16-bit halfword, a 32-bit
word, and a 64-bit double word. Byte ordering defines how the bytes that
make up halfwords, words, and doublewords are ordered in memory.

Most-significant-byte (MSB) ordering, also called as "big-endian", means
that the most-significant byte is located in the lowest addressed byte
position in a storage unit (byte 0).

Least-significant-byte (LSB) ordering, also called as "little-endian",
means that the least-significant byte is located in the lowest addressed
byte position in a storage unit (byte 0).

ARCv3-based processors support either big-endian or little-endian byte
ordering. However, this specification defines only the base-case
little-endian (LSB) architecture.

`bit_byte_num_hw`{.interpreted-text role="numref"} through
`bit_byte_num_dw`{.interpreted-text role="numref"} illustrate the
conventions for bit and byte numbering within storage units of varying
width. These conventions apply to both integer data and floating-point
data, where the most-significant byte of a floating-point value holds
the sign and at least the start of the exponent. The figures show byte
numbers in the upper right corners, and bit numbers in the lower
corners.

> Bit and Byte Numbering in Halfwords

### Data Layout in Memory

ARCv3-based processors access data memory using byte addresses and
generally require that all memory addresses be aligned as follows:

-   64-bit double-words are aligned to
    -   64-bit boundaries on ARC64.
    -   32-bit boundaries on ARC32.
-   32-bit words are aligned to 32-bit word boundaries.
-   16-bit halfwords are aligned to 16-bit halfword boundaries.

Bytes have no specific alignment.

#### Sixty-Four-Bit Data

`64b_reg_LE`{.interpreted-text role="numref"} shows the little-endian
representation in byte-wide memory. If the ARCv3-based processor
supports big-endian addressing, the data is stored in memory as shown in
`64b_reg_BE`{.interpreted-text role="numref"}.

> Sixty-Four-Bit Register Data in Byte-Wide Memory, Little-Endian

#### Thirty-Two-Bit Data

`reg_32b`{.interpreted-text role="numref"} shows the data representation
in a general purpose register.

> Register Containing Thirty-Two-Bit Data

`32b_LE`{.interpreted-text role="numref"} shows the little-endian
representation in byte-wide memory.

> Thirty-Two-Bit Register Data in Byte-Wide Memory, Little-Endian

`32b_BE`{.interpreted-text role="numref"} shows the big-endian
representation.

> Thirty-Two-Bit Register Data in Byte-Wide Memory, Big-Endian

#### Sixteen-Bit Data

`reg_16b`{.interpreted-text role="numref"} shows the 16-bit data
representation in a general purpose register.

For the programmer\'s model, the data is always contained in the lower
bits of the core register and the data memory is accessed using a byte
address. This model is sometimes referred to as a data invariance
principle.

> Register Containing Sixteen-Bit Data

`16b_LE`{.interpreted-text role="numref"} shows the little-endian
representation of 16-bit data in byte-wide memory.

> Sixteen-Bit Register Data in Byte-Wide Memory, Little-Endian

`16b_BE`{.interpreted-text role="numref"} shows the big-endian
representation.

> Sixteen-Bit Register Data in Byte-Wide Memory, Big-Endian

#### Eight-Bit Data

`reg_8b`{.interpreted-text role="numref"} shows the 8-bit data
representation in a general purpose register. For the programmer\'s
model, the data is always contained in the lower bits of the core
register and the data memory is accessed using a byte address. This
model is sometimes referred to as a data invariance principle.

> Register Containing Eight-Bit Data

`8b_bw`{.interpreted-text role="numref"} shows the representation of
8-bit data in byte-wide memory. Regardless of the endianness of the
ARCv3-based system, the byte-aligned address, n, of the byte is
explicitly given and the byte is stored or read from that explicit
address.

> Eight-Bit Register Data in Byte-Wide Memory

#### One-Bit Data

The ARCv3 instruction-set architecture supports single-bit operations on
data stored in the core registers. A bit manipulation instruction
includes an immediate value specifying the bit to operate on. Bit
manipulation instructions can operate on 8-bit, 16-bit, or 32-bit data
located within core registers because each bit is individually
addressable.

![Register Containing One-Bit Data](../images/Reg_1b.png){.align-center}

### Fundamental Types

`t_sc_types32`{.interpreted-text role="numref"} and
`t_sc_types64`{.interpreted-text role="numref"} show how ANSI C scalar
types correspond to those of ARCv3-based 32 and 64-bit processors. For
all types, a null pointer in the default address region has the value
zero. The **Alignment** column specifies the required alignment of a
field of the given type within a struct. Fields in a struct must follow
the alignment specified to ensure consistent struct mapping.

> +---------+-------------------+------+---------+--------------------+
> | |       | |                 | |    | |       | |                  |
> |         |                   |      |         |                    |
> | **Type* | **ANSI C**        | **Si | **Align | **ARCv3 ARC32      |
> | *       |                   | ze** | ment**  | processors**       |
> |         |                   |      | (bytes) |                    |
> +=========+===================+======+=========+====================+
> | Integra | | `char`          | > 1  | > 1     | > `unsigned byte`  |
> | l       | | `unsigned char` |      |         |                    |
> |         |                   | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> | > -   - | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |    -    | -\-\-\-\-\-\-\-\- | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> | -   -   | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- | \-\-\--+           |
> |  -   -  | -\-\--+           | \--+ | -+      |                    |
> |         |                   |      |         | :   `signed byte`  |
> |         | :   `signed char` | :    | :   1   |                    |
> |         |                   | 1    |         | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ |      | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | -\-\-\-\-\-\-\-\- | \-\- | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | \-\-\-\ | \-\-\--+           |
> |         | -\-\--+           | \-\- | -\-\-\- |                    |
> |         | \| `short` \|     | \-\- | -+      | :   `signed halfwo |
> |         | `signed short`    | \--+ |         | rd`                |
> |         | \-\-\-\-\-\-\-\-\ |      | :   2   |                    |
> |         | -\-\-\-\-\-\-\-\- | :    |         | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ | 2    | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | -\-\--+           |      | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         | `unsigned short`  | \-\- | \-\-\-\ | \-\-\--+           |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- |                    |
> |         | -\-\-\-\-\-\-\-\- | \-\- | -+      | :   `unsigned half |
> |         | \-\-\-\-\-\-\-\-\ | \-\- |         | word`              |
> |         | -\-\--+           | \--+ | :   2   |                    |
> |         | \| `int` \|       |      |         | \-\-\-\-\-\-\-\-\- |
> |         | `signed int` \|   | :    | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | `long` \|         | 2    | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         | `signed long`     |      | \-\-\-\ | \-\-\--+           |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- |                    |
> |         | -\-\-\-\-\-\-\-\- | \-\- | -+      | :   `signed word`  |
> |         | \-\-\-\-\-\-\-\-\ | \-\- |         |                    |
> |         | -\-\--+           | \-\- | :   4   | \-\-\-\-\-\-\-\-\- |
> |         | \| `unsigned int` | \--+ |         | \-\-\-\-\-\-\-\-\- |
> |         | \|                |      | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | `unsigned long`   | :    | -\-\-\- | \-\-\--+           |
> |         | \-\-\-\-\-\-\-\-\ | 4    | \-\-\-\ |                    |
> |         | -\-\-\-\-\-\-\-\- |      | -\-\-\- | :   `unsigned word |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | -+      | `                  |
> |         | -\-\--+           | \-\- |         |                    |
> |         | \| `long long` \| | \-\- | :   4   | \-\-\-\-\-\-\-\-\- |
> |         | `signed long long | \-\- |         | \-\-\-\-\-\-\-\-\- |
> |         | `                 | \--+ | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ |      | -\-\-\- | \-\-\--+           |
> |         | -\-\-\-\-\-\-\-\- | :    | \-\-\-\ |                    |
> |         | \-\-\-\-\-\-\-\-\ | 4    | -\-\-\- | :   `signed double |
> |         | -\-\--+           |      | -+      | word`              |
> |         | \|                | \-\- |         |                    |
> |         | `unsigned long lo | \-\- | :   4   | \-\-\-\-\-\-\-\-\- |
> |         | ng`               | \-\- |         | \-\-\-\-\-\-\-\-\- |
> |         |                   | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         |                   | \--+ | -\-\-\- | \-\-\--+           |
> |         |                   |      | \-\-\-\ |                    |
> |         |                   | :    | -\-\-\- | :   `unsigned doub |
> |         |                   | 8    | -+      | leword`            |
> |         |                   |      |         |                    |
> |         |                   | \-\- | :   4   |                    |
> |         |                   | \-\- |         |                    |
> |         |                   | \-\- |         |                    |
> |         |                   | \-\- |         |                    |
> |         |                   | \--+ |         |                    |
> |         |                   |      |         |                    |
> |         |                   | :    |         |                    |
> |         |                   | 8    |         |                    |
> +---------+-------------------+------+---------+--------------------+
> | Pointer | | `any *`         | > 4  | > 4     | `unsigned word`    |
> |         | | `any (*) *`     |      |         |                    |
> +---------+-------------------+------+---------+--------------------+
> | Floatin | > `__fp16`        | > 2  | > 2     | > `half precision` |
> | g       |                   |      |         |                    |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> | :   -   | -\-\-\-\-\-\-\-\- | \-\- | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |  -      | \-\-\-\-\-\-\-\-\ | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | -\-\--+           | \-\- | -\-\-\- | \-\-\--+           |
> |         |                   | \--+ | -+      |                    |
> |         | :   `float`       |      |         | :   `single precis |
> |         |                   | :    | :   4   | ion`               |
> |         | \-\-\-\-\-\-\-\-\ | 4    |         |                    |
> |         | -\-\-\-\-\-\-\-\- |      | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         | -\-\--+           | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | \| `double` \|    | \-\- | -\-\-\- | \-\-\--+           |
> |         | `long double`     | \-\- | -+      |                    |
> |         |                   | \--+ |         | :   `double precis |
> |         |                   |      | :   4   | ion`               |
> |         |                   | :    |         |                    |
> |         |                   | 8    |         |                    |
> +---------+-------------------+------+---------+--------------------+
>
> +---------+-------------------+------+---------+--------------------+
> | |       | |                 | |    | |       | |                  |
> |         |                   |      |         |                    |
> | **Type* | **ANSI C**        | **Si | **Align | **ARCv3 ARC64      |
> | *       |                   | ze** | ment**  | processors**       |
> |         |                   |      | (bytes) |                    |
> +=========+===================+======+=========+====================+
> | Integra | | `char`          | > 1  | > 1     | > `unsigned byte`  |
> | l       | | `unsigned char` |      |         |                    |
> |         |                   | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> | > -   - | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |    -    | -\-\-\-\-\-\-\-\- | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> | -   -   | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- | \-\-\--+           |
> |  -   -  | -\-\--+           | \--+ | -+      |                    |
> |   -   - |                   |      |         | :   `signed byte`  |
> |         | :   `signed char` | :    | :   1   |                    |
> |         |                   | 1    |         | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ |      | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | -\-\-\-\-\-\-\-\- | \-\- | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | \-\-\-\ | \-\-\--+           |
> |         | -\-\--+           | \-\- | -\-\-\- |                    |
> |         | \| `short` \|     | \-\- | -+      | :   `signed halfwo |
> |         | `signed short`    | \--+ |         | rd`                |
> |         | \-\-\-\-\-\-\-\-\ |      | :   2   |                    |
> |         | -\-\-\-\-\-\-\-\- | :    |         | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ | 2    | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | -\-\--+           |      | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         | `unsigned short`  | \-\- | \-\-\-\ | \-\-\--+           |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- |                    |
> |         | -\-\-\-\-\-\-\-\- | \-\- | -+      | :   `unsigned half |
> |         | \-\-\-\-\-\-\-\-\ | \-\- |         | word`              |
> |         | -\-\--+           | \--+ | :   2   |                    |
> |         | \| `int` \|       |      |         | \-\-\-\-\-\-\-\-\- |
> |         | `signed int`      | :    | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ | 2    | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         | -\-\-\-\-\-\-\-\- |      | \-\-\-\ | \-\-\--+           |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- |                    |
> |         | -\-\--+           | \-\- | -+      | :   `signed word`  |
> |         | \| `unsigned int` | \-\- |         |                    |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | :   4   | \-\-\-\-\-\-\-\-\- |
> |         | -\-\-\-\-\-\-\-\- | \--+ |         | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ |      | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | -\-\--+           | :    | -\-\-\- | \-\-\--+           |
> |         | \| `long` \|      | 4    | \-\-\-\ |                    |
> |         | `signed long`     |      | -\-\-\- | :   `unsigned word |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | -+      | `                  |
> |         | -\-\-\-\-\-\-\-\- | \-\- |         |                    |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | :   4   | \-\-\-\-\-\-\-\-\- |
> |         | -\-\--+           | \-\- |         | \-\-\-\-\-\-\-\-\- |
> |         | \|                | \--+ | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | `unsigned long`   |      | -\-\-\- | \-\-\--+           |
> |         | \-\-\-\-\-\-\-\-\ | :    | \-\-\-\ |                    |
> |         | -\-\-\-\-\-\-\-\- | 4    | -\-\-\- | :   `signed double |
> |         | \-\-\-\-\-\-\-\-\ |      | -+      | word`              |
> |         | -\-\--+           | \-\- |         |                    |
> |         | \| `long long` \| | \-\- | :   8   | \-\-\-\-\-\-\-\-\- |
> |         | `signed long long | \-\- |         | \-\-\-\-\-\-\-\-\- |
> |         | `                 | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ | \--+ | -\-\-\- | \-\-\--+           |
> |         | -\-\-\-\-\-\-\-\- |      | \-\-\-\ |                    |
> |         | \-\-\-\-\-\-\-\-\ | :    | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         | -\-\--+           | 8    | -+      | \-\-\-\-\-\-\-\-\- |
> |         | \|                |      |         | \-\-\-\-\-\-\-\-\- |
> |         | `unsigned long lo | \-\- | :   8   | \-\-\--+           |
> |         | ng`               | \-\- |         |                    |
> |         |                   | \-\- | \-\-\-\ | :   `signed double |
> |         |                   | \-\- | -\-\-\- | word`              |
> |         |                   | \--+ | \-\-\-\ |                    |
> |         |                   |      | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         |                   | :    | -+      | \-\-\-\-\-\-\-\-\- |
> |         |                   | 8    |         | \-\-\-\-\-\-\-\-\- |
> |         |                   |      | :   8   | \-\-\--+           |
> |         |                   | \-\- |         |                    |
> |         |                   | \-\- | \-\-\-\ | :   `unsigned doub |
> |         |                   | \-\- | -\-\-\- | leword`            |
> |         |                   | \-\- | \-\-\-\ |                    |
> |         |                   | \--+ | -\-\-\- |                    |
> |         |                   |      | -+      |                    |
> |         |                   | :    |         |                    |
> |         |                   | 8    | :   8   |                    |
> |         |                   |      |         |                    |
> |         |                   | \-\- |         |                    |
> |         |                   | \-\- |         |                    |
> |         |                   | \-\- |         |                    |
> |         |                   | \-\- |         |                    |
> |         |                   | \--+ |         |                    |
> |         |                   |      |         |                    |
> |         |                   | :    |         |                    |
> |         |                   | 8    |         |                    |
> +---------+-------------------+------+---------+--------------------+
> | Pointer | | `any *`         | > 8  | > 8     | `unsigned doublewo |
> |         | | `any (*) *`     |      |         | rd`                |
> +---------+-------------------+------+---------+--------------------+
> | Floatin | > :code:\`\_\_fp1 | > 2  | > 2     | > `half precision` |
> | g       | 6                 |      |         |                    |
> |         |                   | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> | :   -   | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |  -      | -\-\-\-\-\-\-\-\- | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | -\-\-\- | \-\-\--+           |
> |         | -\-\--+           | \--+ | -+      |                    |
> |         |                   |      |         | :   `single precis |
> |         | :   `float`       | :    | :   4   | ion`               |
> |         |                   | 4    |         |                    |
> |         | \-\-\-\-\-\-\-\-\ |      | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | -\-\-\-\-\-\-\-\- | \-\- | -\-\-\- | \-\-\-\-\-\-\-\-\- |
> |         | \-\-\-\-\-\-\-\-\ | \-\- | \-\-\-\ | \-\-\-\-\-\-\-\-\- |
> |         | -\-\--+           | \-\- | -\-\-\- | \-\-\--+           |
> |         | \| `double` \|    | \-\- | -+      |                    |
> |         | `long double`     | \--+ |         | :   `double precis |
> |         |                   |      | :   8   | ion`               |
> |         |                   | :    |         |                    |
> |         |                   | 8    |         |                    |
> +---------+-------------------+------+---------+--------------------+
>
### Enumerations

The enum data type mapping is similar to that of an integer of
equivalent size. Signed integral types are used by default.

### Complex Types

Complex data types may be passed by value in registers or by reference
as a large struct depending on the configuration of your processor.

For example, a 32-bit processor without an FPU must pass 16 bytes for a
\"double \_Complex\". This requires four core registers, too many to be
efficient. It is preferable for such a configuration to pass a \"double
\_Complex\" by reference. The same \"double \_Complex\" value can be
passed in two floating-point registers on a processor configured with a
double-precision floating-point unit.

Complex types have the same alignment as a struct, with two fields of
the appropriate type. The alignment can then be computed using tables
`t_sc_types32`{.interpreted-text role="numref"} and
`t_sc_types64`{.interpreted-text role="numref"} and section
`_t_sc_aggregates`{.interpreted-text role="numref"}.

### Aggregates and Unions

Aggregates (structures, classes, and arrays) and unions assume the
alignment of their most strictly aligned component, that is, the
component with the largest alignment. The size of any object, including
aggregates, classes, and unions, is always a multiple of the alignment
of the object. Non-bitfield members always start on byte boundaries. The
size of a struct or class is the sum of the sizes of its members,
including alignment padding between members. The size of a union is the
size of its largest member, padded such that its size is evenly
divisible by its alignment. Enumerations can be mapped to one, two, or
four bytes, depending on their size. An array uses the same alignment as
its elements. Structure and union objects can be packed or padded to
meet size and alignment constraints:

-   An entire structure or union object is aligned on the same boundary
    as its most strictly aligned member, though a packed structure or
    union need not be aligned on word boundaries.
-   Each member is assigned to the lowest available offset with the
    appropriate alignment. Such alignment might require internal
    padding, depending on the previous member.
-   If necessary, a structure's size is increased to make it a multiple
    of the structure\'s alignment. Such alignment might require tail
    padding, depending on the last member.

For detailed information on C++ classes, see "Storage Mapping for Class
Objects " see `stormap`{.interpreted-text role="ref"}

In the following examples, members' byte offsets appear in the upper
right corners.

Structure smaller than a word:

``` {.c}
struct {
  char c;
};
```

![Byte-Aligned, Sizeof is
1](../images/struct_smaller_word.png){.align-center}

No Padding:

``` {.c}
struct {
  char  c;
  char  d;
  short s;
  int   n;
};   
```

![Word-Aligned, Sizeof is 8](../images/no_padding.png){.align-center}

Internal Padding:

``` {.c}
struct {
  char  c;
  short s;
};  
```

![Halfword-Aligned, Sizeof is
4](../images/int_padding.png){.align-center}

Internal and Tail Padding:

``` {.c}
struct {
  char   c;
  double d;
  short  s;
};   
```

![Word-Aligned (ARC32) or Double-Word-Aligned (ARC64), Sizeof is
16](../images/int_tail_padding.png){.align-center}

Union Allocation:

``` {.c}
union {
  char  c;
  short s;
  int   j;
};
```

![Word-Aligned, Sizeof is 4](../images/union_alloc.png){.align-center}

Storage Mapping for Class Objects {#stormap}
---------------------------------

C++ class objects must be mapped in accordance with the GNU Itanium ABI;
see the following URL:
<http://mentorembedded.github.io/cxx-abi/abi.html>

Bitfields
---------

C/C++ struct and union definitions can have bitfields, defining integral
objects with a specified number of bits.

Bitfields are signed unless explicitly declared as unsigned. For
example, a four-bit field declared as int can hold values from -8 to 7.

`bitfield_types`{.interpreted-text role="numref"} shows the possible
widths for bitfields, where w is maximum width (in bits).

>   ---------------------------------------------------------------------------
>   **Bit Field Type**         **Max Width**       **Range of Values**
>                              [w]{.title-ref}     
>                              **(Bits)**          
>   -------------------------- ------------------- ----------------------------
>   `signed char`              1 to 8              :math:[2\^{(w-1)} -
>                                                  1]{.title-ref} to
>                                                  $-2^{(w-1)}$
>
>   `char` (default            1 to 8              0 to $2^w - 1$
>   signedness)                                    
>
>   `unsigned char`            1 to 8              0 to $2^w - 1$
>
>   `short`                    1 to 16             $-2^{(w-1)}$ to
>                                                  $2^{(w-1)} - 1$
>
>   `unsigned short`           1 to 16             0 to $2^w - 1$
>
>   `int`                      1 to 32             $-2^{(w-1)}$ to
>                                                  $2^{(w-1)} - 1$
>
>   `long`                     1 to 32 ARC32 or 64 $-2^{(w-1)}$ to
>                              ARC64               $2^{(w-1)} - 1$
>
>   `enum` (unless signed      1 to 32             0 to $2^w - 1$
>   values are assigned)                           
>
>   `unsigned int`             1 to 32             0 to $2^w - 1$
>
>   `unsigned long`            1 to 32 ARC32 or 64 0 to $2^w - 1$
>                              ARC64               
>
>   `long long int`            1 to 64             $-2^{(w-1)}$ to
>                                                  $2^{(w-1)} - 1$
>
>   `unsigned long long int`   1 to 64             0 to $2^w - 1$
>   ---------------------------------------------------------------------------
>
Bitfields obey the same size and alignment rules as other structure and
union members, with the following additions:

-   Bitfields are allocated from most to least significant bit on
    big-endian implementations.

-   Bitfields are allocated from least to most significant bit on
    little-endian implementations.

-   The alignment that a bit field imposes on its enclosing struct or
    union is the same as any ordinary (non-bit) field of the same type.
    Thus, a bitfield of type int imposes a four-byte alignment on the
    enclosing struct.

-   Bitfields are packed in consecutive bytes, except if a bitfield
    packed in consecutive bytes crosses a byte offset *B* where
    `B % sizeof(FieldType) == 0`.

    In particular:

    -   A bitfield of type `char` must not cross a byte boundary.
    -   A bitfield of type `short` must not cross a halfword boundary.
    -   A bit field of type `int` must not cross a word boundary.
    -   Because long long ints are four-byte-aligned on ARCv3-based
        processors, a bitfield of type `long 
        long` must not cross two word boundaries. Thus, field B in the
        following code starts on byte 4 of the parent struct: :code:
        [struct S { int A:8; long long B:60; }]{.title-ref}

You can insert padding as needed to comply with these rules.

Unnamed bitfields of non-zero length do not affect the external
alignment. In all other respects, they behave the same as named
bitfields. An unnamed bitfield of zero length causes alignment to occur
at the next unit boundary, based on its type.

The struct in the following example can be mapped as illustrated in or
`struct_LE`{.interpreted-text role="numref"}.

``` {.c}
struct {
   unsigned x:11, y:9, :0, w:13, z:1;
   char  c;
   short i;
   }
```

The [struct]{.title-ref} in `struct_LE`{.interpreted-text role="numref"}
is aligned on address boundaries divisible by four because it contains
`int` types. Note that the unnamed bitfield (:0) forces padding, while
alignment rules sometimes pad.

If w is changed to a [char]{.title-ref} type, it is still forced to
begin in byte four. If no unnamed bitfield is present in this example, w
begins in byte two, three, or four, depending on whether it fits in the
space remaining without crossing its storage-unit boundary (which is
four).

The following examples show the byte offsets of [struct]{.title-ref} and
[union]{.title-ref} members in the upper right corners for little-endian
implementations. Bit numbers appear in the lower corners.

Bit numbering of `0x01020304`:

![Bit Numbering](../images/bit_numbering.png){.align-center}

Bit-Field Allocation:

``` {.c}
struct {
  int j : 5;
  int k : 6;
  int m : 7;
};
```

![Word-Aligned, Sizeof is
4](../images/bitfield_alloc.png){.align-center}

Boundary Alignment:

``` {.c}
struct {
  short s : 9;
  int   j : 9;
  char  c;
  short t : 9;
  short u : 9;
  char  d;
};
```

![Word-Aligned, Sizeof is
12](../images/boundary_align.png){.align-center}

Storage Unit Sharing:

``` {.c}
struct {
  char  c;
  short s : 8;
};
```

![Halfword-Aligned, Sizeof is
2](../images/st_unit_share.png){.align-center}

Union Allocation:

``` {.c}
union {
  char  c;
  short s : 8;
};
```

![Halfword-Aligned, Sizeof is
2](../images/union_alloc2.png){.align-center}

Unnamed Bitfields:

``` {.c}
struct {
  char  c;
  int   : 0;
  char  d;
  short : 9;
  char  e;
};
```

![Byte-Aligned, Sizeof is
9](../images/unnamed_bitfields.png){.align-center}

::: {.note}
::: {.admonition-title}
Note
:::

In this example, the presence of the unnamed int and short fields does
not affect the alignment of the structure. They align the named members
relative to the beginning of the structure, but the named members might
not be aligned in memory on suitable boundaries. For example, the d
members in an array of these structures are not all on an int
(four-byte) boundary. Because there is no named field with any alignment
requirements beyond a byte, the struct is nine bytes wide, one-byte
aligned.
:::

##### Function Calling Sequence

This section discusses the standard function calling sequence, including
stack-frame layout, register usage, and argument passing.

Programs must follow the conventions given here. For examples of
approaches permissible within these conventions, see
`coding_ex`{.interpreted-text role="ref"}.

Registers {#regs}
---------

The base-case processor hardware provides 32 word-sized (32-bit)
registers and a number of special-purpose auxiliary registers. Auxiliary
registers are used only by the LR and SR assembly instructions.

### Core Registers

`t_gen_pc_reg`{.interpreted-text role="numref"} and
`t_aux_reg`{.interpreted-text role="numref"} summarize the registers and
their functions in a standard processor build. If a reduced register set
is specified, only four words of arguments are passed in registers: r0
through r3. In addition, registers r4-r9 and r16-r25 are not available
with the reduced register set.

::: {.note}
::: {.admonition-title}
Note
:::

Alternatively, a compiler can be configured to pass 64-bit arguments in
even/odd register pairs on ARC32 or a single core register on ARC64. In
the example F(int a, long long b); argument a can be passed in r0, and
argument b can be passed in r2 and r3 on ARC32. Note that r1 is skipped
so that the 64-bit value can reside in an even/odd pair if preceded by a
single 32-bit word. On ARC64 they are simply passed in r0 and r1.

Code generated with such an argument-passing mechanism is not compatible
with code emitted using the mechanism described in
`t_gen_pc_reg`{.interpreted-text role="numref"}. See your compiler
documentation for compatibility options.
:::

::: {#t_gen_pc_reg}
  --------------------------------------------------------------------------------------------------------------------------------------
  **Register**         **Primary Function**                                **Secondary Function**
  -------------------- --------------------------------------------------- -------------------------------------------------------------
  r0                   Integer result, Argument 1                          Caller-saved scratch register

  r1                   Argument 2                                          Caller-saved scratch register

  r2                   Argument 3                                          Caller-saved scratch register

  r3                   Argument 4                                          Caller-saved scratch register

  r4                   Argument 5                                          Caller-saved scratch register

  r5                   Argument 6                                          Caller-saved scratch register

  r6                   Argument 7                                          Caller-saved scratch register

  r7                   Argument 8                                          Caller-saved scratch register

  r8 -- r13            Caller-saved scratch register                       r13 *CHANGED* for ARCv3

  r14 -- r26           Callee-saved register variable                      r26 *CHANGED* for ARCv3

  r27                  Frame pointer (fp) Callee-saved register variable   Used for stack relative addressing instead of (sp) when
                                                                           needed or requested

  r28                  Stack top pointer (sp)                              ---

  r29                  Interrupt link register                             ---

  r30                  Small-data base register (gp)                       r30 *CHANGED* for ARCv3

  r31                  Branch link register (blink)                        ---

  r58                  Accumulator Low ACCL (little endian), ACCH          Caller-saved scratch register
                       (big-endian)                                        

  r59                  Accumulator High ACCH (little endian), ACCL         Caller-saved scratch register
                       (big-endian)                                        

  r60                  Loop counter (lp\_count)                            Caller-saved scratch register (compilers only - not user
                                                                           code)

  r61                  Long signed immediate data indicator                ARC64 only

  r62                  Long immediate data indicator                       ---

  r63                  program-counter value (pcl)                         ---
  --------------------------------------------------------------------------------------------------------------------------------------

  : General and Program-Counter Register Functions
:::

The pcl register (r63) contains the four-byte-aligned value of the
program counter.

The lp\_count register (r60) is the 32-bit loop-counter register. It is
not preserved across function calls, but you can change this behavior by
including it in the registers specified with option
`-Hirq_ctrl_saved="regs"` or pragma `irq_ctrl_saved("regs")`.

::: {.note}
::: {.admonition-title}
Note
:::

The scratch registers are not preserved across function calls. When
calling an external function, the compiler assumes that registers r0
through r13 are trashed; and that or r14 through r30 are preserved. The
EV processors reserve r25.
:::

### FPU Registers

  --------------------------------------------------------------------------------------------------------------------------------------
  **Register**         **Primary Function**                                **Secondary Function**
  -------------------- --------------------------------------------------- -------------------------------------------------------------
  f0                   Floating-point result, Argument 1                   Caller-saved scratch register

  f1                   Argument 2                                          Caller-saved scratch register

  f2                   Argument 3                                          Caller-saved scratch register

  f3                   Argument 4                                          Caller-saved scratch register

  f4                   Argument 5                                          Caller-saved scratch register

  f5                   Argument 6                                          Caller-saved scratch register

  f6                   Argument 7                                          Caller-saved scratch register

  f7                   Argument 8                                          Caller-saved scratch register

  f8 -- f15            Caller-saved scratch register                       ---

  f16 -- f31           Callee-saved register variable                      ---
  --------------------------------------------------------------------------------------------------------------------------------------

  : Floating-Point Register Functions

::: {.note}
::: {.admonition-title}
Note
:::

Many other configurations of the FPU registers are possible. To keep it
simple this table defines just the maximal configuration.
:::

When the FPU is configured the ABI changes dramatically as floating
point values are passed in FPU registers rather than core registers.
This means the application must be compiled with runtime libraries that
were compiled similarly.

Varargs also changes significantly as the FPU introduces two separate
register save areas (one for integers and one for floating point). This
means va\_list now becomes a struct (similar to what has been done for
x86 for years).

    typedef struct {
      int32_t gp_offset;
      int32_t fp_offset;
      void *overflow_arg_area;
      void *reg_save_area;
    } va_list[1];

### AGU Registers

Address-generation unit (AGU) registers are caller-saved scratch
registers. These registers exist on processors configured with DSP and
AGU extensions.

### Auxiliary Registers

`t_aux_reg`{.interpreted-text role="numref"} summarizes the most
commonly used auxiliary registers. Due to the large number of auxiliary
registers possible on an ARC processor, this listing is necessarily
incomplete, and might vary from one implementation to another. See the
*Programmer's Reference Manual* for a specific ARCv3-based processor for
a complete listing of the auxiliary registers that can be implemented on
that processor.

::: {#t_aux_reg}
  **Address**   **Function**
  ------------- --------------------------------------------------------------------
  0x2           Loop start address (lp\_start)
  0x3           Loop end address (lp\_end)
  0x4           Processor identification
  0x5           debug
  0x6           Program counter (nextpc)
  0xa           Condition flags (status32)
  0xb           Status save register for highest-priority interrupt (status32\_p0)
  0xc           Unused
  0x21          Processor-timer-0 count value
  0x22          Processor-timer-0 control value
  0x23          Processor-timer-0 limit value
  0x25          Interrupt-vector base address
  0x68          Default vector-base build configuration
  0x100         Processor-timer-1 count value
  0x101         Processor-timer-1 control value
  0x102         Processor-timer-1 limit value
  0x201         Software interrupt
  0x290         JLI table base register
  0x291         LDI table base register
  0x292         EI table base register
  0x400         Exception return address
  0x401         Exception-return branch-target address
  0x402         Exception-return status
  0x403         Exception cause
  0x404         Exception-fault address
  0x410         User-mode extension enables
  0x412         Branch-target address
  0x413         Unused
  0x414         Unused

  : Auxiliary-Register Functions
:::

The nextpc auxiliary register contains the program counter; the pcl
register contains the 4-byte aligned value of the program counter. The
status32 auxiliary register contains the condition flags.

For information on which registers can be used by which 16-bit
instructions, see the *Programmer's Reference Manual* for each
processor.

Stack Frame {#stk_frame}
-----------

This section describes the layout of the stack frame and registers that
must be saved by the callee prolog code.

### The Stack-Pointer Register

The stack-pointer (sp) register always points to the lowest used address
of the most recently allocated stack frame. The value of sp is a
four-byte-aligned address on ARC32 and an eight-byte-aligned value on
ARC64.

The stack-pointer register is commonly used as a base register to access
stack-frame-based variables, which always have a positive offset.
However, when alloca() is called, the stack-pointer register might be
arbitrarily decremented after the stack frame is allocated. In such a
case, the frame pointer register is used to reference stack-frame-based
variables.

### The Frame-Pointer Register

The frame pointer register (fp) is used when a function calls alloca()
to allocate space on the stack, and stack-frame-based variables must be
accessed. It is also used this way when the user specifies the
-ffixed-frame-pointer option.

### The Callee's Prolog Code

The callee's prolog code saves all registers that need to be saved.
Saved values include the value of the caller's frame-pointer register,
blink (return address) register, callee-saved registers used by the
function.

::: {.note}
::: {.admonition-title}
Note
:::

FP and BLINK are saved next to each other when both require saving.
Secondly, only the order in which FP and BLINK are saved is specified by
the ABI. The debugger can properly display stack frames with proper CFA
directives no matter the order in which the registers are saved (the
same currently applies to C++ exception unwinding).
:::

The caller\'s stack-pointer (sp) register does not need to be saved
because the compiler is able to restore the stack pointer for each
function to its original value (for example, by using an add
instruction).

![Stack Frame for One Function
Invocation](../images/stack_frame_1func_invoc.png){.align-center}

Allocating Stack Space Dynamically
----------------------------------

Programs can dynamically grow the current stack frame using a
memory-allocating function. The memory-allocating function must maintain
a frame pointer and the stack mechanics outlined in
`stk_frame`{.interpreted-text role="ref"} through
`pro_epi_code`{.interpreted-text role="ref"}. The stack frame must be
maintained using the frame pointer (fp) instead of the stack pointer
(sp).

Argument Passing {#arg_pass}
----------------

Arguments are passed as an ordered list of machine-level values from the
caller to the callee.

-   ARC32: The first eight words (32 bytes) of arguments are loaded into
    registers r0 to r7. In builds with a reduced register set, the first
    four words are loaded into r0 to r3.
-   ARC64: The first eight double words (64 bytes) of arguments are
    loaded into registers r0 to r7.
-   The remaining arguments are passed by storing them into the stack
    immediately above the stack-pointer register.
-   Floating point values are passed in f0 to f7 when the FPU is
    configured and the registers are wide enough for the specified type.
-   Vectors of floating point types are passed in FPU registers when
    those vectors and floating point types are supported by the hardware
    configuration chosen. They are passed in f0 to f7. After f0 to f7
    are consumed, the remainder are passed on the stack as overflow
    parameters.

Return Values {#ret_val}
-------------

Functions return the following results:

> -   Any scalar or pointer type that is 32 bits or less in size (char,
>     short, int) is returned in r0 (and type \"long\" when ARC32).
>
> -   Eight-byte integers (long long, double, and float complex) are
>     returned in r0 and r1 on ARC32 and just in r0 on ARC64 (and type
>     \"long\" is 64-bits and returned in just r0 on ARC64).
>
> -   Results of type complex double are returned in r0 to r3 on ARC32
>     and r0 and r1 on ARC64 when no FPU is configured.
>
> -   Results of type complex float are returned in r0 and r1 when no
>     FPU is configured.
>
> -   Results of all complex floating point types are returned in f0 and
>     f1 when the FPU is configured and the floating-point element type
>     is supported by that configuration.
>
> -   Results of type struct are returned in a caller-supplied temporary
>     variable whose address is passed in r0. For such functions, the
>     arguments are shifted so that they are passed in r1 and upwards.
>
>     NOTE: When structs (also unions, arrays, and vectors), are passed
>     by value they are passed in the core regisers until those core
>     registers are consumed, and the remainder are passed on the stack
>     in the argument-overflow area. It is very difficult to describe
>     precisely. The best practice is to create lots of examples and
>     examine the generated code.
>
##### Process Initialization

This Supplement does not define a process-initialization state. The
processor begins executing code at a hard-coded location and initially
has no stack; establishing the operating environment for processes and
programs entails setting up a stack and methods for passing arguments
and return values as described in `stk_frame`{.interpreted-text
role="ref"}.

The processor supports kernel and user operating modes to permit
different levels of privilege to be assigned to operating system kernels
and user programs, strictly controlling access to privileged
system-control instructions and special registers. Kernel mode is the
default mode from reset. For more information on the operating modes,
see the *Programmer's Reference Manual*.

The processor can be restarted by clearing the H bit in the STATUS32
register. On restart, the pipeline is flushed; interrupts are disabled;
status register flags are cleared; the semaphore register is cleared;
loop count, loop-start and loop-end registers are cleared; the
scoreboard unit is cleared; the pending-load flag is cleared; and
program execution resumes from the 32-bit address specified by the user
as the first 32-bit entry in the interrupt-vector table, the reset
vector. The core registers are not initialized except lp\_count (which
is cleared). A jump to the reset vector (a soft reset) does not pre-set
any of the internal states of the processor. The reset value of the
vector base register determines the reset vector address.

::: {.note}
::: {.admonition-title}
Note
:::

User extensions and optimizations to this area are permitted.
:::

##### Operating System Interface

Linux
-----

OS ABI consists of system calls provided by Linux kernel and call upon
by user space library code.

> -   ABI is similar to a regular function call in terms of arguments
>     passing semantics. For example, 64-bit data in register pairs.
> -   Up to eight arguments allowed in registers r0 to r7.
> -   Syscall number must be passed in register r8.
> -   Syscall return value is returned back in r0.
> -   All registers except r0 are preserved by kernel across the
>     Syscall.

The current Linux OS ABI (v4.8 kernel onwards) is ABIv4. For information
on the ABI versions, see
<https://github.com/foss-for-synopsys-dwc-arc-processors/linux/wiki/ARC-Linux-Syscall-ABI-Compatibility>

##### Coding Examples {#coding_ex}

This section discusses example code sequences for basic operations.

Prolog and Epilog Code {#pro_epi_code}
----------------------

A function's prolog and epilog code establish the environment needed by
the body of the function. This Supplement does not specify any
particular prolog or epilog code, but provides the following suggested
guidelines and examples; the only requirements of a function prolog are
that it meet the expectations of the caller and callee, particularly as
regards the passing of parameters.

-   The prolog establishes a stack frame, if necessary, and can save any
    callee-saved registers the function uses.
-   The epilog generally restores registers that were saved in the
    prolog code, restores the previous stack frame, and returns to the
    caller.

In each of the prolog-code examples in this section, framesize is the
size, in bytes, of the area needed for auto variables, spill
temporaries, and saved registers.

### Standard Prolog Code

Standard prolog code performs the following tasks, in this order:

> 1.  Saves the return-address (blink) register on the stack.
> 2.  Saves any callee-saved registers that are modified by the
>     function.
> 3.  Allocates any additional space required in the frame by
>     decrementing the stack pointer accordingly.

This is the standard prolog code ARCv3:

``` {.}
; Save return address register:
   push_s   %blink
; Save registers r14, r15, r16, and so on 
; (all callee-saved registers that must be saved):
   push_s   %r14
   push_s   %r15
   push_s   %r16
: Allocate remainder of frame
   sub      %sp, %sp, additional_space
```

### Abbreviated Prolog and Epilog

For a leaf function (that does not call other functions), a compiler can
abbreviate the prolog and epilog, as long as it conforms to the ABI for
globally accessed functions.

### Data Objects

The transfer of data to and from memory is accomplished using load and
store instructions.

### Volatile and Uncached Variables

The run-time model permits variables to be designated as volatile or
uncached.

-   A volatile variable is assumed to have a value that can
    asynchronously change, independent of the thread that is referencing
    the variable. Thus it is not advisable to cache the value of such
    variables or to attempt to optimize multiple accesses to them.
-   Uncached variables are loaded and stored without using the
    processor's data cache. Use .ucdata section to store them
    separately.

### Function Calls and Branching

Programs might use one of several branch, jump, and link instructions to
control execution flow through direct and indirect function calls and
branching. For function calling, the conditional branch-and-link
instruction has a maximum branch range of +/- 1 MB, and the target
address is 32-bit-aligned. The unconditional branch-and-link format has
a maximum branch range of +/- 16 MB.

See *Programmer's Reference Manual* for your ARCv3-based processor for a
list of instructions.
 


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
99    |0x63 | Reserved             | Reserved                  | N.A.
100   |0x64 | R_ARC_JLI64_SECTOFF  | JLI offset                | u10 = ((S - <start of section>) + A) >> 2 
101   |0x65 | R_ARC_S25W_PCREL_WCALL | PC-relative (weak)      | disp25w = (S + A - P) >> 2
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

<!-- below from MWDT //dwarc/TechPubs/UserDocs/Source/4091_ARCv3_ABI/RST/source/obj_files.rst#3 -->

Object Files {#obj_files}
============

ELF Header
----------

### Machine Information

For file identification in [e\_ident]{.title-ref}, ARCv3-based
processors require the following values:

> `e_ident[EI_CLASS]` `ELFCLASS32` For all 32-bit implementations
>
> `e_ident[EI_CLASS]` `ELFCLASS64` For all 64-bit implementations
>
> `e_ident[EI_DATA]` `ELFDATA2LSB` If execution environment is
> little-endian
>
> `e_ident[EI_DATA]` `ELFDATA2MS` If execution environment is big-endian

Processor identification resides in the ELF header\'s e\_machine member,
and must have the value 253 (0xfd), defined as the name
`EM_ARC_COMPACT3_64` for all 64-bit implementations, or the value 255
(0xff), defined as the name `EM_ARC_COMPACT3` for all 32-bit
implementations.

Tools may use e\_flags to distinguish ARCv3-based processor families,
where 5 identifies the ARC EM processor family, and 6 identifies the ARC
HS processor family.

The high bits are used to select the Linux OSABI:

  ------- ------------- ------------------------------
  0x000   OSABI\_ORIG   v2.6.35 kernel (sourceforge)
  0x200   OSABI\_V2     v3.2 kernel (sourceforge)
  0x300   OSABI\_V3     v3.9 kernel (sourceforge)
  0x400   OSABI\_V4     v24.8 kernel (sourceforge)
  ------- ------------- ------------------------------

  : Linux OSABI Selection

Special Sections
----------------

### Special Sections: Types and Attributes

The sections listed in `t_sp_sec`{.interpreted-text role="numref"} are
used by the system and have the types and attributes shown.

::: {#t_sp_sec}
  **Name**             **Type**        **Attributes**
  -------------------- --------------- -----------------------------------------------------------
  .arcextmap           SHT\_PROGBITS   none
  .bss                 SHT\_NOBITS     SHF\_ALLOC + SHF\_WRITE
  .ctors               SHT\_PROGBITS   SHF\_ALLOC
  .data                SHT\_PROGBITS   SHF\_ALLOC + SHF\_WRITE
  .fixtable            SHT\_PROGBITS   SHF\_ALLOC + SHF\_WRITE
  .heap                SHT\_NOBITS     SHF\_ALLOC + SHF\_WRITE
  .initdata            SHT\_PROGBITS   SHF\_ALLOC
  .offsetTable         SHT\_PROGBITS   SHF\_ALLOC + SHF\_OVERLAY\_OFFSET\_TABLE + SHF\_INCLUDE
  .overlay             SHT\_PROGBITS   SHF\_ALLOC + SHF\_EXECINSTR + SHF\_OVERLAY + SHF\_INCLUDE
  .overlayMultiLists   SHT\_PROGBITS   SHF\_ALLOC + SHF\_INCLUDE
  .pictable            SHT\_PROGBITS   SHF\_ALLOC
  .rodata\_in\_data    SHT\_PROGBITS   SHF\_ALLOC + SHF\_WRITE
  .sbss                SHT\_NOBITS     SHF\_ALLOC + SHF\_WRITE
  .sdata               SHT\_PROGBITS   SHF\_ALLOC + SHF\_WRITE
  .stack               SHT\_NOBITS     SHF\_ALLOC + SHF\_WRITE
  .text                SHT\_PROGBITS   SHF\_ALLOC + SHF\_EXECINST
  .tls                 SHT\_PROGBITS   SHF\_ALLOC + SHF\_WRITE
  .ucdata              SHT\_PROGBITS   SHF\_ALLOC + SHF\_WRITE
  .vectors             SHT\_PROGBITS   SHF\_ALLOC + SHF\_EXECINST

  : Special Sections
:::

::: {.note}
::: {.admonition-title}
Note
:::

To be compliant with the ARCv3 ABI, a system must support
[.tls]{.title-ref}, [.sdata]{.title-ref}, and [.sbss]{.title-ref}
sections, and must recognize, but may choose to ignore, .arcextmap and
.stack sections.
:::

### Special Sections: Description

The special sections are described in `t_spl_sec_desc`{.interpreted-text
role="numref"}

Special features might create additional sections. For details regarding
overlay-related sections see the *Automated Overlay Manager User's
Guide*.

>   --------------------------------------------------------------------------------
>   **Special Section**  **Description**
>   -------------------- -----------------------------------------------------------
>   .arcextmap           Debugging information relating to processor extensions
>
>   .bss                 Uninitialized variables that are not const-qualified
>                        (startup code normally sets .bss to all zeros)
>
>   .ctors               Contains an array of functions that are called at startup
>                        to initialize elements such as C++ static variables
>
>   .data                Static variables (local and global)
>
>   .fixtable            Function replacement prologs
>
>   .heap                Uninitialized memory used for the heap
>
>   .initdata            Initialized variables and code (usually compressed) to be
>                        copied into place during run-time startup
>
>   .offsetTable         Overlay-offset table
>
>   .overlay             All overlays defined in the executable
>
>   .overlayMultiLists   Token lists for functions that appear in more than one
>                        overlay group
>
>   .pictable            Table for relocating pre-initialized data when generating
>                        position-independent code and data
>
>   .rodata\_in\_data    Read-only string constants when -Hharvard or -Hccm is
>                        specified.
>
>   .sbss                Uninitialized data, set to all zeros by startup code and
>                        directly accessible from the %gp register
>
>   .sdata               Initialized small data, directly accessible from the %gp
>                        register, and small uninitialized variables
>
>   .stack               Stack information
>
>   .text                Executable code
>
>   .tls                 Thread-local data
>
>   .ucdata              Holds data accessed using cache bypass
>
>   .vectors             Interrupt vector table
>   --------------------------------------------------------------------------------
>
::: {.note}
::: {.admonition-title}
Note
:::

[.tls]{.title-ref} is not necessarily the same as the
[.tdata]{.title-ref} section found in other architectures. It does not
need special treatment except to be recognized as a valid .data section.
It may or may not map into any current or future system thread
architecture. It must remain programmable by the RTOS and application
programmer as defined by the ARC MetaWare run time so that true
lightweight threads can be implemented.
:::

::: {.caution}
::: {.admonition-title}
Caution
:::

Sections that contribute to a loadable program segment must not contain
overlapping virtual addresses.
:::

Symbol Table
------------

### Symbol Values

ARCv3-based processors that support the Linux operating system follow
the Linux conventions for dynamic linking.

Small-Data Area
---------------

Programs may use a small-data area to reduce code size by storing small
variables in the .sdata and .sbss sections, where such data can be
addressed using small, signed offsets from the %gp register. If the
program uses small data, program startup must initialize the %gp
register to the address of symbol `_SDA_BASE_` Such initialization is
typically performed by the default startup code.

Register Information
--------------------

The names and functions of the processor registers are described in
`regs`{.interpreted-text role="ref"}. Compilers may map variables to a
register or registers as needed in accordance with the rules described
in `arg_pass`{.interpreted-text role="ref"} and
`ret_val`{.interpreted-text role="ref"}, including mapping multiple
variables to a single register.

Compilers may place auto variables that are not mapped into registers at
fixed offsets within the function's stack frame as required, for example
to obtain the variable's address or if the variable is of an aggregate
type.

Relocation
----------

### Relocation Types

Relocation entries describe how to alter the instruction and data
relocation fields shown in `reloc_fields`{.interpreted-text role="ref"}.
Bit numbers appear in the lower box corners. Little-endian byte numbers
appear in the upper right box corners.

### Relocatable Fields {#reloc_fields}

This document specifies several types of relocatable fields used by
relocations.

#### bits8

Specifies 8 bits of data in a separate byte.

![bits8 Relocatable
Field](../images/bits8_reloc_field.png){.align-center}

#### bits16

Specifies 16 bits of data in a separate byte.

![bits16 Relocatable
Field](../images/bits16_reloc_field.png){.align-center}

#### bits24

Specifies 24 bits of data in a separate byte.

![bits24 Relocatable
Field](../images/bits24_reloc_field.png){.align-center}

#### disp7u

The gray areas in `disp7u_rf`{.interpreted-text role="numref"} represent
a disp7u relocatable field, which specifies a seven-bit unsigned
displacement within a 16-bit instruction word, with bits 2-0 of the
instruction stored in bits 2-0 and bits 6-3 of the instruction stored in
bits 7-4.

> disp7u Relocatable Field

#### disp9

The gray area in `disp9_rf`{.interpreted-text role="numref"} represents
a disp9 relocatable field, which specifies a nine-bit signed
displacement within a 32-bit instruction word.

> disp9 Relocatable Field

#### disp9ls

The gray areas in `disp9ls_rf`{.interpreted-text role="numref"}
represent a disp9ls relocatable field, which specifies a nine-bit signed
displacement within a 32-bit instruction word.

> disp9ls Relocatable Field

#### disp9s

The gray area in `disps_rf`{.interpreted-text role="numref"} represents
a disp9s relocatable field, which specifies a 9-bit signed displacement
within a 16-bit instruction word.

> disp9s Relocatable Field

#### disp10u

The gray area in `disp10u_rf`{.interpreted-text role="numref"}
represents a disp10u relocatable field, which specifies a 10-bit
unsigned displacement within a 16-bit instruction word.

> disp10u Relocatable Field

#### disp13s

The gray area in `disp_13s_rf`{.interpreted-text role="numref"}
represents a disp13s relocatable field, which specifies a signed 13-bit
displacement within a 16-bit instruction word. The displacement is to a
32-bit-aligned location and thus bits 0 and 1 of the displacement are
not explicitly stored.

> disp13s Relocatable Field

#### disp21h

The gray areas in `disp21h_rf`{.interpreted-text role="numref"}
represent a disp21h relocatable field, which specifies a 21-bit signed
displacement within a 32-bit instruction word. The displacement is to a
halfword-aligned target location, and thus bit 0 of the displacement is
not explicitly stored. Note that the 32-bit instruction containing this
relocation field may be either 16-bit-aligned or 32-bit-aligned.

> disp21h Relocatable Field

#### disp21w

The gray areas in `disp21w_rf`{.interpreted-text role="numref"}
represent a disp21w relocatable field, which specifies a signed 21-bit
displacement within a 32-bit instruction word. The displacement is to a
32-bit-aligned target location, and thus bits 0 and 1 of the
displacement are not explicitly stored. Note that the 32-bit instruction
containing this relocation field may be either 16-bit-aligned or
32-bit-aligned.

> disp21w Relocatable Field

#### disp25h

The gray areas in `disp25h_rf`{.interpreted-text role="numref"}
represent a disp25h relocatable field, which specifies a 25-bit signed
displacement within a 32-bit instruction word. The displacement is to a
halfword-aligned target location, and thus bit 0 is not explicitly
stored. Note that the 32-bit instruction containing this relocation
field may be either 16-bit-aligned or 32-bit-aligned.

> disp25h Relocatable Field

#### disp25w

The gray areas in `disp25w_rf`{.interpreted-text role="numref"}
represent a disp25w relocatable field, which specifies a 25-bit signed
displacement within a 32-bit instruction word. The displacement is to a
32-bit-aligned target location, and thus bits 0 and 1 are not explicitly
stored. Note that the 32-bit instruction containing this relocation
field may be either 16-bit-aligned or 32-bit-aligned.

> disp25w Relocatable Field

#### disps9

The gray area in `disps9_rf`{.interpreted-text role="numref"} represents
a disps9 relocatable field, which specifies a nine-bit signed
displacement within a 16-bit instruction word. The displacement is to a
32-bit-aligned location, and thus bits 0 and 1 of the displacement are
not explicitly stored. This means that effectively the field is bits
10-2, stored at 8-0.

> disps9 Relocatable Field

#### disps12

The gray areas in `disps12_rf`{.interpreted-text role="numref"}
represent a disps12 relocatable field, which specifies a twelve-bit
signed displacement within a 32-bit instruction word. The high six bits
are in 0-5, and the low six bits are in 6-11.

> disps12 Relocatable Field

#### word32

`word32_rf`{.interpreted-text role="numref"} specifies a 32-bit field
occupying four bytes, the alignment of which is four bytes unless
otherwise specified. See also `word32le_rf`{.interpreted-text
role="numref"} and `word32be_rf`{.interpreted-text role="numref"}.

> disps12 Relocatable Field

#### word32me (Little-Endian)

Specifies a 32-bit field in middle-endian Storage. Bits 31..16 are
stored first, and bits 15..0 are stored adjacently. The individual
halfwords are stored in the native endian orientation of the machine
(little endian in `word32le_rf`{.interpreted-text role="numref"}).

> word32me Relocatable Field on a Little-Endian Machine

#### word32me (Big-Endian)

Specifies a 32-bit field in middle-endian Storage. Bits 31..16 are
stored first, and bits 15..0 are stored adjacently. The individual
halfwords are stored in the native endian orientation of the machine
(big endian in `word32be_rf`{.interpreted-text role="numref"}).

> word32me Relocatable Field on a Big-Endian Machine

### Relocatable-Field Calculations

The calculations presented in this section assume that the actions
transform a relocatable file into either an executable or a
shared-object file. Conceptually, the link editor merges one or more
relocatable files to form the output.

The procedure is as follows:

> -   Decide how to combine and locate the input files.
> -   Update the symbol values.
> -   Perform the relocation.

Relocations applied to executable or shared object files are similar and
accomplish the same result.

The descriptions in this section use the following notation:

+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| **Address**                 | **Function**                                                                                                                       |
+=============================+====================================================================================================================================+
| A                           | The addend used to compute the value of the relocatable field                                                                      |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| B                           | The base address at which a shared object has been loaded into memory during execution. Generally, a shared object file is built   |
|                             | with a 0-base virtual address, but the execution address will be different.                                                        |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| G                           | The offset into the global offset table at which the address of the relocated symbol will reside during execution.                 |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| GOT                         | The address of the global offset table                                                                                             |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| L                           | The place (section offset or address) of the PLT entry for a symbol. A procedure linkage table entry redirects a function call to  |
|                             | the proper destination. The link editor builds the initial procedure linkage table, and the dynamic linker modifies the associated |
|                             | GOT entries during execution.                                                                                                      |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| MES                         | Middle-Endian Storage A 32-bit word is stored in two halfwords, with bits 31..16 stored first and bits 15..0 stored adjacently.    |
|                             | The individual halfwords are stored in the native endian orientation of the machine. This type of storage is used for all          |
|                             | instructions and long immediate operands in the ARCv3 architecture.                                                                |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| P                           | The place (section offset or address) of the storage unit being relocated (computed using r\_offset)                               |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| S                           | The value of the symbol whose index resides in the relocation entry                                                                |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| SECTSTART                   | Start of the current section. Used in calculating offset types.                                                                    |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| \_[SDA\_BASE]()             | Base of the small-data area                                                                                                        |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+
| JLI                         | Base of the JLI table                                                                                                              |
+-----------------------------+------------------------------------------------------------------------------------------------------------------------------------+

: Relocation Terminology

A relocation entry\'s r\_offset value designates the offset or virtual
address of the first byte of the field to be relocated. The relocation
type specifies which bits to change and how to calculate their values.
The ARCv3 architecture uses only Elf32\_Rela relocation entries. The
addend is contained in the relocation entry. Any data from the field to
be relocated is discarded. In all cases, the addend and the computed
result use the same byte order.

::: {.note}
::: {.admonition-title}
Note
:::

With the exception of word32, all relocations with replacement fields in
four-byte words must be written using Middle-Endian Storage.
:::

  **Name**                                                                                                                                                                                                                            **Value**                                                **Field**   **Calculation**
  ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------- ----------- -----------------------------------------------------
  R\_ARC\_NONE                                                                                                                                                                                                                        0x0                                                      none        none
  R\_ARC\_8                                                                                                                                                                                                                           0x1                                                      bits8       S+A
  R\_ARC\_16                                                                                                                                                                                                                          0x2                                                      bits16      S+A
  R\_ARC\_24                                                                                                                                                                                                                          0x3                                                      bits24      S+A
  R\_ARC\_32                                                                                                                                                                                                                          0x4                                                      word32      S+A
  R\_ARC\_64                                                                                                                                                                                                                          0x5                                                      word64      S+A
  R\_ARC\_N8                                                                                                                                                                                                                          0x8                                                      bits8       A--S
  R\_ARC\_N16                                                                                                                                                                                                                         0x9                                                      bits16      A--S
  R\_ARC\_N24                                                                                                                                                                                                                         0xa                                                      bits24      A--S
  R\_ARC\_N32                                                                                                                                                                                                                         0xb                                                      word32      P - (S+A)
  R\_ARC\_SDA                                                                                                                                                                                                                         0xc                                                      disp9       S--\_[SDA\_BASE]() +A
  R\_ARC\_SECTOFF                                                                                                                                                                                                                     0xd                                                      word32      (S-SECTSTART)+A
  R\_ARC\_S21H\_PCREL                                                                                                                                                                                                                 0xe                                                      disp21h     (S+A-P)\>\>1 (convert to halfword displacement)
  R\_ARC\_S21W\_PCREL                                                                                                                                                                                                                 0xf                                                      disp21w     (S+A-P)\>\>2 (convert to longword dis+D69placement)
  R\_ARC\_S25H\_PCREL                                                                                                                                                                                                                 0x10                                                     disp25h     (S+A-P)\>\>1 (convert to halfword displacement)
  R\_ARC\_S25W\_PCREL                                                                                                                                                                                                                 0x11                                                     disp25w     (S+A-P)\>\>2 (convert to longword displacement)
  R\_ARC\_SDA32                                                                                                                                                                                                                       0x12                                                     word32      (S+A)-\_[SDA\_BASE]()
  R\_ARC\_SDA\_LDST                                                                                                                                                                                                                   0x13                                                     disp9ls     (S+A-\_[SDA\_BASE]()) (s9 range)
  R\_ARC\_SDA\_LDST1                                                                                                                                                                                                                  0x14                                                     disp9ls     (S+A-\_[SDA\_BASE]()) \>\>1 (s10 range)
  R\_ARC\_SDA\_LDST2                                                                                                                                                                                                                  0x15                                                     disp9ls     (S+A-\_[SDA\_BASE]()) \>\>2 (s11 range)
  R\_ARC\_SDA16\_LD                                                                                                                                                                                                                   0x16                                                     disp9s      (S+A-\_[SDA\_BASE]()) (s9 range)
  R\_ARC\_SDA16\_LD1                                                                                                                                                                                                                  0x17                                                     disp9s      (S+A-\_[SDA\_BASE]()) \>\>1 (s10 range)
  R\_ARC\_SDA16\_LD2                                                                                                                                                                                                                  0x18                                                     disp9s      (S+A-\_[SDA\_BASE]()) \>\>2 (s11 range)
  R\_ARC\_S13\_PCREL                                                                                                                                                                                                                  0x19                                                     disp13s     (S+A-P) \>\>2
  R\_ARC\_W                                                                                                                                                                                                                           0x1a                                                     word32      (S+A) & \~3 (word-align)
  R\_ARC\_32\_ME                                                                                                                                                                                                                      0x1b                                                     word32me    S+A (MES)
  R\_ARC\_N32\_ME                                                                                                                                                                                                                     0x1c                                                     word32me    (ME (A-S))
  R\_ARC\_SECTOFF\_ME                                                                                                                                                                                                                 0x1d                                                     word32me    (S-SECTSTART)+A (MES)
  R\_ARC\_SDA32\_ME                                                                                                                                                                                                                   0x1e                                                     word32me    (S+A)-\_[SDA\_BASE]() (MES)
  R\_ARC\_W\_ME                                                                                                                                                                                                                       0x1f                                                     word32me    (S+A) & \~3 (word-aligned MES)
  R\_AC\_SECTOFF\_U8                                                                                                                                                                                                                  0x23                                                     disp9ls     S+A-SECTSTART
  R\_AC\_SECTOFF\_U8\_1                                                                                                                                                                                                               0x24                                                     disp9ls     (S+A-SECTSTART) \>\>1
  R\_AC\_SECTOFF\_U8\_2                                                                                                                                                                                                               0x25                                                     disp9ls     (S+A-SECTSTART) \>\>2
  R\_AC\_SECTOFF\_S9                                                                                                                                                                                                                  0x26                                                     disp9ls     S+A-SECTSTART - 256
  R\_AC\_SECTOFF\_S9\_1                                                                                                                                                                                                               0x27                                                     disp9ls     (S+A-SECTSTART - 256) \>\>1
  R\_AC\_SECTOFF\_S9\_2                                                                                                                                                                                                               0x28                                                     disp9ls     (S+A-SECTSTART - 256) \>\>2
  R\_ARC\_SECTOFF\_ME\_1                                                                                                                                                                                                              0x29                                                     word32me    ((S-SECTSTART)+A) \>\>1 (MES)
  R\_ARC\_SECTOFF\_ME\_2                                                                                                                                                                                                              0x2a                                                     word32me    ((S-SECTSTART)+A) \>\>2 (MES)
  R\_ARC\_SECTOFF\_1                                                                                                                                                                                                                  0x2b                                                     word32      ((S-SECTSTART)+A) \>\>1
  R\_ARC\_SECTOFF\_2                                                                                                                                                                                                                  0x2c                                                     word32      ((S-SECTSTART)+A) \>\>2
  R\_ARC\_SDA\_12                                                                                                                                                                                                                     0x2d                                                     disps12     (S + A) - \_[SDA\_BASE]()
  R\_ARC\_LDI\_SECTOFF1                                                                                                                                                                                                               0x2e                                                     disp7u      (S - \<ldi-table base\> + A) \>\> 2
  R\_ARC\_LDI\_SECTOFF2                                                                                                                                                                                                               0x2f                                                     disps12     (S - \<ldi-table base\> + A) \>\> 2
  R\_ARC\_SDA16\_ST2                                                                                                                                                                                                                  0x30                                                     disps9      (S+A-\_SDA\_BASE) \>\> 2
  R\_ARC\_PC32                                                                                                                                                                                                                        0x32                                                     word32      S+A-P
  R\_ARC\_GOTPC32                                                                                                                                                                                                                     0x33                                                     word32      GOT+G+A-P
  R\_ARC\_PLT32                                                                                                                                                                                                                       0x34                                                     word32      L+A-P
  R\_ARC\_COPY                                                                                                                                                                                                                        0x35                                                     none        none
  R\_ARC\_GLOB\_DAT                                                                                                                                                                                                                   0x36                                                     word32      S
  R\_ARC\_JMP\_SLOT                                                                                                                                                                                                                   0x37                                                     word32      S
  R\_ARC\_RELATIVE                                                                                                                                                                                                                    0x38                                                     word32      B+A
  R\_ARC\_GOTOFF                                                                                                                                                                                                                      0x39                                                     word32      S+A-GOT
  R\_ARC\_GOTPC                                                                                                                                                                                                                       0x3a                                                     word32      GOT+A-P
  R\_ARC\_GOT32                                                                                                                                                                                                                       0x3b                                                     word32      G+A
  R\_ARC\_S25H\_PCREL\_PLT                                                                                                                                                                                                            0x3d                                                     disp25w     L+A-P
  R\_ARC\_JLI\_SECTOFF                                                                                                                                                                                                                0x3f                                                     disp10u     S--JLI
  R\_ARC\_AOM\_TOKEN\_ME                                                                                                                                                                                                              0x40                                                     word32me    AOM token (32 bits)(MES)
  R\_ARC\_AOM\_TOKEN R\_ARC\_TLS\_DTPMOD R\_ARC\_TLS\_DTPOFF R\_ARC\_TLS\_TPOFF R\_ARC\_TLS\_GD\_GOT R\_ARC\_TLS\_GD\_LD R\_ARC\_TLS\_GD\_CALL R\_ARC\_TLS\_IE\_GOT R\_ARC\_TLS\_DTPOFF\_S9 R\_ARC\_TLS\_LE\_S9 R\_ARC\_TLS\_LE\_32   0x41 0X42 0X43 0x44 0x45 0X46 0X47 0X48 0X49 0X4A 0X4B   word32      AOM token (32 bits)
  R\_ARC\_S25W\_PCREL\_PLT                                                                                                                                                                                                            0x4c                                                     disp25w     L+A-P
  R\_ARC\_S21H\_PCREL\_PLT                                                                                                                                                                                                            0x4d                                                     disp21h     L+A-P

  : Relocation Types

A relocation entry\'s r\_offset value designates the offset or virtual
address of the first byte of the field to be relocated. The relocation
type specifies which bits to change and how to calculate their values.
The ARCv3 architecture uses only Elf32\_Rela relocation entries. The
addend is contained in the relocation entry. Any data from the field to
be relocated is discarded. In all cases, the addend and the computed
result use the same byte order.

::: {.note}
::: {.admonition-title}
Note
:::

With the exception of word32, all relocations with replacement fields in
four-byte words must be written using Middle-Endian Storage.
:::

**R\_ARC\_S21H\_PCREL**

This relocation type is used with conditional branches, for example:

``` {.}
bne label
```

**R\_ARC\_S21W\_PCREL**

This relocation type is used with conditional branch and link, for
example:

``` {.}
blne label
```

**R\_ARC\_S25H\_PCREL**

This relocation type is used with unconditional branches, for example:

``` {.}
b label
```

**R\_ARC\_S25W\_PCREL**

This relocation type is used with unconditional branch and link, for
example:

``` {.}
bl printf
```

**R\_ARC\_SDA32**

This relocation type is used with 32-bit small-data fixups, for example:

``` {.}
add   r0, gp, var@sda
```

**R\_ARC\_SDA\_LDST\***

The R\_ARC\_SDA\_LDST\* relocation types are used with small-data fixups
on loads and stores. Examples:

``` {.}
ldb   r0,  [gp, var@sda]   ; R_ARC_SDA_LDST
stw   r0,  [gp, var@sda]   ; R_ARC_SDA_LDST1
ld    r0,  [gp, var@sda]   ; R_ARC_SDA_LDST2
```

**R\_ARC\_SDA16\_LD\***

The R\_ARC\_SDA16\_LD\* relocation types are used with 16-bit
GP-relative load instructions, when such instructions load a small-data
variable relative to the GP. Examples:

``` {.}
ldb_s  r0, [gp, var@sda]   ; R_ARC_SDA16_LD
ldw_s  r0, [gp, var@sda]   ; R_ARC_SDA16_LD1
ld_s   r0, [gp, var@sda]   ; R_ARC_SDA16_LD2
```

**R\_ARC\_S13\_PCREL**

This relocation type is used with 16-bit branch and link, for example:

``` {.}
bl_s printf
```

**R\_ARC\_W**

This relocation type is used to ensure 32-bit alignment of a fixup
value. Examples:

``` {.}
mov   r0,  var@l
ld    r0, [pcl, lab - .@l]
```

**R\_ARC\_\*\_ME**

Relocation types ending in \_ME behave like the non-ME relocation type
of the same name, with the exception that they use Middle-Endian
Storage: A 32-bit word is stored in two halfwords, with bits 31..16
stored first and bits 15..0 stored adjacently. The individual halfwords
are stored in the native endian orientation of the machine. That is, the
upper halfwords both have bits 31..16, but they are in a different
sequence between big and little endian.

This type of storage is used for all instructions and long immediate
operands in the ARCv3 architecture.

**R\_AC\_SECTOFF\***

The R\_AC\_SECTOFF\* relocation types allow a section-relative offset
for ARCv3 loads and stores in the short-immediate-operand range of 0 to
255 (-256 to -255 for the S9 variety), so long as the base register is
loaded with the address of the section. Addressing may be scaled such
that the range for halfwords is 0 to 510 (-256 to -510) and the range
for 32-bit word accesses is 0 to 1020 (-256 to -1020), with byte
accesses retaining the range 0 to 255 or -256 to -255. Examples:

``` {.}
ldb  r0, [r20, var@sectoff_u8]   ; R_AC_SECTOFF_U8
stw  r0, [r20, var@sectoff_u8]   ; R_AC_SECTOFF_U8_1
ld   r0, [r20, var@sectoff_u8]   ; R_AC_SECTOFF_U8_2
ldb  r0, [r20, var@sectoff_s9]   ; R_AC_SECTOFF_S9
stw  r0, [r20, var@sectoff_s9]   ; R_AC_SECTOFF_S9_1
ld   r0, [r20, var@sectoff_s9]   ; R_AC_SECTOFF_S9_2
```

::: {.note}
::: {.admonition-title}
Note
:::

The ninth bit of the replacement field is not used for the following
relocation types: - R\_AC\_SECTOFF\_U8 - R\_AC\_SECTOFF\_U8\_1 -
R\_AC\_SECTOFF\_U8\_2
:::

**R\_ARC\_SECTOFF\***

The R\_ARC\_SECTOFF\* relocation types are used with section-relative
offset loads and stores from or to XY memory.

**R\_ARC\_GOTPC32**

This relocation type is used to obtain a PC-relative reference to the
GOT entry for a symbol. This type is used for the same purpose as
R\_ARC\_GOT32 but uses PC-relative addressing to reference the GOT
whereas type R\_ARC\_GOT32 is typically used with a base register
containing the address of the GOT. Example:

``` {.}
ld r0, [pcl, var@gotpc]
```

**R\_ARC\_PLT32**

This relocation type computes the address of the symbol\'s PLT entry and
additionally instructs the link editor to build a procedure linkage
table. This relocation type is usually not explicitly needed, as the
link editor converts function calls to use this type when building a
shared library or dynamic executable. Example:

``` {.}
bl func@plt
```

**R\_ARC\_COPY**

The link editor creates this relocation type for dynamic linking. Its
offset member refers to a location in a writable segment. The symbol
table index specifies a symbol that should exist both in the current
object file and in a shared object. During execution, the dynamic linker
copies data associated with the shared object\'s symbol to the location
specified by the offset.

**R\_ARC\_GLOB\_DAT**

The link editor creates this relocation type for dynamic linking. This
relocation type is used to set a global offset table entry to the
address of the specified symbol. The special relocation type allows one
to determine the correspondence between symbols and global offset table
entries.

**R\_ARC\_JMP\_SLOT**

The link editor creates this relocation type for dynamic linking. Its
offset member gives the location of a PLT's GOT entry. The dynamic
linker modifies the GOT entry so that the PLT will transfer control to
the designated symbol\'s address.

You might add examples after implementation is finished (mj, 1/05).

**R\_ARC\_RELATIVE**

The link editor creates this relocation type for dynamic linking. Its
offset member gives a location within a shared object that contains a
value representing a relative address. The dynamic linker computes the
corresponding virtual address by adding the virtual address at which the
shared object was loaded to the relative address. Relocation entries for
this type must specify 0 for the symbol table index.

**R\_ARC\_GOTOFF**

This relocation type computes the difference between a symbol\'s value
and the address of the global offset table. It additionally instructs
the link editor to build the global offset table. This relocation type
is not used for loading from the contents of the GOT, but to use the
global data pointer anchored at the GOT to access other nearby data.

Example:

``` {.}
add r0, gp, var@gotoff
```

**R\_ARC\_GOTPC**

This relocation type resembles R\_ARC\_PC32, except it uses the address
of the global offset table in its calculation. The symbol referenced in
this relocation is \_[GLOBAL\_OFFSET\_TABLE](), which additionally
instructs the link editor to build the global offset table. This
relocation type provides a PC-relative means of obtaining the address of
the global offset table. Example:

``` {.}
add gp, pcl, _GLOBAL_OFFSET_TABLE_@gotpc
```

### Relocation Table

``` {.}
# Generic
#Relocation.new("R_ARC_NONE         0x0   none      bitfield    none")
Relocation.new("R_ARC_8             0x1   bits8     bitfield    S+A")
Relocation.new("R_ARC_16            0x2   bits16    bitfield    S+A")
Relocation.new("R_ARC_24            0x3   bits24    bitfield    S+A")
Relocation.new("R_ARC_32            0x4   word32    bitfield    S+A")

# Unsupported
Relocation.new("R_ARC_N8            0x8   bits8     bitfield    A-S")
Relocation.new("R_ARC_N16           0x9   bits16    bitfield    A-S")
Relocation.new("R_ARC_N24           0xa   bits24    bitfield    A-S")
Relocation.new("R_ARC_N32           0xb   word32    bitfield    A-S")
Relocation.new("R_ARC_SDA           0xc   disp9     bitfield    ME(S+A-_SDA_BASE_)")
Relocation.new("R_ARC_SECTOFF       0xd   word32    bitfield    (S-SECTSTART)+A")

# arcompact elf me reloc
Relocation.new("R_ARC_S21H_PCREL    0xe   disp21h   signed      ME((S+A-P)>>1) (convert to halfword displacement)")
Relocation.new("R_ARC_S21W_PCREL    0xf   disp21w   signed      ME((S+A-P)>>2) (convert to longword displacement)")
Relocation.new("R_ARC_S25H_PCREL    0x10  disp25h   signed      ME((S+A-P)>>1) (convert to halfword displacement)")
Relocation.new("R_ARC_S25W_PCREL    0x11  disp25w   signed      ME((S+A-P)>>2) (convert to longword displacement)")
Relocation.new("R_ARC_SDA32         0x12  word32    signed      ME((S+A)-_SDA_BASE_)")
Relocation.new("R_ARC_SDA_LDST      0x13  disp9ls   signed      ME((S+A-_SDA_BASE_)) (s9 range)")
Relocation.new("R_ARC_SDA_LDST1     0x14  disp9ls   signed      ME((S+A-_SDA_BASE_)>>1) (s10 range)")
Relocation.new("R_ARC_SDA_LDST2     0x15  disp9ls   signed      ME((S+A-_SDA_BASE_)>>2) (s11 range)")

# Short instructions should no be marked as ME
Relocation.new("R_ARC_SDA16_LD      0x16  disp9s    signed      (S+A-_SDA_BASE_) (s9 range)")
Relocation.new("R_ARC_SDA16_LD1     0x17  disp9s    signed      (S+A-_SDA_BASE_)>>1 (s10 range)")
Relocation.new("R_ARC_SDA16_LD2     0x18  disp9s    signed      (S+A-_SDA_BASE_)>>2 (s11 range)")
Relocation.new("R_ARC_S13_PCREL     0x19  disp13s   signed      ((S+A-P)>>2)")

# Unsupported
Relocation.new("R_ARC_W             0x1a  word32    bitfield    (S+A)&~3 (word-align)")

# arcompact elf me reloc
Relocation.new("R_ARC_32_ME         0x1b  limm      signed      ME(S+A) (MES)")

# TODO: This is a test relocation
Relocation.new("R_ARC_32_ME_S       0x69  limms     signed      ME(S+A) (MES)")

# Unsupported
Relocation.new("R_ARC_N32_ME        0x1c  word32    bitfield    ME(A-S) (MES)")
Relocation.new("R_ARC_SECTOFF_ME    0x1d  word32    bitfield    ME((S-SECTSTART)+A) (MES)")

# arcompact elf me reloc
Relocation.new("R_ARC_SDA32_ME      0x1e  limm      signed      (S+A-_SDA_BASE_)")

# Unsupported
Relocation.new("R_ARC_W_ME          0x1f  word32    bitfield    ME((S+A)&~3) (word-aligned MES)")
Relocation.new("R_AC_SECTOFF_U8     0x23  disp9ls   bitfield    ME(S+A-SECTSTART)")
Relocation.new("R_AC_SECTOFF_U8_1   0x24  disp9ls   bitfield    ME((S+A-SECTSTART)>>1)")
Relocation.new("R_AC_SECTOFF_U8_2   0x25  disp9ls   bitfield    ME((S+A-SECTSTART)>>2)")

Relocation.new("R_AC_SECTOFF_S9     0x26  disp9ls   bitfield    ME(S+A-SECTSTART-256)")
Relocation.new("R_AC_SECTOFF_S9_1   0x27  disp9ls   bitfield    ME((S+A-SECTSTART-256)>>1)")
Relocation.new("R_AC_SECTOFF_S9_2   0x28  disp9ls   bitfield    ME((S+A-SECTSTART-256)>>2)")


Relocation.new("R_ARC_SECTOFF_ME_1  0x29  word32    bitfield    ME(((S-SECTSTART)+A)>>1) (MES)")
Relocation.new("R_ARC_SECTOFF_ME_2  0x2a  word32    bitfield    ME(((S-SECTSTART)+A)>>2) (MES)")
Relocation.new("R_ARC_SECTOFF_1     0x2b  word32    bitfield    ((S-SECTSTART)+A)>>1")
Relocation.new("R_ARC_SECTOFF_2     0x2c  word32    bitfield    ((S-SECTSTART)+A)>>2")

Relocation.new("R_ARC_SDA_12        0x2d  disp12s   signed      (S+A-_SDA_BASE_)")

Relocation.new("R_ARC_SDA16_ST2     0x30  disp9s1   signed      (S+A-_SDA_BASE_)>>2 (Dsiambiguation for several relocations)")

# arcompact elf me reloc
Relocation.new("R_ARC_32_PCREL      0x31  word32    signed      S+A-PDATA")
Relocation.new("R_ARC_PC32          0x32  word32    signed      ME(S+A-P)")

# Special
Relocation.new("R_ARC_GOT32         0x3b  word32    dont        G+A") # == Special

# arcompact elf me reloc
Relocation.new("R_ARC_GOTPC32       0x33  word32    signed      ME(GOT+G+A-P)")
Relocation.new("R_ARC_PLT32         0x34  word32    signed      ME(L+A-P)")
Relocation.new("R_ARC_COPY          0x35  none      signed      none")
Relocation.new("R_ARC_GLOB_DAT      0x36  word32    signed      S")
Relocation.new("R_ARC_JMP_SLOT      0x37  word32    signed      ME(S)")
Relocation.new("R_ARC_RELATIVE      0x38  word32    signed      ME(B+A)")
Relocation.new("R_ARC_GOTOFF        0x39  word32    signed      ME(S+A-GOT)")
Relocation.new("R_ARC_GOTPC         0x3a  word32    signed      ME(GOT_BEGIN-P)")

Relocation.new("R_ARC_S21W_PCREL_PLT  0x3c  disp21w    signed      ME((L+A-P)>>2)")
Relocation.new("R_ARC_S25H_PCREL_PLT  0x3d  disp25h    signed      ME((L+A-P)>>1)")

# WITH TLS
Relocation.new("R_ARC_TLS_DTPMOD    0x42  word32    dont        0") # , 0, 2, 32, FALSE, 0, arcompact_elf_me_reloc, "R_ARC_TLS_DTPOFF",-1),
Relocation.new("R_ARC_TLS_TPOFF     0x44  word32    dont        0") # ,"R_ARC_TLS_TPOFF"),
Relocation.new("R_ARC_TLS_GD_GOT    0x45  word32    dont        ME(G+GOT-P)") # , 0, 2, 32, FALSE, 0, arcompact_elf_me_reloc, "R_ARC_TLS_GD_GOT",-1),
Relocation.new("R_ARC_TLS_GD_LD     0x46  none      dont        0") # ,"R_ARC_TLS_GD_LD"),
Relocation.new("R_ARC_TLS_GD_CALL   0x47  word32    dont        0") # ,"R_ARC_TLS_GD_CALL"),
Relocation.new("R_ARC_TLS_IE_GOT    0x48  word32    dont        ME(G+GOT-P)") # , 0, 2, 32, FALSE, 0, arcompact_elf_me_reloc, "R_ARC_TLS_IE_GOT",-1),
Relocation.new("R_ARC_TLS_DTPOFF    0x43  word32    dont        ME(S-SECTSTART+A)") # , 0, 2, 32, FALSE, 0, arcompact_elf_me_reloc, "R_ARC_TLS_DTPOFF",-1),
Relocation.new("R_ARC_TLS_DTPOFF_S9 0x49  word32    dont        ME(S-SECTSTART+A)") # , 0, 2, 32, FALSE, 0, arcompact_elf_me_reloc, "R_ARC_TLS_DTPOFF_S9",-1),
Relocation.new("R_ARC_TLS_LE_S9     0x4a  word32    dont        ME(S+TCB_SIZE-TLS_REL)") # , 0, 2, 9, FALSE, 0, arcompact_elf_me_reloc, "R_ARC_TLS_LE_S9",-1),
Relocation.new("R_ARC_TLS_LE_32     0x4b  word32    dont        ME(S+A+TCB_SIZE-TLS_REL)") # , 0, 2, 32, FALSE, 0, arcompact_elf_me_reloc, "R_ARC_TLS_LE_32",-1),
# WITHOUT TLS

Relocation.new("R_ARC_S25W_PCREL_PLT         0x4c  disp25w    signed      ME((L+A-P)>>2)")
Relocation.new("R_ARC_S21H_PCREL_PLT         0x4d  disp21h    signed      ME((L+A-P)>>1)")   
```


# <a name=dwarf></a>DWARF

Dwarf Register Numbers <a name=dwarf-register-numbers>
-------------------------------------------------------------------------
Dwarf Number  | Register Name | Description
--------------|---------------|-----------------------------------------

<!-- below from mwdt //dwarc/TechPubs/UserDocs/Source/4091_ARCv3_ABI/RST/source/load_link.rst#2 -->
Program Loading and Dynamic Linking {#load_link}
===================================

This section discusses loading and linking requirements for ARCv3-based
processors that support UNIX-style operating systems, including Linux.

Program Loading
---------------

As the system creates or augments a process image, it logically copies a
file\'s segment to a virtual memory segment. When and if the system
physically reads the file depends on the program\'s execution behavior,
system load, and so on. A process does not require a physical page
unless it references the logical page during execution, and processes
commonly leave many pages unreferenced. Therefore, delaying physical
reads frequently obviates them, improving system performance. To obtain
this efficiency in practice, executable and shared object files must
have segment images with offsets and virtual addresses that are
congruent, modulo the page size.

Virtual addresses and file offsets for segments in ARCv3-based
processors are congruent modulo 64 K bytes (0x10000) or larger powers of
two. Because 64 K bytes is the maximum page size, the files are suitable
for paging regardless of physical page size.

The value of the p\_align member of each program header in a shared
object file must be 0x10000.

`exe_file_layout`{.interpreted-text role="numref"} is an example of an
executable file assuming an executable program linked with a base
address of 0x10000000.

> Executable File Layout

The following are possible corresponding program header segments:

  -----------------------------------------------------------------------------------------------------------------------------
  **Member**                                **text**                                  **Data**
  ----------------------------------------- ----------------------------------------- -----------------------------------------
  p\_type                                   PT\_LOAD                                  PT\_LOAD

  p\_offset                                 0x100                                     0x2bf00

  p\_vaddr                                  0x10000100                                0x1003bf00

  p\_paddr                                  unspecified                               unspecified

  p\_filesz                                 0x2be00                                   0x4e00

  p\_memsz                                  0x2be00                                   0x5e24

  p\_flags                                  PF\_R+PF\_X                               PF\_R+PF\_W

  p\_align                                  0x10000                                   0x10000
  -----------------------------------------------------------------------------------------------------------------------------

  : Special Section Description

Although the file offsets and virtual addresses are congruent modulo
64,000 bytes, the beginning and end file pages of each segment group can
be impure. No restriction applies to the number or order of the segment
groups, but ELF files traditionally contain one code group followed by
one data group. For such a traditional single text and data file, up to
four file pages can hold impure text or data (depending on the page size
and file system block size).

> -   The first text page usually contains the ELF header, and other
>     information.
> -   The last text page typically contains a copy of the beginning of
>     data.
> -   The first data page usually contains a copy of the end of text.
> -   The last data page typically contains file information not
>     relevant to the running process.

Logically, the system enforces memory permissions as if each segment
were complete and separate; segment addresses are adjusted to ensure
that each logical page in the address space has a single set of
permissions. In Figure 4-1, the file region holding the end of text and
the beginning of data is mapped twice; at one virtual address for text
and at a different virtual address for data.

The end of a data segment requires special handling if it is followed
contiguously by the uninitialized data (.bss), which is required to be
initialized at startup with zeros. So if the last page of a file's
representation of a data segment includes information that is not part
of the segment, the extraneous data must be set to zero, rather than to
the unknown contents. "Impurities" in the other start and end pages are
not logically part of the process image; whether the system expunges
them is unspecified. The memory image for the program above is shown
here, assuming pages with a size of 4096 (0x1000) bytes.

![Virtual Address](../images/virtual_addr.png){.align-center}

One aspect of segment loading differs between executable files and
shared objects. Executable file segments may contain absolute code. For
the process to execute correctly, the segments must reside at the
virtual addresses assigned when building the executable file, with the
system using the p\_vaddr values unchanged as virtual addresses.

However, shared object segments typically contain position-independent
code. This allows a segment\'s virtual address to change from one
process to another, without invalidating execution behavior. Though the
system chooses virtual addresses for individual processes, it maintains
the relative positions of the segments. The difference between virtual
addresses in memory must match the difference between virtual addresses
in the file.

`virt_addr_assign`{.interpreted-text role="numref"} shows the
virtual-address assignments for shared objects that are possible for
several processes, illustrating constant relative positioning. The table
also illustrates the base-address computations.

>   **source**   **text**   **Data**   **Base Address**
>   ------------ ---------- ---------- ------------------
>   File         0x000200   0x02a400   ---
>   Process1     0x100200   0x12a400   0x100000
>   Process2     0x200200   0x22a400   0x200000
>   Process3     0x300200   0x32a400   0x300000
>   Process4     0x400200   0x42a400   0x400000
>   Process1     0x100200   0x12a400   0x100000
>
### Program Interpreter

The standard program interpreter is /usr/lib/ld.so.1.

Dynamic Linking
---------------

### Dynamic Section

Dynamic section entries give information to the dynamic linker. Some of
this information is processor-specific, including the interpretation of
some entries in the dynamic structure.

#### DT\_PLTGOT

The d\_ptr member for this entry gives the address of the first byte in
the procedure linkage table.

#### DT\_JMPREL

As explained in the System V ABI, this entry is associated with a table
of relocation entries for the procedure linkage table. For ARCv3-based
processors, this entry is mandatory both for executable and
shared-object files. Moreover, the relocation table\'s entries must have
a one-to-one correspondence with the procedure linkage table. The table
of DT\_JMPREL relocation entries is wholly contained within the DT\_RELA
referenced table. See "Procedure Linkage Table " for more information.

### Global Offset Table

Position-independent code generally may not contain absolute virtual
addresses. The global offset table (GOT) holds absolute addresses in
private data, making the addresses available without compromising the
position independence and sharability of a program\'s text. A program
references its GOT using position-independent addressing and extracts
absolute values, redirecting position-independent references to absolute
locations.

When the dynamic linker creates memory segments for a loadable object
file, it processes the relocation entries, some of which are of type
R\_ARC\_GLOB\_DAT, referring to the global offset table. The dynamic
linker determines the associated symbol values, calculates their
absolute addresses, and sets the GOT entries to the proper values.

Because the executable file and shared objects have separate global
offset tables, a symbol might appear in several tables. The dynamic
linker processes all the global offset table relocations before giving
control to any code in the process image, ensuring the absolute
addresses are available during execution.

The dynamic linker may choose different memory segment addresses for the
same shared object in different programs; it may even choose different
library addresses for different executions of the same program.
Nonetheless, memory segments do not change addresses after the process
image is established. As long as a process exists, its memory segments
reside at fixed virtual addresses.

The global offset table normally resides in the .got ELF section in an
executable or shared object. The symbol `_GLOBAL_OFFSET_TABLE_` can be
used to access the table. This symbol can reside in the middle of the
.got section, allowing both positive and negative subscripts into the
array of addresses.

The entry at `_GLOBAL_OFFSET_TABLE_[0]` is reserved for the address of
the dynamic structure, referenced with the symbol `_DYNAMIC`. This
allows the dynamic linker to find its dynamic structure prior to the
processing of the relocations.

The entry at `_GLOBAL_OFFSET_TABLE_[1]` is reserved for use by the
dynamic loader. The entry at `_GLOBAL_OFFSET_TABLE_[2]` is reserved to
contain a dynamic the lazy symbol-resolution entry point.

If no explicit .pltgot is used, `_GLOBAL_OFFSET_TABLE_[3 .. 3+F]` are
used for resolving function references, and
`_GLOBAL_OFFSET_TABLE_[3+F+1 .. last]` are for resolving data
references. Addressability to the global offset table (GOT) is
accomplished using direct PC-relative addressing. There is no need for a
function to materialize an explicit base pointer to access the GOT.
GOT-based variables can be referenced directly using a single eight-byte
long-intermediate-operand instruction:

``` {.}
ld rdest,[pcl,varname@gotpc]
```

Similarly, the address of the GOT can be computed relative to the PC:

``` {.}
add rdest,pcl, _GLOBAL_OFFSET_TABLE_ @gotpc
```

This add instruction relies on the universal placement of the address of
the \_DYNAMIC variable at location 0 of the GOT.

### Function Addresses

References to the address of a function from an executable file or
shared object and the shared objects associated with it might not
resolve to the same value. References from within shared objects are
normally resolved by the dynamic linker to the virtual address of the
function itself. References from within the executable file to a
function defined in a shared object are normally resolved by the link
editor to the address of the procedure linkage table entry for that
function within the executable file.

To allow comparisons of function addresses to work as expected, if an
executable file references a function defined in a shared object, the
link editor places the address of the PLT entry for that function in the
associated symbol-table entry. The dynamic linker treats such
symbol-table entries specially. If the dynamic linker is searching for a
symbol, and encounters a symbol-table entry for that symbol in the
executable file, it normally follows the rules below.

If the st\_shndx member of the symbol-table entry is not SHN\_UNDEF, the
dynamic linker has found a definition for the symbol and uses its
st\_value member as the symbol\'s address. If the st\_shndx member is
SHN\_UNDEF and the symbol is of type STT\_FUNC and the st\_value member
is not zero, the dynamic linker recognizes the entry as special and uses
the st\_value member as the symbol\'s address.

Otherwise, the dynamic linker considers the symbol to be undefined
within the executable file and continues processing.

Some relocations are associated with PLT entries. These entries are used
for direct function calls rather than for references to function
addresses. These relocations are not treated in the special way
described above because the dynamic linker must not redirect procedure
linkage table entries to point to themselves.

### Procedure Linkage Table

Procedure linkage tables (PLTs) are used to redirect function calls
between the executables and shared objects or between shared objects.

The PLT is designed to permit lazy or deferred symbol resolution at run
time, and to allow for dynamic run-time patching and upgrading of
library code.

Several PLT entries may exist for the same function, corresponding to
the calls and references from several different libraries, but for each
program there is exactly one dominant PLT entry per function, which
serves as the formal function address for the function. All pointer
comparisons use this PLT address when referencing the function. The
dominant PLT entry is the first PLT entry processed by the dynamic
linker. The dynamic linker resolves all subsequent references to the
function to this first address.

The PLT may be subsumed within the .got section, or divided into parts:
A read-only executable part (.plt) The .plt portion of a PLT in such an
arrangement consists of an array of 12-byte entries, one entry for each
function requiring PLT linkage. A read-write data part (.pltgot) The
.pltgot portion is a subsection of the GOT table and contains one
four-byte address per PLT entry. The purpose of a .pltgot is to isolate
the PLT-specific .got entries from the rest of the .got; in this
arrangement, no part of the .got is ever marked read only. If a PLT
entry is required by the operating system, a static linker may generate
a fixed sequence of code in the read-only part of the PLT that loads the
address and jumps to it.

The following example lists a permissible assembly-language definition
of a PLT entry.

::: {.admonition .\"admonition .tip\"}
Example: PLT Entry in ARCv3 Assembly Language

``` {.}
ld %r12,[%pcl,func@gotpc]
j [%r12]
mov %r12,%pcl
```
:::

This PLT entry sequence occupies 16 bytes of storage. In the preceding
example, `func@gotpc` represents the PC-relative offset of the location
in the GOT (or PLTGOT) that contains the actual address of the function
or the address of the code stub that transfers control to the dynamic
linker.

When executed, the PLT code loads the actual address of the function
into r12 from the GOT. It then jumps through r12 to its destination. As
it jumps, the delay-slot instruction loads r12 with the current value of
the 32-bit-aligned PC address for identification. The PLT-entry PC
address identifies the function called by allowing the lazy loader to
calculate the index into the PLT, which also corresponds to the index of
the relocation in the .rela.plt relocation section. The writable GOT or
PLTGOT entry is initialized by the dynamic linker when the object is
first loaded into memory. At first it is initialized to the special code
stub that saves the volatile registers and calls the dynamic linker. The
first time the function is called, the dynamic linker loads, links, and
resolves the GOT or PLTGOT entry to point to the actual loaded function
for subsequent calls.

The first entry in the PLT is reserved and is used as a reference to
transfer control to the dynamic linker. At program load time, each GOT
or PLTGOT entry is set to PLT\[0\], which is a hard-coded jump to the
dynamic-link stub routine.

The code residing at the beginning of the PLT occupies 24 bytes of
storage. The code is the equivalent of the following:

``` {.}
ld r11, [pcl, (GOT+4)@gotpc] ; module info stored by dynamic loader
ld r10, [pcl, (GOT+8)@gotpc] ; dynamic loader entry point
j [r10]
```

A relocation table (.rela.plt) is associated with the PLT. The
DT\_JMPREL entry in the dynamic section gives the location of the first
relocation entry. The relocation table\'s entries parallel the PLT
entries in a one-to-one correspondence. That is, relocation table entry
1 applies to PLT entry 1, and so on. The relocation type for each entry
is R\_ARC\_JMP\_SLOT. The relocation offset shall specify the address of
the GOT or PLTGOT entry associated with the function, and the symbol
table index shall reference the function\'s symbol in the .dynsym symbol
table. The dynamic linker locates the symbol referenced by the
R\_ARC\_JMP\_SLOT relocation. The value of the symbol is the address of
the first instruction of the function\'s PLT entry.

The dynamic linker can resolve the procedure linkage table relocations
lazily, resolving them only when they are needed. Doing so might reduce
program startup time. The LD\_BIND\_NOW environment variable can change
dynamic linking behavior. If its value is non-null, the dynamic linker
resolves the function call binding at load time, before transferring
control to the program. That is, the dynamic linker processes relocation
entries of type R\_ARC\_JMP\_SLOT during process initialization.
Otherwise, the dynamic linker evaluates procedure linkage table entries
lazily, delaying symbol resolution and relocation until the first
execution of a table entry.

Lazy binding generally improves overall application performance because
unused symbols do not incur the dynamic-linking overhead. Nevertheless,
some situations make lazy binding undesirable for some applications: The
initial reference to a shared object function takes longer than
subsequent calls because the dynamic linker intercepts the call to
resolve the symbol, and some applications cannot tolerate such
unpredictability.

If an error occurs and the dynamic linker cannot resolve the symbol, the
dynamic linker terminates the program. Under lazy binding, this might
occur at arbitrary times. Some applications cannot tolerate such
unpredictability. By turning off lazy binding, the dynamic linker forces
the failure to occur during process initialization, before the
application receives control.
