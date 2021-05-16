import React from 'react';

import {
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@material-ui/core';

export interface TChain {
    chain: Array<string>
    length: number
}

const Chain: React.FC<TChain> = ({chain}): JSX.Element => {
    const showBlockInformation = (c: string) => {
        console.log(c)
    }

    return (
        <Container
            maxWidth="xl"
        >
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Block Hash</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {chain.map((c, idx) => {
                            return (
                                <TableRow
                                    key={idx}
                                    onClick={() => showBlockInformation(c)}
                                >
                                    <TableCell>{c}</TableCell>
                                </TableRow>
                            )
                        })}
                    </TableBody>
                </Table>
            </TableContainer>
        </Container>
    );
}

export default Chain;