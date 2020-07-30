.. _load_link:

Program Loading and Dynamic Linking
===================================

This section discusses loading and linking requirements for 
ARCv2-based processors that support UNIX-style operating 
systems, including Linux.

Program Loading
---------------
 
As the system creates or augments a process image, it logically 
copies a file's segment to a virtual memory segment. When and if 
the system physically reads the file depends on the program's 
execution behavior, system load, and so on. A process does not 
require a physical page unless it references the logical page during 
execution, and processes commonly leave many pages unreferenced. 
Therefore, delaying physical reads frequently obviates them, 
improving system performance. To obtain this efficiency in practice, 
executable and shared object files must have segment images with 
offsets and virtual addresses that are congruent, modulo the page 
size.

Virtual addresses and file offsets for segments in ARCv2-based 
processors are congruent modulo 64 K bytes (0x10000) or larger powers 
of two. Because 64 K bytes is the maximum page size, the files are 
suitable for paging regardless of physical page size.

The value of the p_align member of each program header in a 
shared object file must be 0x10000.

:numref:`exe_file_layout` is an example of an executable file assuming 
an executable program linked with a base address of 0x10000000.

.. _exe_file_layout:
.. figure::  ../images/exe_file_layout.png
   :align: center
   
   Executable File Layout
..  

The following are possible corresponding program header segments:

.. table:: Special Section Description
   :widths: 40, 40, 40 
   
   ============  ============  ============
   **Member**    **text**      **Data** 
   ============  ============  ============
   p_type        PT_LOAD       PT_LOAD
   p_offset      0x100         0x2bf00
   p_vaddr       0x10000100    0x1003bf00
   p_paddr       unspecified   unspecified
   p_filesz      0x2be00       0x4e00
   p_memsz       0x2be00       0x5e24
   p_flags       PF_R+PF_X     PF_R+PF_W
   p_align       0x10000       0x10000
   ============  ============  ============
..

Although the file offsets and virtual addresses are congruent modulo 
64,000 bytes, the beginning and end file pages of each segment group 
can be impure. No restriction applies to the number or order of the 
segment groups, but ELF files traditionally contain one code group 
followed by one data group. For such a traditional single text and 
data file, up to four file pages can hold impure text or data 
(depending on the page size and file system block size).

   - The first text page usually contains the ELF header, and other 
     information.

   - The last text page typically contains a copy of the beginning 
     of data.

   - The first data page usually contains a copy of the end of text.

   - The last data page typically contains file information not 
     relevant to the running process.
   
Logically, the system enforces memory permissions as if each segment 
were complete and separate; segment addresses are adjusted to ensure 
that each logical page in the address space has a single set of permissions. 
In Figure 4-1, the file region holding the end of text and 
the beginning of data is mapped twice; at one virtual address for text
and at a different virtual address for data.
 
The end of a data segment requires special handling if it is followed 
contiguously by the uninitialized data (.bss), which is required to be 
initialized at startup with zeros. So if the last page of a file’s 
representation of a data segment includes information that is not part 
of the segment, the extraneous data must be set to zero, rather than to 
the unknown contents. “Impurities” in the other start and end pages are 
not logically part of the process image; whether the system expunges 
them is unspecified. The memory image for the program above is shown 
here, assuming pages with a size of 4096 (0x1000) bytes.  
 
.. figure::  ../images/virtual_addr.png
   :align: center
   
   Virtual Address 
..  

One aspect of segment loading differs between executable files and shared 
objects. Executable file segments may contain absolute code. For the process 
to execute correctly, the segments must reside at the virtual addresses 
assigned when building the executable file, with the system using the p_vaddr 
values unchanged as virtual addresses.

However, shared object segments typically contain position-independent code. 
This allows a segment's virtual address to change from one process to another, 
without invalidating execution behavior.
Though the system chooses virtual addresses for individual processes, it 
maintains the relative positions of the segments. The difference between virtual 
addresses in memory must match the difference between virtual addresses in the 
file.

:numref:`virt_addr_assign` shows the virtual-address assignments for shared objects that are 
possible for several processes, illustrating constant relative positioning. 
The table also illustrates the base-address computations.

.. _virt_addr_assign:
.. table:: Virtual Address Assignments
   :widths: 40, 40, 40, 40 
   
   ============  ============  ============  ================
   **source**    **text**      **Data**      **Base Address**
   ============  ============  ============  ================
   File          0x000200      0x02a400      —
   Process1      0x100200      0x12a400      0x100000
   Process2      0x200200      0x22a400      0x200000
   Process3      0x300200      0x32a400      0x300000
   Process4      0x400200      0x42a400      0x400000
   Process1      0x100200      0x12a400      0x100000
   ============  ============  ============  ================
..
 
Program Interpreter 
~~~~~~~~~~~~~~~~~~~

The standard program interpreter is /usr/lib/ld.so.1. 

Dynamic Linking 
---------------

Dynamic Section 
~~~~~~~~~~~~~~~

Dynamic section entries give information to the dynamic 
linker. Some of this information is processor-specific, 
including the interpretation of some entries in the dynamic 
structure.

DT_PLTGOT
^^^^^^^^^

The d_ptr member for this entry gives the address of the 
first byte in the procedure linkage table.


DT_JMPREL
^^^^^^^^^

As explained in the System V ABI, this entry is associated 
with a table of relocation entries for the procedure linkage 
table. For ARCv2-based processors, this entry is mandatory 
both for executable and shared-object files. Moreover, the 
relocation table's entries must have a one-to-one correspondence 
with the procedure linkage table. The table of DT_JMPREL 
relocation entries is wholly contained within the DT_RELA 
referenced table. See “Procedure Linkage Table ” for more 
information.

Global Offset Table
~~~~~~~~~~~~~~~~~~~
 
Position-independent code generally may not contain absolute virtual addresses. 
The global offset table (GOT) holds absolute addresses in private data, making 
the addresses available without compromising the position independence and 
sharability of a program's text. A program references its GOT using position-independent 
addressing and extracts absolute values, redirecting position-independent references 
to absolute locations.

When the dynamic linker creates memory segments for a loadable object file, it processes 
the relocation entries, some of which are of type R_ARC_GLOB_DAT, referring to the global 
offset table. The dynamic linker determines the associated symbol values, calculates their 
absolute addresses, and sets the GOT entries to the proper values.
 
Because the executable file and shared objects have separate global offset tables, a symbol 
might appear in several tables. The dynamic linker processes all the global offset table 
relocations before giving control to any code in the process image, ensuring the absolute 
addresses are available during execution.

The dynamic linker may choose different memory segment addresses for the same shared object 
in different programs; it may even choose different library addresses for different executions 
of the same program. Nonetheless, memory segments do not change addresses after the process 
image is established. As long as a process exists, its memory segments reside at fixed virtual 
addresses.

The global offset table normally resides in the .got ELF section in an executable or shared 
object. The symbol :code:`_GLOBAL_OFFSET_TABLE_` can be used to access the table. This symbol can 
reside in the middle of the .got section, allowing both positive and negative subscripts 
into the array of addresses.

The entry at :code:`_GLOBAL_OFFSET_TABLE_[0]` is reserved for the address of the dynamic structure, 
referenced with the symbol :code:`_DYNAMIC`. This allows the dynamic linker to find its dynamic 
structure prior to the processing of the relocations.

The entry at :code:`_GLOBAL_OFFSET_TABLE_[1]` is reserved for use by the dynamic loader. 
The entry at :code:`_GLOBAL_OFFSET_TABLE_[2]` is reserved to contain a dynamic the lazy 
symbol-resolution entry point.

If no explicit .pltgot is used, :code:`_GLOBAL_OFFSET_TABLE_[3 .. 3+F]` are used for resolving 
function references, and :code:`_GLOBAL_OFFSET_TABLE_[3+F+1 .. last]` are for resolving data 
references.
Addressability to the global offset table (GOT) is accomplished using direct PC-relative 
addressing. There is no need for a function to materialize an explicit base pointer to 
access the GOT. GOT-based variables can be referenced directly using a single eight-byte 
long-intermediate-operand instruction:

.. code:: 

   ld rdest,[pcl,varname@gotpc]
..

Similarly, the address of the GOT can be computed relative to the PC:

.. code::

   add rdest,pcl, _GLOBAL_OFFSET_TABLE_ @gotpc
..

This add instruction relies on the universal placement of the address of the \_DYNAMIC 
variable at location 0 of the GOT.

Function Addresses 
~~~~~~~~~~~~~~~~~~

References to the address of a function from an executable file or shared object and the 
shared objects associated with it might not resolve to the same value. References from 
within shared objects are normally resolved by the dynamic linker to the virtual address 
of the function itself. References from within the executable file to a function defined 
in a shared object are normally resolved by the link editor to the address of the procedure 
linkage table entry for that function within the executable file. 

To allow comparisons of function addresses to work as expected, if an executable file 
references a function defined in a shared object, the link editor places the address of 
the PLT entry for that function in the associated symbol-table entry. The dynamic linker 
treats such symbol-table entries specially. If the dynamic linker is searching for a 
symbol, and encounters a symbol-table entry for that symbol in the executable file, it 
normally follows the rules below. 

If the st_shndx member of the symbol-table entry is not SHN_UNDEF, the dynamic linker has 
found a definition for the symbol and uses its st_value member as the symbol's address. 
If the st_shndx member is SHN_UNDEF and the symbol is of type STT_FUNC and the st_value 
member is not zero, the dynamic linker recognizes the entry as special and uses the st_value 
member as the symbol's address. 

Otherwise, the dynamic linker considers the symbol to be undefined within the executable file 
and continues processing. 

Some relocations are associated with PLT entries. These entries are used for direct function 
calls rather than for references to function addresses. These relocations are not treated in 
the special way described above because the dynamic linker must not redirect procedure linkage 
table entries to point to themselves. 

Procedure Linkage Table 
~~~~~~~~~~~~~~~~~~~~~~~

Procedure linkage tables (PLTs) are used to redirect function calls between the executables and 
shared objects or between shared objects. 

The PLT is designed to permit lazy or deferred symbol resolution at run time, and to allow for 
dynamic run-time patching and upgrading of library code.

Several PLT entries may exist for the same function, corresponding to the calls and references 
from several different libraries, but for each program there is exactly one dominant PLT entry 
per function, which serves as the formal function address for the function. All pointer 
comparisons use this PLT address when referencing the function. The dominant PLT entry is the 
first PLT entry processed by the dynamic linker. The dynamic linker resolves all subsequent 
references to the function to this first address.

The PLT may be subsumed within the .got section, or divided into parts: 
A read-only executable part (.plt) 
The .plt portion of a PLT in such an arrangement consists of an array of 12-byte entries, one 
entry for each function requiring PLT linkage. 
A read-write data part (.pltgot)
The .pltgot portion is a subsection of the GOT table and contains one four-byte address per PLT 
entry. The purpose of a .pltgot is to isolate the PLT-specific .got entries from the rest of the 
.got; in this arrangement, no part of the .got is ever marked read only. If a PLT entry is required 
by the operating system, a static linker may generate a fixed sequence of code in the read-only 
part of the PLT that loads the address and jumps to it. 

The following example lists a permissible assembly-language definition of a PLT entry.

.. admonition:: Example: PLT Entry in ARCv2 Assembly Language 
   :class: "admonition tip"

   .. code::
   
      ld %r12,[%pcl,func@gotpc]
      j [%r12]
      mov %r12,%pcl
   ..	 
..

This PLT entry sequence occupies 16 bytes of storage.
In the preceding example, :code:`func@gotpc` represents the PC-relative offset of the location in the GOT (or PLTGOT) 
that contains the actual address of the function or the address of the code stub that transfers 
control to the dynamic linker.

When executed, the PLT code loads the actual address of the function into r12 from the GOT. It then 
jumps through r12 to its destination. As it jumps, the delay-slot instruction loads r12 with the 
current value of the 32-bit-aligned PC address for identification. The PLT-entry PC address identifies 
the function called by allowing the lazy loader to calculate the index into the PLT, which also 
corresponds to the index of the relocation in the .rela.plt relocation section. 
The writable GOT or PLTGOT entry is initialized by the dynamic linker when the object is first loaded 
into memory. At first it is initialized to the special code stub that saves the volatile registers 
and calls the dynamic linker. The first time the function is called, the dynamic linker loads, links, 
and resolves the GOT or PLTGOT entry to point to the actual loaded function for subsequent calls.

The first entry in the PLT is reserved and is used as a reference to transfer control to the dynamic 
linker. At program load time, each GOT or PLTGOT entry is set to PLT[0], which is a hard-coded jump 
to the dynamic-link stub routine.
 
The code residing at the beginning of the PLT occupies 24 bytes of storage. The code is the equivalent 
of the following:

.. code::

   ld r11, [pcl, (GOT+4)@gotpc] ; module info stored by dynamic loader
   ld r10, [pcl, (GOT+8)@gotpc] ; dynamic loader entry point
   j [r10]
..


A relocation table (.rela.plt) is associated with the PLT. The DT_JMPREL entry in the dynamic section 
gives the location of the first relocation entry. The relocation table's entries parallel the PLT 
entries in a one-to-one correspondence. That is, relocation table entry 1 applies to PLT entry 1, and 
so on. The relocation type for each entry is R_ARC_JMP_SLOT. The relocation offset shall specify the 
address of the GOT or PLTGOT entry associated with the function, and the symbol table index shall 
reference the function's symbol in the .dynsym symbol table. The dynamic linker locates the symbol 
referenced by the R_ARC_JMP_SLOT relocation. The value of the symbol is the address of the first 
instruction of the function's PLT entry. 

The dynamic linker can resolve the procedure linkage table relocations lazily, resolving them only 
when they are needed. Doing so might reduce program startup time.
The LD_BIND_NOW environment variable can change dynamic linking behavior. If its value is non-null, 
the dynamic linker resolves the function call binding at load time, before transferring control to 
the program. That is, the dynamic linker processes relocation entries of type R_ARC_JMP_SLOT during 
process initialization. Otherwise, the dynamic linker evaluates procedure linkage table entries lazily, 
delaying symbol resolution and relocation until the first execution of a table entry.

Lazy binding generally improves overall application performance because unused symbols do not incur the 
dynamic-linking overhead. Nevertheless, some situations make lazy binding undesirable for some applications:
The initial reference to a shared object function takes longer than subsequent calls because the dynamic 
linker intercepts the call to resolve the symbol, and some applications cannot tolerate such unpredictability.

If an error occurs and the dynamic linker cannot resolve the symbol, the dynamic linker terminates the 
program. Under lazy binding, this might occur at arbitrary times. Some applications cannot tolerate such 
unpredictability. By turning off lazy binding, the dynamic linker forces the failure to occur during 
process initialization, before the application receives control. 
































   
