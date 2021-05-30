class NotEnoughCoinError(Exception):
    """
    Attributes:
        sender  -- sender
        amount  -- amount
        balance -- balance
        message -- explanation of the error
    """

    def __init__(
        self,
        sender: str,
        amount: int,
        balance: int,
        message="Sender does not have enough coin for this transaction",
    ) -> None:
        self.sender = sender
        self.amount = amount
        self.balance = balance
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return (
            f"Sender: {self.sender} -> Amount: {self.amount} -> "
            f"Balance: {self.balance} -> {self.message}"
        )


class InvalidNonceError(Exception):
    """
    Attributes:
        sender           -- sender
        nonce            -- nonce
        expected_nonce   -- expected nonce
        message          -- explanation of the error
    """

    def __init__(
        self,
        sender: str,
        nonce: int,
        expected_nonce: int,
        message="invalid nonce in transaction",
    ) -> None:
        self.sender = sender
        self.nonce = nonce
        self.expected_nonce = expected_nonce
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return (
            f"Sender: {self.sender} -> Transaction nonce: {self.nonce} -> "
            f"Expected nonce: {self.expected_nonce} -> {self.message}"
        )
