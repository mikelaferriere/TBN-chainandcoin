//import '@testing-library/jest-dom/extend-expect';

global.fetch = jest.fn(() => Promise.resolve());

global.console = {
  log: jest.fn(), // console.log are ignored in tests

  // Keep native behaviour for other methods, use those to print out things in your own tests, not `console.log`
  error: jest.fn(),
  warn: jest.fn(),
  info: jest.fn(),
  debug: jest.fn(),
};
