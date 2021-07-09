# ARCv3 ELF ABI specification

## Table of Contents
1. [Low-Level System Information] (#low-level-sys-info)
	* [Processor Architecture] (#processor-architecture)
	* [Data Representation] (#data-representation)
2. [Register Convention](#register-convention)
	* [Integer Register Convention](#integer-register-convention)
	* [Floating-point Register Convention](#floating-point-register-convention)
3. [Procedure Calling Convention](#procedure-calling-convention)
	* [Integer Calling Convention](#integer-calling-convention)
	* [Hardware Floating-point Calling Convention](#hardware-floating-point-calling-convention)
	* [Default ABIs and C type sizes](#default-abis-and-c-type-sizes)
	* [va_list, va_start, and va_arg](#va-list-va-start-and-va-arg)
4. [ELF Object Files](#elf-object-file)
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
5. [DWARF](#dwarf)
	* [Dwarf Register Numbers](#dwarf-register-numbers)

## Copyright and license information

This ARCv3 ELF ABI specification document is

 &copy; 2020 Synopsys, Claudiu Zissulescu <claziss@synopsys.com>

# <a name=low-level-sys-info></a> Low-Level System Information
## <a name=processor-architecture></a> Processor Architecture

Programs intended to execute on ARCv3-based processors use the ARCv3
instruction set and the instruction encoding and semantics of the
architecture.

Assume that all instructions defined by the architecture are neither
privileged nor exist optionally and work as documented.

To conform to ARCv3 System V ABI, the processor must do the following:

*   implement the instructions of the architecture,
*   perform the specified operations,
*   produce the expected results.

The ABI neither places performance constraints on systems nor specifies
what instructions must be implemented in hardware. A software emulation
of the architecture can conform to the ABI.

:exclamation:  Caution

Some processors might support optional or additional instructions or
capabilities that do not conform to the ARCv3 ABI. Executing programs
that use such instructions or capabilities on hardware that does not
have the required additional capabilities results in undefined behavior.

## <a name=data-representation></a> Data Representation
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

### Data Layout in Memory

ARCv3-based processors access data memory using byte addresses and
generally require that all memory addresses be aligned as follows:

-   64-bit double-words are aligned to
    -   64-bit boundaries on ARC64.
    -   32-bit boundaries on ARC32.
-   32-bit words are aligned to 32-bit word boundaries.
-   16-bit halfwords are aligned to 16-bit halfword boundaries.

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
r58     | acc0         | The only accumulator   | No
r59     | N.A.         | Reserved               | No
r60     | lp_count     | Reserved               | -- (Unallocatable)
r61     | slimm        | Signed-extended LIMM   | -- (Unallocatable)
r62     | zlimm        | Zero-extended LIMM     | -- (Unallocatable)
r63     | pcl          | Program counter        | -- (Unallocatable)


In the standard ABI, procedures should not modify the integer register
Global/Thread Pointer (`gp`), because signal handlers may rely upon
their values.

The `pcl` register (`r63`) contains the four-byte-aligned value of the
program counter.

:memo: memo

The scratch registers are not preserved across function calls. When
calling an external function, the compiler assumes that registers r0
through r13 are trashed; and that or r14 through r30 are
preserved. The EV processors reserve r25.

:memo: AGU registers

Address-generation unit (AGU) registers are caller-saved scratch
registers. These registers exist on processors configured with DSP and
AGU extensions.

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
f8-f15  | f8-f15       | Temporary registers    | No
f16-f31 | f16-f31      | Callee saved registers | Yes*

*: Floating-point values in callee-saved registers are only preserved
 across calls if they are no larger than the width of a floating-point
 register in the targeted ABI. Therefore, these registers can always
 be considered temporaries if targeting the base integer calling
 convention.

:memo:

Many other configurations of the FPU registers are possible. To keep it
simple this table defines just the maximal configuration.

# <a name=procedure-calling-convention></a> Procedure Calling Convention
## <a name=integer-calling-convention></a> Integer Calling Convention

Argument Passing

- The base integer calling convention provides eight argument
  registers, r0-r7, the first four of which are also used to return
  values.  In builds with a reduced register set, the first four words
  are loaded into r0 to r3.

- The remaining arguments are passed by storing them into the stack
  immediately above the stack-pointer register.

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
the next alignment boundary. For example,

```C
struct
 {
  int x : 10;
  int y : 12;
 }
```

is a 32-bit type with `x` in bits 9-0, `y` in bits 21-10, and
bits 31-22 undefined.  By contrast,

```C
struct
 {
  short x : 10;
  short y : 12;
 }
```

is a 32-bit type with `x` in bits 9-0, `y` in bits 27-16, and
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

## <a name=hardware-floating-point-calling-convention></a> Hardware Floating-point Calling Convention

When the FPU is configured the ABI changes dramatically as floating
point values are passed in FPU registers rather than core registers.
This means the application must be compiled with runtime libraries that
were compiled similarly.

Argument passing:

- ARC32: The first eight words (32 bytes) of arguments are loaded into
  registers `r0` to `r7`. In builds with a reduced register set, the
  first four words are loaded into `r0` to `r3`.

- ARC64: The first eight double words (64 bytes) of arguments are
  loaded into registers `r0` to `r7`.

- The remaining arguments are passed by storing them into the stack
  immediately above the stack-pointer register.

- Floating point values are passed in `f0` to `f7` when the FPU is
  configured and the registers are wide enough for the specified type.

- Vectors of floating point types are passed in FPU registers when
  those vectors and floating point types are supported by the hardware
  configuration chosen. They are passed in `f0` to `f7`. After `f0` to
  `f7` are consumed, the remainder are passed on the stack as overflow
  parameters.

Functions return the following results:

 - Any scalar or pointer type that is 32 bits or less in size (char,
   short, int) is returned in `r0` (and type `long` when ARC32).

 - Eight-byte integers (long long, double, and float complex) are
   returned in `r0` and `r1` on ARC32 and just in `r0` on ARC64 (and
   type `long` is 64-bits and returned in just `r0` on ARC64).

 - Results of type complex double are returned in `r0` to `r3` on ARC32
   and `r0` and `r1` on ARC64 when no FPU is configured.

 - Results of type complex float are returned in `r0` and `r1` when no
   FPU is configured.

 - Results of all complex floating point types are returned in `f0` and
   `f1` when the FPU is configured and the floating-point element type
   is supported by that configuration.

 - Results of type struct are returned in a caller-supplied temporary
   variable whose address is passed in `r0`.  For such functions, the
   arguments are shifted so that they are passed in r1 and upwards.

NOTE: When structs (also unions, arrays, and vectors), are passed by
value they are passed in the core regisers until those core registers
are consumed, and the remainder are passed on the stack in the
argument-overflow area. It is very difficult to describe precisely.
The best practice is to create lots of examples and examine the
generated code.

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
    __fp16      |  2            |  2
    float       |  4            |  4
    double      |  8            |  8
    long double | 16            | 16

`char` is unsigned.  `wchar_t` is signed.  `wint_t` is unsigned.

`_Complex` types have the alignment and layout of a struct containing two
fields of the corresponding real type (`float`, `double`, or `long double`),
with the first field holding the real part and the second field holding
the imaginary part.

### Aggregates and Unions

Aggregates (structures, classes, and arrays) and unions assume the
alignment of their most strictly aligned component, that is, the
component with the largest alignment. The size of any object,
including aggregates, classes, and unions, is always a multiple of the
alignment of the object. Non-bitfield members always start on byte
boundaries. The size of a struct or class is the sum of the sizes of
its members, including alignment padding between members. The size of
a union is the size of its largest member, padded such that its size
is evenly divisible by its alignment. Enumerations can be mapped to
one, two, or four bytes, depending on their size. An array uses the
same alignment as its elements. Structure and union objects can be
packed or padded to meet size and alignment constraints:

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
Objects " see (#stormap)

:point_up: Examples

Structure smaller than a word:

```C
struct {
  char c;
};
```

No Padding:

```C
struct {
  char  c;
  char  d;
  short s;
  int   n;
};
```

Internal Padding:

```C
struct {
  char  c;
  short s;
};
```

Internal and Tail Padding:

``` {.c}
struct {
  char   c;
  double d;
  short  s;
};
```

Union Allocation:

```C
union {
  char  c;
  short s;
  int   j;
};
```

### <a name=stormap></a> Storage Mapping for Class Objects

C++ class objects must be mapped in accordance with the [GNU Itanium
ABI](http://mentorembedded.github.io/cxx-abi/abi.html)

### Bitfields

C/C++ struct and union definitions can have bitfields, defining
integral objects with a specified number of bits.

Bitfields are signed unless explicitly declared as unsigned. For
example, a four-bit field declared as int can hold values from -8 to
7.

`bitfield_types` shows the possible widths for bitfields, where w is
maximum width (in bits).

**Bit Field Type**       | **Max Width**      | **Range of Values**
			 | **(Bits)**         |
:------------------------|:-------------------|----------------------------
signed char              | 1 to 8             | -2<sup>(w-1)</sup> to 2<sup>(w-1)</sup>-1
char(default signedness) | 1 to 8             | 0 to 2^<sup>w</sup> - 1
unsigned char            | 1 to 8             | 0 to 2^<sup>w</sup> - 1
short                    | 1 to 16            | -2^<sup>(w-1)</sup> to 2^<sup>(w-1)</sup> - 1
unsigned short           | 1 to 16            | 0 to 2^<sup>(w-1)</sup> - 1
int                      | 1 to 32            | -2^<sup>(w-1)</sup> to 2^<sup>(w-1)</sup> - 1
long                     | 1 to 32/64         | -2^<sup>(w-1)</sup> to 2^<sup>(w-1)</sup> - 1
enum (unless signed values)| 1 to 32          | 2^<sup>(w-1)</sup> - 1
unsigned int             | 1 to 32            | 2^<sup>(w-1)</sup> - 1
unsigned long            | 1 to 32/64         | 2^<sup>(w-1)</sup> - 1
long long int            | 1 to 64            | -2^<sup>(w-1)</sup> to 2^<sup>(w-1)</sup> -1
unsigned long long int   | 1 to 64            | 0 to 2^<sup>(w-1)</sup> -1

Bitfields obey the same size and alignment rules as other structure
and union members, with the following additions:

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
	following code starts on byte 4 of the parent struct:
	`struct S { int A:8; long long B:60; }`

You can insert padding as needed to comply with these rules.

Unnamed bitfields of non-zero length do not affect the external
alignment. In all other respects, they behave the same as named
bitfields. An unnamed bitfield of zero length causes alignment to
occur at the next unit boundary, based on its type.

## <a name=va-list-va-start-and-va-arg></a> va_list, va_start, and va_arg

The `va_list` type is `void*`. A callee with variadic arguments is responsible
for copying the contents of registers used to pass variadic arguments to the
vararg save area, which must be contiguous with arguments passed on the stack.
The `va_start` macro initializes its `va_list` argument to point to the start
of the vararg save area.  The `va_arg` macro will increment its `va_list`
argument according to the size of the given type, taking into account the
rules about 2x64 aligned arguments being passed in "aligned" register pairs.

## <a name=stack-frame></a> Stack Frame

This section describes the layout of the stack frame and registers
that must be saved by the callee prolog code.

### The Stack-Pointer Register

The stack-pointer (sp) register always points to the lowest used
address of the most recently allocated stack frame. The value of sp is
a four-byte-aligned address on ARC32 and an eight-byte-aligned value
on ARC64.

The stack-pointer register is commonly used as a base register to
access stack-frame-based variables, which always have a positive
offset.  However, when alloca() is called, the stack-pointer register
might be arbitrarily decremented after the stack frame is
allocated. In such a case, the frame pointer register is used to
reference stack-frame-based variables.

### The Frame-Pointer Register

The frame pointer register (fp) is used when a function calls alloca()
to allocate space on the stack, and stack-frame-based variables must be
accessed.

### The Callee's Prolog Code

The callee's prolog code saves all registers that need to be saved.
Saved values include the value of the caller's frame-pointer register,
`blink` (return address) register, callee-saved registers used by the
function.

:memo: Note

`fp` and `blink` are saved next to each other when both require
saving.  Secondly, only the order in which `fp` and `blink` are saved
is specified by the ABI. The debugger can properly display stack
frames with proper CFA directives no matter the order in which the
registers are saved (the same currently applies to C++ exception
unwinding).

The caller's stack-pointer (sp) register does not need to be saved
because the compiler is able to restore the stack pointer for each
function to its original value (for example, by using an add
instruction).

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

Dynamic stack allocations such as alloca insert data after local
variables.  The stack frame must be maintained using the frame pointer
(`fp`) instead of the stack pointer (`sp`).

# <a name=elf-object-file></a> ELF Object Files

## <a name=file-header></a> File Header

* e_ident
  * EI_CLASS: Specifies the base ISA:
    * ELFCLASS64: ELF-64 Object File
    * ELFCLASS32: ELF-32 Object File
  * EI_DATA:
    * ELFDATA2LSB: If execution environment is little-endian
    * ELFDATA2LSB: If execution environment is little-endian

* e_type: Nothing ARCv3 specific.

* e_machine: Identifies the machine this ELF file targets. Always contains:
  * EM_ARC_COMPACT3_64 (253 - 0xfd) for Synopsys ARCv3 64-bit
  * EM_ARC_COMPACT3 (255 - 0xff) for Synopsys ARCv3 32-bit

* e_flags: Describes the format of this ELF file.  These flags are used by the
  linker to disallow linking ELF files with incompatible ABIs together.

The high bits are used to select the Linux OSABI:

:------|:------------|:-----------------------------
0x000  |OSABI\_ORIG  |v2.6.35 kernel (sourceforge)
0x200  |OSABI\_V2    |v3.2 kernel (sourceforge)
0x300  |OSABI\_V3    |v3.9 kernel (sourceforge)
0x400  |OSABI\_V4    |v24.8 kernel (sourceforge)
-------|-------------|------------------------------

## <a name=sections></a>Sections

### Special Sections: Types and Attributes

The sections listed are used by the system and have the types and
attributes shown.

*Name*             |*Type*         |*Attributes*
:------------------|:--------------|:-----------------------
.arcextmap         |SHT\_PROGBITS  |none
.bss               |SHT\_NOBITS    |SHF\_ALLOC + SHF\_WRITE
.ctors             |SHT\_PROGBITS  |SHF\_ALLOC
.data              |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_WRITE
.fixtable          |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_WRITE
.heap              |SHT\_NOBITS    |SHF\_ALLOC + SHF\_WRITE
.initdata          |SHT\_PROGBITS  |SHF\_ALLOC
.offsetTable       |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_OVERLAY\_OFFSET\_TABLE + SHF\_INCLUDE
.overlay           |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_EXECINSTR + SHF\_OVERLAY + SHF\_INCLUDE
.overlayMultiLists |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_INCLUDE
.pictable          |SHT\_PROGBITS  |SHF\_ALLOC
.rodata\_in\_data  |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_WRITE
.sbss              |SHT\_NOBITS    |SHF\_ALLOC + SHF\_WRITE
.sdata             |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_WRITE
.stack             |SHT\_NOBITS    |SHF\_ALLOC + SHF\_WRITE
.text              |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_EXECINST
.tls               |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_WRITE
.ucdata            |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_WRITE
.vectors           |SHT\_PROGBITS  |SHF\_ALLOC + SHF\_EXECINST

To be compliant with the ARCv3 ABI, a system must support `.tls`,
`.sdata`, and `.sbss` sections, and must recognize, but may choose to
ignore, `.arcextmap` and `.stack` sections.

Special features might create additional sections. For details
regarding overlay-related sections see the *Automated Overlay Manager
User's Guide*.

* .arcextmap           Debugging information relating to processor extensions

* .bss                 Uninitialized variables that are not const-qualified
                       (startup code normally sets .bss to all zeros)

* .ctors               Contains an array of functions that are called at startup
                       to initialize elements such as C++ static variables

* .data                Static variables (local and global)

* .fixtable            Function replacement prologs

* .heap                Uninitialized memory used for the heap

* .initdata            Initialized variables and code (usually compressed) to be
                       copied into place during run-time startup

* .offsetTable         Overlay-offset table

* .overlay             All overlays defined in the executable

* .overlayMultiLists   Token lists for functions that appear in more than one
                       overlay group

* .pictable            Table for relocating pre-initialized data when generating
                       position-independent code and data

* .rodata\_in\_data    Read-only string constants when -Hharvard or -Hccm is
                       specified.

*.sbss                 Uninitialized data, set to all zeros by startup code and
                       directly accessible from the %gp register

* .sdata               Initialized small data, directly accessible from the %gp
                       register, and small uninitialized variables

*.stack                Stack information

*.text                 Executable code

*.tls                  Thread-local data

*.ucdata               Holds data accessed using cache bypass

*.vectors              Interrupt vector table

:exclamation:  Caution

Sections that contribute to a loadable program segment must not
contain overlapping virtual addresses.

## <a name=string-tables></a>String Tables

## <a name=symbol-table></a>Symbol Table

ARCv3-based processors that support the Linux operating system follow
the Linux conventions for dynamic linking.

### Small-Data Area

Programs may use a small-data area to reduce code size by storing
small variables in the `.sdata` and `.sbss` sections, where such data
can be addressed using small, signed offsets from the `gp`
register. If the program uses small data, program startup must
initialize the `gp` register to the address of symbol `_SDA_BASE_`
Such initialization is typically performed by the default startup
code.

### Register Information

The names and functions of the processor registers are described in
`regs`. Compilers may map variables to a register or registers as
needed in accordance with the rules described in `arg_pass` and
`ret_val`, including mapping multiple variables to a single register.

Compilers may place auto variables that are not mapped into registers at
fixed offsets within the function's stack frame as required, for example
to obtain the variable's address or if the variable is of an aggregate
type.

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

### Relocatable Fields

This document specifies several types of relocatable fields used by
relocations.

* bits8  Specifies 8 bits of data in a separate byte.

* bits16 Specifies 16 bits of data in a separate byte.

* bits24 Specifies 24 bits of data in a separate byte.

* disp7u Secifies a seven-bit unsigned displacement within a 16-bit
         instruction word, with bits 2-0 of the instruction stored in
         bits 2-0 and bits 6-3 of the instruction stored in bits 7-4.

* disp9 Specifies a nine-bit signed displacement within a 32-bit
        instruction word.

* disp9ls Specifies a nine-bit signed displacement within a 32-bit
        instruction word.

* disp9s Specifies a 9-bit signed displacement within a 16-bit
        instruction word.

* disp10u Specifies a 10-bit unsigned displacement within a 16-bit
  instruction word.

* disp13s Specifies a signed 13-bit displacement within a 16-bit
          instruction word. The displacement is to a 32-bit-aligned
          location and thus bits 0 and 1 of the displacement are not
          explicitly stored.

* disp21h Specifies a 21-bit signed displacement within a 32-bit
          instruction word. The displacement is to a halfword-aligned
          target location, and thus bit 0 of the displacement is not
          explicitly stored. Note that the 32-bit instruction
          containing this relocation field may be either
          16-bit-aligned or 32-bit-aligned.

* disp21w Specifies a signed 21-bit displacement within a 32-bit
          instruction word. The displacement is to a 32-bit-aligned
          target location, and thus bits 0 and 1 of the displacement
          are not explicitly stored. Note that the 32-bit instruction
          containing this relocation field may be either
          16-bit-aligned or 32-bit-aligned.

* disp25h Specifies a 25-bit signed displacement within a 32-bit
          instruction word. The displacement is to a halfword-aligned
          target location, and thus bit 0 is not explicitly
          stored. Note that the 32-bit instruction containing this
          relocation field may be either 16-bit-aligned or
          32-bit-aligned.

* disp25w Specifies a 25-bit signed displacement within a 32-bit
          instruction word. The displacement is to a 32-bit-aligned
          target location, and thus bits 0 and 1 are not explicitly
          stored. Note that the 32-bit instruction containing this
          relocation field may be either 16-bit-aligned or
          32-bit-aligned.

* disps9 Specifies a nine-bit signed displacement within a 16-bit
         instruction word. The displacement is to a 32-bit-aligned
         location, and thus bits 0 and 1 of the displacement are not
         explicitly stored. This means that effectively the field is
         bits 10-2, stored at 8-0.

* disps12 Specifies a twelve-bit signed displacement within a 32-bit
          instruction word. The high six bits are in 0-5, and the low
          six bits are in 6-11.

* word32 Specifies a 32-bit field occupying four bytes, the alignment
         of which is four bytes unless otherwise specified.

* word32me (Little-Endian) Specifies a 32-bit field in middle-endian
          Storage. Bits 31..16 are stored first, and bits 15..0 are
          stored adjacently. The individual halfwords are stored in
          the native endian orientation of the machine.

* word32me (Big-Endian) Specifies a 32-bit field in middle-endian
          Storage. Bits 31..16 are stored first, and bits 15..0 are
          stored adjacently. The individual halfwords are stored in
          the native endian orientation of the machine.

### Address Calculation Symbols

The following table provides details on the variables used in address
calculation:

Variable  | Description
:-------- | :----------------
A         | Addend field in the relocation entry associated with the symbol
B         | The base address at which a shared object has been loaded into memory during execution
S         | Base address of a shared object loaded into memory
G         | The offset into the global offset table at which the address of the relocated symbol will reside during execution
GOT       | Offset of the symbol into the GOT (Global Offset Table)
L         | The place (section offset or address) of the PLT entry for a symbol
MES       | Middle-Endian Storage
P         | The place (section offset or address) of the storage unit being relocated (computed using r\_offset).
S         | Value of the symbol in the symbol table
SECTSTART | Start of the current section. Used in calculating offset types.
\_SDA\_BASE | Base of the small-data area.
JLI       | Base of the JLI table.


A relocation entry\'s r\_offset value designates the offset or virtual
address of the first byte of the field to be relocated. The relocation
type specifies which bits to change and how to calculate their values.
The ARCv3 architecture uses only Elf32\_Rela relocation entries. The
addend is contained in the relocation entry. Any data from the field
to be relocated is discarded. In all cases, the addend and the
computed result use the same byte order.

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

```asm
ld rdest,[pcl,varname@gotpc]
```

Similarly, the address of the GOT can be computed relative to the PC:

```asm
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

### Linux
OS ABI consists of system calls provided by Linux kernel and call upon
by user space library code.

- ABI is similar to a regular function call in terms of arguments
  passing semantics. For example, 64-bit data in register pairs.

- Up to eight arguments allowed in registers `r0` to `r7`.

- Syscall number must be passed in register `r8`.

- Syscall return value is returned back in `r0`.

- All registers except `r0` are preserved by kernel across the Syscall.

The current Linux OS ABI (v4.8 kernel onwards) is ABIv4. For information
on the ABI versions, see
<https://github.com/foss-for-synopsys-dwc-arc-processors/linux/wiki/ARC-Linux-Syscall-ABI-Compatibility>


## <a name=dynamic-table></a>Dynamic Table

## <a name=hash-table></a>Hash Table

# <a name=dwarf></a>DWARF

Dwarf Register Numbers <a name=dwarf-register-numbers>
-------------------------------------------------------------------------
Dwarf Number  | Register Name | Description
--------------|---------------|-----------------------------------------
