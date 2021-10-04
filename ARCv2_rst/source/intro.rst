.. raw:: latex


   \titleformat
   {\chapter} % command
   {\normalfont\bfseries\Huge} % format
   {\thechapter} % label
   {0.5ex} % sep
   {
     \vspace{1ex}
     \raggedleft
   } % before-code
   [
     \rule{\textwidth\color {violet}}{1pt}
   ]%aftercode

   \titleformat{\section}
   {\normalfont\bfseries\Large} % format
   {\thesection} % label
   {0.5ex} % sep
   {
     \vspace{1ex}
     \raggedright
   } % before-code

   \titleformat{\subsection}
   {\normalfont\bfseries} % format
   {\thesubsection} % label
   {0.5ex} % sep
   {
     \vspace{1ex}
     \raggedright
   } % before-code

   \renewcommand{\sfdefault}{phv}
   \listoftables

   \renewcommand{\sfdefault}{phv}
   \listoffigures
   
.. highlight:: none

Introduction
============

The *System V Application Binary Interface* defines a linking interface 
for compiled application programs. The interface is described in two 
parts: 

 - The first part is the generic System V ABI, shared across all 
   processor architectures. 

 - The second part is a processor specific supplement. 
 
This document is the processor specific supplement for use 
with ELF on processor systems based on the ARCv2 instruction-set 
architecture. 

This document is not a complete *System V Application 
Binary Interface Supplement*, because it does not define any OS 
library-interface information. Further, this ABI pertains primarily to 
C and assembly and contains only limited information on C++.

In the ARCv2 architecture, a processor can run in either of two modes: 
big-endian mode or little-endian mode. Programs and (in general) data 
produced by programs that run on an implementation of the big-endian 
interface are not portable to an implementation of the little-endian 
interface, and vice versa. An ARCv2 ABI-conforming system must support 
little-endian byte ordering. Accordingly, the ABI specification defines 
only the little-endian byte-ordering model. The ARCv2 ELF ABI is not the 
same as the preliminary ARC ABI published December 1999–April 2010.

.. note::
   This ABI does not specify software installation, media, and formats.

..
   
How to Use the System V ABI Supplement   
--------------------------------------

While the generic *System V ABI* is the prime reference document, this 
document contains ARCv2-specific implementation details, some of which 
supersede information in the generic ABI.

As with the System V ABI, this *Supplement* refers to other documents, 
especially the *ARCv2 Programmer's Reference Manual*, all of which should 
be considered part of this *ARCv2 ABI Supplement* and as binding as the 
requirements and data it explicitly includes.

Structure
~~~~~~~~~

This ABI Supplement consists of the following major divisions: 

Chapter 2, :ref:`low_lvl` describes the machine interface, byte ordering, 
data types, storage mapping, function calling sequence, registers, stack 
frame, function prolog and epilog, and function calls and branching.

Chapter 3, :ref:`obj_files` describes the ELF header, special sections, symbol 
table, small-data area, mapping variables to registers, and relocation types 
and fields.

Chapter 4, :ref:`load_link` is of interest to UNIX-style 
operating systems, and describes how programs are loaded and dynamically linked, 
including the global offset table and procedure linkage table. 

Terminology
~~~~~~~~~~~

.. glossary::
   :sorted:

   Callee-saved
      *Callee-saved registers* (sometimes called *non-volatile registers*) hold values 
      that are expected to be preserved across calls. 

   Caller-saved
      *Caller-saved registers* (sometimes called *volatile registers*) hold temporary 
      values that are not expected to be preserved across calls. 

   Word
      Thirty-two bits of data, unless otherwise specified.
..

Evolution of the ABI Specification
----------------------------------

Each new edition of *System V Application Binary Interface* is likely to 
contain extensions and additions that increases the potential capabilities 
of applications that are written to conform to the ABI.

Reference Documents
-------------------

 - *System V Interface Definition, Issue 3*

 - *DWARF Debugging Information Format*, Version 4, 2010, Free Standards Group, 
   DWARF Debugging Information Format Workgroup

 - *ARCv2 Programmer's Reference Manual* 

.. table:: Revision History
   :widths: 30, 20, 130
   
   +---------------+----------------+----------------------------------------+
   |  **Version**  |  **Date**      |  **Description**                       |
   +===============+================+========================================+
   | 4092-001      | July 2015      | Initial publication                    |
   +---------------+----------------+----------------------------------------+
   | 4092-002      | September 2015 | Added information on overlay-related   | 
   |               |                | sections                               |
   +---------------+----------------+----------------------------------------+
   | 4092-003      | December 2015  | - Added information on .vectors        |
   |               |                |   section                              |
   |               |                | - Specified that signed integral types | 
   |               |                |   are used by default for enums.       |
   +---------------+----------------+----------------------------------------+
   | 4092-004      | June 2016      | - Corrected :code:`dispu7` to          |
   |               |                |   :code:`disp7u` and documented the    |
   |               |                |   field.                               |
   |               |                | - Corrected :code:`disp10` field name  |
   |               |                |   to :code:`disp10u` and documented    | 
   |               |                |   the field.                           |
   |               |                | - Clarified that With the exception of |
   |               |                |   :code:`word32`, all relocations with |
   |               |                |   replacement fields in four-byte      |
   |               |                |   words must be written using Middle-  |
   |               |                |   Endian Storage.                      |
   |               |                | - Labeled :code:`word32` fields        |
   |               |                |   *word32me* when they are subject to  |
   |               |                |   middle-endian storage.               |
   |               |                | - Removed relocation type              |
   |               |                |   :code:`R_ARC_SPE_SECTOFF`            |
   |               |                | - Corrected calculations of relocation |
   |               |                |   types:                               |
   |               |                |                                        |
   |               |                |    - :code:`R_ARC_32_ME`               |
   |               |                |    - :code:`R_ARC_N32_ME`              |
   |               |                |    - :code:`R_AC_SECTOFF_S9`           |
   |               |                |    - :code:`R_AC_SECTOFF_S9_1`         |
   |               |                |    - :code:`R_AC_SECTOFF_S9_2`         |
   |               |                |                                        |   
   |               |                | - Corrected field type of              |
   |               |                |   :code:`R_ARC_AOM_TOKEN_ME` from      |
   |               |                |   :code:`limm` to :code:`word32me`     |
   |               |                | - Further clarified explanation of     |
   |               |                |   :code:`R_ARC_*_ME` relocation type   |
   |               |                | - Noted that the ninth bit of the      |
   |               |                |   replacement field is not used for    |
   |               |                |   the following relocation types:      |
   |               |                |                                        |   
   |               |                |    - :code:`R_AC_SECTOFF_U8`           |
   |               |                |    - :code:`R_AC_SECTOFF_U8_1`         |
   |               |                |    - :code:`R_AC_SECTOFF_U8_2`         |
   |               |                |                                        |
   |               |                | - Corrected various typographical      |
   |               |                |   errors.                              |
   +---------------+----------------+----------------------------------------+
   | 4092-005      | March 2018     | - Made the relocation displacement     |
   |               |                |   figures bit-exact.                   |
   |               |                | - Clarified that the :code:`LP_COUNT`, |
   |               |                |   :code:`r58`, and :code:`r59`         |
   |               |                |   registers are accumulators and       |
   |               |                |   caller-saved registers.              |
   |               |                | - Clarified that register :code:`r25`  |
   |               |                |   is reserved by the EV6x processors   |
   |               |                | - Clarified that the :code:`r30`       |
   |               |                |   register is used as a scratch        |
   |               |                |   register                             |
   |               |                | - Clarified that the :code:`r25`       |
   |               |                |   register is used for TLS by gcc      |
   |               |                | - Clarified that when calling an       |
   |               |                |   external function, the compiler      |
   |               |                |   assumes that registers :code:`r0`    |
   |               |                |   through :code:`r12` and :code:`r30`  |
   |               |                |   are trashed; and that :code:`r13`    |
   |               |                |   through r29 are preserved.           |
   |               |                | - Clarified that gcc reserves          |
   |               |                |   :code:`r25` as Thread pointer if     |
   |               |                |   Thread local storage is enabled.     |
   +---------------+----------------+----------------------------------------+
   | 4092-006      | September 2021 |   Correction: r25 is callee-saved.     |
   +---------------+----------------+----------------------------------------+
 
