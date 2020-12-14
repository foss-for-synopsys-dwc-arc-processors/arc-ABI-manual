# ARC ABI addendum

## Build Attributes

Build attributes record data that a linker uses to determine the
compatibility, or incompatibility, of a set of relocatable
files. Other tools that consume relocatable files may also benefit
from the data. Build attributes are designed to reflect ARC CPU
configuration options defined in ARC Programmer Reference Manual.

The main uses of the attributes are to:

- ensure compatibility and/or check compatibility between two distinct
  tool chains, and
- within a toolchain, to allow the linker, assembler or disassembler
  to diagnose incompatibility, or enforce compatibility.

The attributes values are based on the user intentions at compile
time, which are also important at link time.

Build attributes are intended to check two types of compatibility:
- The compatibility of binary code with a target hardware configuration;
- The procedure-call compatibility between toolchains ABI variations.

Build attributes can be used to:
- Link two objects, one produced by GNU and the other produced by MWDT;
- Pass to the disassembler exactly the machine configuration we want to disassemble for;
- Pass to the assembler the exact machine the compiler compiled for;
- Pass to the simulator (ARC nSIM) the exact machine configuration;
- check the object attributes against the running machine when loading a dynamic module,.

## Representing build attributes in ELF files

### Encoding

Build attributes are encoded in a section of type
SHT_ARC_ATTRIBUTES (0x70000001), with a name of .ARC.attributes.

The content of the section is a stream of bytes. An attribute is
encoded in a <tag, value> pair. Both tags and numerical values are
encoded using unsigned LEB128 encoding (ULEB128), DWARF-3 style which
will allow values in the range 0-127. String values are encoded using
NULL-terminated byte strings (NTBS).

An attribute section contains a sequence of subsections. Each one is either:

- Defined by this ABI and public to all tools that process that
  file. This subsection is defined by the “ARC” pseudo-vector.
- Private to a tool vendor’s tools. This information may be safely
  ignored if it is not understood.

Attributes can apply to:
- A whole translation unit;
- A section
- A function (symbol of type STT_FUNC).

### Syntactic structure

The overall syntactic structure of an attribute section is:

```
<format-version: ‘A’>
	[<uint32: subsection-length>  <NTBS: vendor-name>
		[<file-tag: 0x01> <uint32: byte-size> <attribute>*
		| <section-tag: 0x02> <uint32: byte-size> <section-number>* 0 <attribute>*
		|<symbol-tag: 0x03> <uint32: byte-size> <symbol-number>* 0 <attribute>*
		]+
	]*
```

A public subsection contains any number of sub-subsections. Each
records attributes relating to:

- The whole relocatable file. These sub-subsections contain just a
  list of attributes. They are identified by a leading Tag_File (=1)
  byte.

- A set of sections within the relocatable file. These sub-subsections
  contain a list of ULEB128 section numbers followed by a list of
  attributes. They are identified by a leading Tag_Section (=2) byte.

- A set of (defined) symbols in the relocatable file. These
  sub-subsections contain a list of ULEB128 symbol numbers followed by
  a list of attributes. They are identified by a leading
  Tag_Symbol (=3) byte.

In each case, byte-size is a 4-byte unsigned integer in the byte order
of the ELF file. Byte-size includes the initial tag byte, the size
field itself, and the sub-subsection content. That is, it is the byte
offset from the start of this subsubsection to the start of the next
sub-subsection. Both section indexes and defined symbol indexes are
non-zero, so a NULL byte ends a string and a list of indexes without
ambiguity.

## Overview of public ARC attributes

Value | Tag | Visibility | Parameter type
------|-----|------------|----------------
4     | Tag_ARC_PCS_config | Public | uleb128
5     | Tag_ARC_CPU_base   | Public | uleb128
6     | Tag_ARC_CPU_variation | Public | uleb128
7     | Tag_ARC_CPU_name   | Public | NTBS
8     | Tag_ARC_ABI_rf16   | Public | uleb128
9     | Tag_ARC_ABI_osver  | Public | uleb128
10    | Tag_ARC_ABI_sda    | Public | uleb128
11    | Tag_ARC_ABI_pic    | Public | uleb128
12    | Tag_ARC_ABI_tls    | Public | uleb128
13    | Tag_ARC_ABI_enumsize | Public | uleb128
14    | Tag_ARC_ABI_exceptions | Public | uleb128
15    | Tag_ARC_ABI_double_size | Public | uleb128
16    | Tag_ARC_ISA_config | Public | NTBS
17    | Tag_ARC_ISA_apex | Public | NTBS
18    | Tag_ARC_ISA_mpy_option | Public | uleb128
19    | Tag_ARC_ISA_lpc_size | Public | uleb128
20    | Tag_ARC_ATR_version | Public | uleb128
21    | Tag_ARC_ABI_pack_struct | Public | uleb128

## ARC Platform configuration

### Tag_ARC_PCS_config

Defines the intended use of the produced object. This attribute is
required. An absent value will cause errors when linking with anything
else than absent/non standard.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
|4     | Tag_ARC_PCS_config | Default | 0 | Absent/Non standard
| ||| 1 | Bare-metal/mwdt
| ||| 2 | Bare-metal/newlib
| ||| 3 | Linux/uclibc
| ||| 4 | Linux/glibc

### Tag_ARC_CPU_base

Defines the intended target CPU. This attribute is mandatory. It can
be derived from .cpu pseudo op.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 5    | Tag_ARC_CPU_base | Default | 0 | Absent/legacy
| ||| 1 | ARC6xx
| ||| 2 | ARC7xx
| ||| 3 | ARCEM
| ||| 4 | ARCHS
| ||| 5 | ARC HS5x (32bit)
| ||| 6 |ARC HS6x (64bit)

### Tag_ARC_CPU_variation

Defines additional information to CPU_base. This attribute is optional
and can be omitted.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 6    | Tag_ARC_CPU_variation | Default | 0 | Absent/Default/Core0
| ||| 1-15 | Core1-Core14

### Tag_ARC_CPU_name

Defines name of the CPU, which can be the name of a specific
manufacturer, a generic name, or any other name. This attribute can be
omitted.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 7    | Tag_ARC_CPU_name | "" |  <NTBS> | CPU name

### Tag_ARC_ISA_config

Comma separated list of ISA extensions. This attribute is optional and
can be omitted. The names accepted are defined.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 16   | Tag_ARC_ISA_config | "" |  <NTBS> | Comma separated list of ISA extensions.

Recognized ISA name extensions

Name | Extension
-----|-----------
BITSCAN | Bit scan
BS | Barrel shifter
SWAP | Swap ops
DIV_REM | Division/remainder
NPS400 | NPS400
CD | Code density
QUARKSE | QuarkSE-EM
SPFP | FPX single precision
DPFP | FPX double precision
FPUDA | FP double assist
FPUS | FPU single precision
FPUD | FPU double precision
SA | Shift assist
LL64 | Double store/load

### Tag_ARC_ISA_apex

Defines list of APEX extensions present. This attribute is optional
and can be omitted.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 17   | Tag_ARC_ISA_apex | "" | <NTBS> | Comma separated list of APEX extensions.

### Tag_ARC_ISA_mpy_option

Defines MPY configuration option. This attribute is optional and can be omitted.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 18   | Tag_ARC_ISA_mpy_option | 0 | any | MPY configuration.


### Tag_ARC_ISA_lpc_size

Defines the number of bits in the LP_COUNT register. This attribute is
optional and can be omitted.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 19 | Tag_ARC_ISA_lpc_size | 32 | 8, 16, 24, 32 | Number of bits.

## ARC ABI related attributes

###  Tag_ARC_ABI_rf16

Indicates whether CPU has a reduced register set. This attribute is
mandatory. If not specified, Default value is assumed and selected.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 8 | Tag_ARC_ABI_rf16 | Default | 0 | Absent/Full register file
|||| 1 | Reduced register file

### Tag_ARC_ABI_osver

Defines ABI version.  This attribute also controls the corresponding
eflag value. This attribute is optional and can be omitted.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 9 | Tag_ARC_ABI_osver | 0 | Unset/Not available
|||| 1 | Reserved
|||| 2 | OSABI v2
|||| 3 | OSABI v3
||| Default | 4 | OSABI v4

### Tag_ARC_ABI_sda

Indicates whether small data implementation is present. This attribute
is mandatory. If not specified, Default value is assumed and selected.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 10 | Tag_ARC_ABI_sda | Default | 0 | Absent
|||| 1 | MWDT specific
|||| 2 | GNU specific

### Tag_ARC_ABI_pic

Indicates whether pic implementation is present. This attribute is
mandatory.. If not specified, Default value is assumed and selected.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 11 | Tag_ARC_ABI_pic | Default | 0 | Absent
|||| 1 | MWDT specific
|||| 2 | GNU specific

###  Tag_ARC_ABI_tls

Indicates whether R25 is used as Thread pointer or not. This attribute
is mandatory. If not specified Default value is assumed and selected.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 12 | Tag_ARC_ABI_tls | Default | 0 | Absent/not used
|||| n | Use Rn as thread pointer

### Tag_ARC_ABI_enumsize

Defines the enum size. This attribute is mandatory. If not specified,
Default value is assumed and selected.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 13 | Tag_ARC_ABI_enumsize | Default | 0 | Default/32-bit container
|||| 1 | Smallest container

### Tag_ARC_ABI_exceptions

Indicates whether libgcc OPTFP library is used or any other ABI
exception. This library uses a non-standard ABI calling convention
hence extra care is needed when linking. This attribute is
mandatory. If not specified Default value is assumed and selected.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 14 | Tag_ARC_ABI_exceptions | Default | 0 | Absent
|||| 1 | Libgcc OPTFP library

### Tag_ARC_ATR_version

Shows the attribute version. If set to 1 indicates the attribute
section is encoded using old MWDT encoding.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 20 | Tag_ARC_ATR_version | Default | 0 | Absent/GNU
|||| 1 | MWDT compatible

### Tag_ARC_ABI_pack_struct

Indicates the value used by GCC compatible option “-fpack-struct=n”
that defines the maximum alignment of struct memb ers. In addition, we
relax things so that if the user specifies 8, then 8-byte integers and
double are 8-byte aligned.

|Value | Attribute name | Default | Allowed Values | Meaning
|------|----------------|---------|----------------|--------
| 21 | Tag_ARC_ABI_pack_struct | Default | 0 | Absent
|||| n | Maximum alignment of struct members

## References
https://sourceware.org/binutils/docs/as/Object-Attributes.html#Object-Attributes
