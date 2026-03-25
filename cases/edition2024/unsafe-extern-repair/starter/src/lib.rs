use std::ffi::c_char;

extern "C" {
    pub fn puts(message: *const c_char) -> i32;
}

pub fn puts_symbol_addr() -> usize {
    puts as usize
}
