<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>


<script>
	let result = null;

	async function callApi() {
		const res = await fetch('http://localhost:8000/api/process', {
			method: 'POST'
		});
		result = await res.json();
	}
</script>

<h1>SpeakyDoc</h1>
<button on:click={callApi}>Run backend</button>

{#if result}
	<pre>{JSON.stringify(result, null, 2)}</pre>
{/if}