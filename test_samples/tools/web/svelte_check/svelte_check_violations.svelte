<script lang="ts">
    // svelte_check_violations.svelte - Deliberate Svelte type errors for testing

    // Type mismatch: string assigned to number
    let count: number = "hello";

    // Using undefined variable
    const message = undefinedVariable;

    // Type mismatch: assigning number (from add) to string-typed result
    function add(a: number, b: number): number {
        return a + b;
    }
    const result: string = add(1, 2);

    // Unused variable
    const unused: boolean = true;
</script>

<h1>{count}</h1>
<p>{message}</p>
<span>{result}</span>
