import React from 'react';

import {
  Container,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@material-ui/core';

import * as Blockchain from './blockchain';

interface THeader {
    version: number
    previous_hash: string
    transaction_merkle_root: string
    timestamp: Date
    difficulty: number
    nonce: number
}

interface TTransactionData {
    sender: string
    recipient: string
    amount: number
    nonce: number
    timestamp: Date
    public_key: string
}

interface TSignedTransaction {
    details: TTransactionData
    signature: string
}

export interface TTransaction {
    transaction_hash: string
    transaction_id: string
    signed_transaction: TSignedTransaction
}

export interface TBlock {
    index: number
    transaction_count: number
    transactions: string[]
    header: THeader
    block_hash: string
    size: number
}

export interface TChain {
    chain: Array<string>
    length: number
}

const Transaction: React.FC<TTransaction> = (t): JSX.Element => {
    return <TableContainer>
        <Table>
            <TableHead>
                <TableRow>
                    <TableCell>Transaction Hash</TableCell>
                    <TableCell>Sender</TableCell>
                    <TableCell>Recipient</TableCell>
                    <TableCell>Amount</TableCell>
                    <TableCell>Timestamp</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                <TableRow>
                    <TableCell>{t.transaction_hash}</TableCell>
                    <TableCell>{t.signed_transaction.details.sender}</TableCell>
                    <TableCell>{t.signed_transaction.details.recipient}</TableCell>
                    <TableCell>{t.signed_transaction.details.amount}</TableCell>
                    <TableCell>{t.signed_transaction.details.timestamp}</TableCell>
                </TableRow>
            </TableBody>
        </Table>
    </TableContainer>
}

const Block: React.FC<TBlock> = (
    {block_hash, transaction_count, transactions}
): JSX.Element => {
    const [transaction, setTransaction] = React.useState<TTransaction | undefined>()

    const handleClick = (hash: string) => {
        Blockchain.getTransactionByHash(hash).then(setTransaction)
    }

    return <TableContainer>
        <Table>
            <TableHead>
                <TableRow>
                    <TableCell>Block Hash</TableCell>
                    <TableCell>Transaction Count</TableCell>
                    <TableCell>Transactions</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                <TableRow>
                    <TableCell>{block_hash}</TableCell>
                    <TableCell>{transaction_count}</TableCell>
                    <TableCell>
                        {transactions.map((t, idx) =>
                            <Typography
                                onClick={() => handleClick(t)}
                                key={idx}
                            >
                                {t}
                            </Typography>
                        )}
                    </TableCell>
                </TableRow>
                {transaction && <TableRow>
                    <TableCell>
                        <Transaction {...transaction} />
                    </TableCell>
                </TableRow>}
            </TableBody>
        </Table>
    </TableContainer>
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