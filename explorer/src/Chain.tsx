import React from 'react';

import {
  Container
} from '@material-ui/core';

export interface TChain {
    chain: Array<string>
    length: number
}

const Chain: React.FC<TChain> = ({chain}): JSX.Element => {
    return (
        <Container
            maxWidth="xl"
        >
            {chain.map((c, idx) => {
                return <div key={idx}>{c}</div>
            })}
        </Container>
    );
}

export default Chain;