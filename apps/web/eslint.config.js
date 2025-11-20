import js from '@eslint/js'

export default [
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx,mjs,cjs}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    rules: {
      // Disable some strict rules for development
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      'no-undef': 'off', // TypeScript handles this
      'no-redeclare': 'off', // TypeScript handles this
    },
  },
  {
    // Ignore TypeScript files from ESLint since tsc handles them
    ignores: [
      'node_modules/**',
      '.next/**',
      'out/**',
      'dist/**',
      'build/**',
      '**/*.ts',
      '**/*.tsx',
      '**/*.config.js',
      '**/*.config.ts',
    ],
  },
]
