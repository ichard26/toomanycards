import adapter from '@sveltejs/adapter-node';
import preprocess from 'svelte-preprocess';

const config = {
    preprocess: preprocess(),
    kit: {
        // adapter-auto only supports some environments, see https://kit.svelte.dev/docs/adapter-auto for a list.
        // If your environment is not supported or you settled on a specific environment, switch out the adapter.
        // See https://kit.svelte.dev/docs/adapters for more information about adapters.
        adapter: adapter(),
        csp: {
            directives: {
                "default-src": ["self"],
                "style-src": ["self", "unsafe-inline"],
                "img-src": ["self", "ichard26.github.io"],
                "frame-src": ["none"],
                "frame-ancestors": ["none"],
                "upgrade-insecure-requests": true
            }
        }
    }
};

export default config;
