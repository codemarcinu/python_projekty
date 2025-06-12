import type { Config } from '@sveltejs/kit';

const config: Config = {
  kit: {
    alias: {
      $lib: 'src/lib',
      $components: 'src/lib/components',
      $stores: 'src/lib/stores',
      $services: 'src/lib/services',
      $types: 'src/lib/types'
    }
  }
};

export default config; 