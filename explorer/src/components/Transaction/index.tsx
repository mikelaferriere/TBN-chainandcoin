import React from 'react';

import { makeStyles } from '@material-ui/core/styles';

import {
  Card,
  CardContent,
  Typography,
} from '@material-ui/core';

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

interface Props {
    transaction?: TTransaction
}

const useStyles = makeStyles({
    root: {
        margin: 'auto',
        display: 'flex'
    },
    title: {
        fontSize: 14,
    },
});

const Transaction: React.FC<Props> = ({transaction}): JSX.Element => {
    const classes = useStyles();

    if (!transaction) return <div></div>
    return (
        <Card className={classes.root}>
            <CardContent>
                <Typography variant="h6" component="h2">
                    {transaction.signed_transaction.details.sender}
                </Typography>
                <Typography className={classes.title} color="textSecondary" gutterBottom>
                    Sender
                </Typography>
                <Typography variant="h6" component="h2">
                    {transaction.signed_transaction.details.recipient}
                </Typography>
                <Typography className={classes.title} color="textSecondary" gutterBottom>
                    Recipient
                </Typography>
                <Typography variant="h6" component="h2">
                    {transaction.signed_transaction.details.amount}
                </Typography>
                <Typography className={classes.title} color="textSecondary" gutterBottom>
                    Amount
                </Typography>
                <Typography variant="h6" component="h2">
                    {transaction.signed_transaction.details.timestamp}
                </Typography>
                <Typography className={classes.title} color="textSecondary" gutterBottom>
                    Date
                </Typography>
            </CardContent>
        </Card>
    );
}


export default Transaction;