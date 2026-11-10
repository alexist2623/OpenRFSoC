# Firmware

RISC-V bare-metal firmware will live here after the CPU and memory map are selected.
No CPU implementation, linker script or cross-compiler is selected by this bootstrap.
CPU selection must account for the existing 128-bit event enqueue operation. A
32-bit CPU needs an explicit staging/commit contract or another atomic enqueue path.
