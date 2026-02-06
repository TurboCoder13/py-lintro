<script lang="ts">
    // svelte_check_clean.svelte - Valid Svelte code without type errors

    let count: number = 0;
    let message: string = "Welcome to Svelte";

    function add(a: number, b: number): number {
        return a + b;
    }

    const result: number = add(1, 2);

    function increment(): void {
        count += 1;
    }
</script>

<h1>{message}</h1>
<p>Count: {count}</p>
<p>Result: {result}</p>
<button on:click={increment}>Increment</button>
