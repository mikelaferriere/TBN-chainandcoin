import logging
import getpass
import json
from uuid import uuid4

from blockchain import Blockchain
from verification import Verification
from transaction import Transaction
from utils import configure_logging
from walletv2 import Wallet

configure_logging()


class Node:
    """
    This node class runs the local blockchain instance
    (id: Id of the node, blockchain: blockchain which is run by node)
    """

    def __init__(self):
        self.id = str(uuid4())
        self.wallet = Wallet()
        self.blockchain = None

    def get_transaction_value(self):
        """
        Get the user input, transform it from a string to a float and store it in user_input
        """
        tx_recipient = input("Enter the recipient of the transaction: ")
        tx_amount = float(input("Your transaction amount please: "))
        return tx_recipient, tx_amount

    def get_user_choice(self):
        """
        Prompts the user for its choice and return it
        """
        user_input = input("Your choice: ")
        return user_input

    def print_blockchain_elements(self):
        """
        Output the blockchain list to the console
        """
        print(json.dumps(self.blockchain.pretty_chain(), indent=2))
        print("-" * 20)

    def listen_for_input(self) -> None:  # pylint: disable=too-many-branches
        """
        Starts the node and waits for user input
        """
        waiting_for_input = True

        # User Input Interface
        while waiting_for_input:
            print("\nPlease choose")
            print("1: Add a new transaction value")
            print("2: Mine a new block")
            print("3: Output the blockchain blocks")
            print("4: Check transaction validity")
            print("q: Quit")
            user_choice = self.get_user_choice()
            if user_choice == "1":
                tx_data = self.get_transaction_value()
                recipient, amount = tx_data
                signature = self.wallet.sign_transaction(
                    self.wallet.address, recipient, amount
                )
                transaction = Transaction(
                    sender=self.wallet.address,
                    recipient=recipient,
                    amount=amount,
                    signature=signature,
                )
                if self.blockchain.add_transaction(transaction):
                    logging.info("Added transaction!")
                else:
                    logging.error("Transaction failed!")
                print(self.blockchain.get_open_transactions)
            elif user_choice == "2":
                if not self.blockchain.mine_block():
                    logging.error("Mining failed. Got no wallet?")
            elif user_choice == "3":
                self.print_blockchain_elements()
            elif user_choice == "4":
                if Verification.verify_transactions(
                    self.blockchain.get_open_transactions, self.blockchain.get_balance
                ):
                    logging.info("All transactions are valid")
                else:
                    logging.error("There are invalid transactions")
            elif user_choice == "q":
                waiting_for_input = False
            else:
                logging.warning("Input was invalid, please pick a value from the list!")
            if not Verification.verify_chain(self.blockchain.chain):
                self.print_blockchain_elements()
                logging.error("Invalid blockchain!")
                # Break out of the loop
                break
            print(
                "Wallet {}\nBalance: {:6.2f}".format(
                    self.wallet.address, self.blockchain.get_balance()
                )
            )
        else:
            logging.info("User left!")

        logging.info("Done!")


if __name__ == "__main__":
    node = Node()
    logging.info("Load wallet")
    passphrase = getpass.getpass()
    node.wallet.login(passphrase)

    if not node.wallet.logged_in:
        raise ValueError(
            "\nMust log into wallet. \n"
            "Maybe it was the wrong password?\n"
            "If you haven't created a wallet yet, follow the instructions in WALLET.md"
        )
    if not node.wallet.address:
        raise ValueError(
            "Must generate an address to be used for blockchain transactions"
        )

    node.blockchain = Blockchain(node.wallet.address, node.id)

    print("\nDo you want to sync with the blockchain, or just run it locally?")
    print("Please choose")
    print("1: Sync with network blockchain")
    print("2: Run with local blockchain")
    choice = node.get_user_choice()
    if choice == "1":
        logging.info("Connecting to MASTERNODE")
        node.blockchain.register_node("https://sedrik.life/blockchain")

        logging.info("Syncing with the network")
        node.blockchain.resolve_conflicts()

        logging.info("Synced with the network")

    print(f"Wallet {node.wallet.address}")
    print("Balance: {:6.2f}".format(node.blockchain.get_balance()))  # type: ignore
    node.listen_for_input()
