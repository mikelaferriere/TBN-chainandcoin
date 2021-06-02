import React from 'react';

import {
  Container,
} from '@material-ui/core';

import './App.css';

import Chain, {TChain} from './Chain';

import * as Blockchain from './blockchain';

const App: React.FC = (): JSX.Element => {
  const [chain, setChain] = React.useState<TChain>({chain: [], length: 0})

  React.useEffect(() => {
    Blockchain.getFullChain().then(setChain)
  }, [])

  return (
    <div className="App">
      <Container maxWidth="xl">
        <div>Choose your own adventure Coin</div>
        {chain && <Chain {...chain} />}
      </Container>
    </div>
  );
}

export default App;