// Test file with Biome violations

// Unused variable
var unused = 1;

// Using == instead of ===
if (unused == 2) {
  // Console statement
  console.log("test");
}

// Using var instead of const/let
var oldStyle = "bad";

// Missing semicolon
const noSemi = "test"
