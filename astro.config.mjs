// @ts-check
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import rehypeExternalLinks from 'rehype-external-links';
import { defineConfig } from 'astro/config';

export default defineConfig({
	site: 'https://gaichuunavi.com',
	integrations: [mdx(), sitemap()],
	output: 'static',
	markdown: {
		rehypePlugins: [
			[rehypeExternalLinks, { target: '_blank', rel: ['noopener', 'noreferrer'] }],
		],
	},
});
