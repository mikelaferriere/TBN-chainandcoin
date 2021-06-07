import React from 'react';

import { makeStyles } from '@material-ui/core/styles';

import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@material-ui/core';

import * as Blockchain from '../../blockchain';
import Transaction, {TTransaction} from '../Transaction';

interface THeader {
    version: number
    previous_hash: string
    transaction_merkle_root: string
    timestamp: Date
    difficulty: number
    nonce: number
}

export interface TBlock {
    index: number
    transaction_count: number
    transactions: string[]
    header: THeader
    block_hash: string
    size: number
}

const useStyles = makeStyles((theme) => ({
    root: {
        width: '100%',
    },
    heading: {
        fontSize: theme.typography.pxToRem(15),
        flexBasis: '33.33%',
        flexShrink: 0,
    },
    secondaryHeading: {
        fontSize: theme.typography.pxToRem(15),
        color: theme.palette.text.secondary,
    },
}));

const Block: React.FC<TBlock> = (
    {block_hash, transaction_count, transactions}
): JSX.Element => {
    const classes = useStyles();
    const [expanded, setExpanded] = React.useState<string |  boolean>(false);
    const [transaction, setTransaction] = React.useState<TTransaction | undefined>()

    const handleChange = (hash: string) => (_event, isExpanded: boolean) => {
        Blockchain.getTransactionByHash(hash).then(setTransaction)
        setExpanded(isExpanded ? hash : false);
    };

    return (
        <div className={classes.root}>
            <TableContainer>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Block Hash</TableCell>
                        <TableCell>Transaction Count</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    <TableRow>
                        <TableCell>{block_hash}</TableCell>
                        <TableCell>{transaction_count}</TableCell>
                    </TableRow>
                    <TableRow>
                        <TableCell colSpan={2}>Transactions</TableCell>
                    </TableRow>
                    <TableRow>
                        <TableCell colSpan={2}>
                            {transactions.map((t: string, idx: number) => {
                                return (
                                    <Accordion
                                        TransitionProps={{ unmountOnExit: true }}
                                        expanded={expanded === t}
                                        onChange={handleChange(t)}
                                        key={idx}
                                    >
                                        <AccordionSummary
                                            aria-controls={idx.toString() + "-content"}
                                            id={idx.toString()}
                                            key={idx}
                                        >
                                            <Typography className={classes.heading}>{t}</Typography>
                                        </AccordionSummary>
                                        <AccordionDetails>
                                            <Transaction transaction={transaction} />
                                        </AccordionDetails>
                                    </Accordion>
                                );
                            })}
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
            </TableContainer>
        </div>
    );
}

export default Block;