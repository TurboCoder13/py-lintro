// This file intentionally violates Prettier rules
function foo() {
    console.log("Hello, world!");  // Double quotes instead of single quotes
    let arr = [1,2,3];  // Missing spaces after commas
    return {a: 1, b: 2};  // Missing spaces after colons and missing trailing comma
}

foo()  // Missing semicolon

// Long line that exceeds printWidth of 100 characters
const veryLongVariableNameThatExceedsTheMaximumLineLengthAndShouldTriggerAPrettierViolation = "this is a very long string that makes the line too long";

// Inconsistent indentation
function bar() {
  console.log("inconsistent indentation");  // 2 spaces instead of consistent indentation
    console.log("more inconsistent indentation");  // 4 spaces
}

// Object with missing trailing comma
const obj = {
    name: "test",
    value: 123  // Missing trailing comma
};

// More violations
const badArray = [1,2,3,4,5];  // Missing spaces after commas
const badObject = {key1:"value1",key2:"value2"};  // Missing spaces after colons and commas

function badFunction(param1,param2,param3) {  // Missing spaces after commas
    if(param1===param2) {  // Missing spaces around operators
        return true;
    }
    return false;
}

// Inconsistent quote usage
const mixedQuotes = "This uses double quotes";
const anotherString = 'This uses single quotes';

// Bad spacing in function calls
console.log("test");
console.log( "test" );  // Extra spaces
console.log("test" );  // Extra space after
