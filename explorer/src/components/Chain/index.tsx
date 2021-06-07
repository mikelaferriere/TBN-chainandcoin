import React from 'react';

import {
  Container,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@material-ui/core';

import * as Blockchain from '../../blockchain';
import Block, {TBlock} from '../Block';

export interface TChain {
    chain: Array<string>
    length: number
}

const Chain: React.FC<TChain> = ({chain}): JSX.Element => {
    const [block, setBlock] = React.useState<TBlock | undefined>()

    const handleClick = (hash: string) => {
        Blockchain.getBlockByHash(hash).then(setBlock)
    }

    return (
        <Container
            maxWidth="xl"
        >
            <TableContainer>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>
                            </TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {chain.map((hash, idx) => {
                            return (
                                <TableRow
                                    key={idx}
                                    onClick={() => handleClick(hash)}
                                >
                                    <TableCell>{hash}</TableCell>
                                </TableRow>
                            )
                        })}
                        {block &&
                            <TableRow>
                                <TableCell>
                                    <Block {...block} />
                                </TableCell>
                            </TableRow>
                        }
                    </TableBody>
                </Table>
            </TableContainer>
        </Container>
    );
}

export default Chain;