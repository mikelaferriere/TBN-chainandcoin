// jest.config.js
module.exports = {
  verbose: true,
  setupFiles: [],
  setupFilesAfterEnv: ['<rootDir>/.jest/setup.js'],
  moduleFileExtensions: ['js', 'ts', 'tsx'],
  moduleDirectories: [
    'node_modules',
    'src',
    'src/components',
    '.jest'
  ],
  moduleNameMapper: {
    "\\.(css|less|scss)$": "identity-obj-proxy"
  },
  modulePathIgnorePatterns: [
    "<rootDir>/dist/"
  ],
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
  },
  testRegex: '\\.test.(js|ts|tsx)$',
  transformIgnorePatterns: ['node_modules'],
  testPathIgnorePatterns: [
    '<rootDir>/.jest/setup.js',
  ],
  // This is the only part which you can keep
  // from the above linked tutorial's config:
  cacheDirectory: '.jest/cache',
};
