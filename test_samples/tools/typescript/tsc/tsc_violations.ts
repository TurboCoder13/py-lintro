// tsc_violations.ts - Deliberate TypeScript type errors for testing

// Type mismatch: string assigned to number
const count: number = "hello";

// Missing return type annotation (implicit any in strict mode)
function greet(name: string) {
    return `Hello, ${name}`;
}

// Wrong argument type passed to function
function add(a: number, b: number): number {
    return a + b;
}
const result = add("1", "2");

// Property access on possibly undefined
interface User {
    name: string;
    email?: string;
}

function getEmailLength(user: User): number {
    return user.email.length;
}

// Type assertion that's incorrect
const value: unknown = "hello";
const num: number = value as number;
