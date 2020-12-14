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

<format-version: ‘A’>
	[<uint32: subsection-length>  <NTBS: vendor-name>
		[<file-tag: 0x01> <uint32: byte-size> <attribute>*
		| <section-tag: 0x02> <uint32: byte-size> <section-number>* 0 <attribute>*
		|<symbol-tag: 0x03> <uint32: byte-size> <symbol-number>* 0 <attribute>*
		]+
	]*

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



