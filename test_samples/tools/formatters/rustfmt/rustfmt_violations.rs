// This file contains formatting violations for rustfmt testing
// rustfmt will flag these issues when run with --check

fn main(){
    let x=1;
    let y=  2;
    let z    =3;

    // Bad spacing around operators
    let sum=x+y+z;

    // Missing spaces after commas
    let arr = [1,2,3,4,5];

    // Inconsistent indentation
  let poorly_indented = "text";
   let also_bad = "more text";

    // Long line that should be wrapped
    let very_long_variable_name_that_exceeds_reasonable_line_length = "this is a very long string that should probably be on its own line";

    println!("Sum: {}", sum);
}

// Badly formatted function signature
fn example_function(arg1:i32,arg2:i32,arg3:String)->i32{
    arg1+arg2
}

// Struct with bad formatting
struct BadlyFormattedStruct{field1:i32,field2:String,field3:bool}
