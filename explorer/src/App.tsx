import React from 'react';

import {
  Container
} from '@material-ui/core';

import './App.css';

const App: React.FC = (): JSX.Element => {
  return (
    <div className="App">
      <Container
        maxWidth="xl"
      >
        <div>learn react</div>
      </Container>
    </div>
  );
}

export default App;