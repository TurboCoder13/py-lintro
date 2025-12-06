// This file intentionally violates ESLint rules

// Unused variable
var unusedVar = 1;

// Missing semicolon
const noSemi = "test"

// Using var instead of let/const
var oldStyle = "bad"

// Unused function parameter
function unusedParam(param1, param2) {
  return param1;
}

// Console statement (often flagged in production code)
console.log("Debug statement");

// Equality operator instead of strict equality
if (noSemi == "test") {
  console.log("Using == instead of ===");
}

// Trailing comma issue (depends on ESLint config)
const obj = {
  key1: "value1",
  key2: "value2"
}

// Missing space before function parentheses (depends on ESLint config)
function noSpace(){
  return true;
}

// Unreachable code after return
function unreachable() {
  return true;
  console.log("This will never run");
}

// Duplicate key in object
const duplicate = {
  key: "value1",
  key: "value2"
}

// Using eval (security issue)
eval("console.log('bad')");

// Missing quotes consistency (depends on ESLint config)
const mixedQuotes = "single quotes preferred";

// No return statement in function that should return
function noReturn() {
  const x = 1;
}

