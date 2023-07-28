<script>
  export let data;
  import Header from "./header.svelte";
</script>

<Header api={data.api} userPromise={data.user}/>

<h1>TooManyCards</h1>

<p>An overengineered Quizlet "replacement".</p>
