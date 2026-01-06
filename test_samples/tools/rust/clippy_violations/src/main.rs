// Test file with various Clippy violations

fn main() {
    // clippy::needless_return
    println!("Hello, world!");
    call_functions();
    return;
}

fn call_functions() {
    // Call all functions to trigger clippy analysis
    unused_variable();
    needless_lifetimes();
    single_char_pattern();
    len_zero();
    redundant_clone();
    manual_range_contains();
    needless_borrow();
    explicit_counter();
    too_many_arguments();
    cast_possible_truncation();
    needless_pass_by_value();
    match_same_arms();
    collapsible_if();
    needless_bool();
    identity_op();
    suspicious_map_or();
    too_many_lines();
    cognitive_complexity();
    float_cmp();
    approx_constant();
}

fn unused_variable() {
    // clippy::unused_variable
    let x = 42;
}

fn needless_lifetimes() {
    // clippy::needless_lifetimes
    fn foo<'a>(s: &'a str) -> &'a str {
        s
    }
}

fn single_char_pattern() {
    // clippy::single_char_pattern
    let s = "hello world";
    let _ = s.split(" ");
}

fn len_zero() {
    // clippy::len_zero
    let v = vec![1, 2, 3];
    if v.len() == 0 {
        println!("empty");
    }
}

fn redundant_clone() {
    // clippy::redundant_clone
    let s = String::from("hello");
    let _ = s.clone();
}

fn manual_range_contains() {
    // clippy::manual_range_contains
    let x = 5;
    if x >= 0 && x < 10 {
        println!("in range");
    }
}

fn needless_borrow() {
    // clippy::needless_borrow
    let s = String::from("hello");
    let _ = &s;
}

fn explicit_counter() {
    // clippy::explicit_counter
    let mut i = 0;
    for _item in vec![1, 2, 3] {
        i += 1;
    }
}

fn too_many_arguments() {
    // clippy::too_many_arguments
    fn bad(a: i32, b: i32, c: i32, d: i32, e: i32, f: i32, g: i32, h: i32) {
        println!("too many args");
    }
}

fn cast_possible_truncation() {
    // clippy::cast_possible_truncation
    let x: u64 = 1000;
    let _: u32 = x as u32;
}

fn needless_pass_by_value() {
    // clippy::needless_pass_by_value
    fn takes_owned(s: String) {
        println!("{}", s);
    }
    let s = String::from("hello");
    takes_owned(s);
}

fn match_same_arms() {
    // clippy::match_same_arms
    let x = 5;
    match x {
        1 => println!("one"),
        2 => println!("one"),
        _ => println!("other"),
    }
}

fn collapsible_if() {
    // clippy::collapsible_if
    let x = 5;
    let y = 10;
    if x > 0 {
        if y > 0 {
            println!("both positive");
        }
    }
}

fn needless_bool() {
    // clippy::needless_bool
    let x = true;
    if x == true {
        println!("true");
    }
}

fn identity_op() {
    // clippy::identity_op
    let x = 5;
    let _ = x + 0;
    let _ = x * 1;
}

fn suspicious_map_or() {
    // clippy::suspicious_map_or
    let opt: Option<i32> = Some(5);
    let _ = opt.map(|x| x + 1).or(Some(0));
}

fn too_many_lines() {
    // clippy::too_many_lines
    fn long_function() {
        println!("line 1");
        println!("line 2");
        println!("line 3");
        println!("line 4");
        println!("line 5");
        println!("line 6");
        println!("line 7");
        println!("line 8");
        println!("line 9");
        println!("line 10");
        println!("line 11");
        println!("line 12");
        println!("line 13");
        println!("line 14");
        println!("line 15");
        println!("line 16");
        println!("line 17");
        println!("line 18");
        println!("line 19");
        println!("line 20");
        println!("line 21");
        println!("line 22");
        println!("line 23");
        println!("line 24");
        println!("line 25");
        println!("line 26");
        println!("line 27");
        println!("line 28");
        println!("line 29");
        println!("line 30");
        println!("line 31");
        println!("line 32");
        println!("line 33");
        println!("line 34");
        println!("line 35");
        println!("line 36");
        println!("line 37");
        println!("line 38");
        println!("line 39");
        println!("line 40");
        println!("line 41");
        println!("line 42");
        println!("line 43");
        println!("line 44");
        println!("line 45");
        println!("line 46");
        println!("line 47");
        println!("line 48");
        println!("line 49");
        println!("line 50");
        println!("line 51");
    }
}

fn cognitive_complexity() {
    // clippy::cognitive_complexity
    let x = 5;
    if x > 0 {
        if x > 1 {
            if x > 2 {
                if x > 3 {
                    if x > 4 {
                        if x > 5 {
                            if x > 6 {
                                if x > 7 {
                                    if x > 8 {
                                        if x > 9 {
                                            println!("deep");
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

fn float_cmp() {
    // clippy::float_cmp
    let x = 0.1 + 0.2;
    if x == 0.3 {
        println!("equal");
    }
}

fn approx_constant() {
    // clippy::approx_constant
    let pi = 3.14;
    let _ = pi;
}
