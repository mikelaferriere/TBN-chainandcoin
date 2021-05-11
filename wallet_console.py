import logging
import getpass
from walletv3 import Wallet

logging.basicConfig(level=logging.INFO)


class WalletNode:
    """
    This wallet node class runs a wallet instance
    """

    def __init__(self):
        self.wallet = Wallet()

    # Prompts the user for its choice and return it
    def get_user_choice(self):
        user_input = input("Your choice: ")
        print("\n")
        return user_input

    # Starts the node and waits for user input
    def listen_for_input(self) -> None:
        waiting_for_input = True

        # User Input Interface
        while waiting_for_input:
            print("Please choose")
            print("1: Login to wallet")
            print("2: Create new login for wallet")
            print("3: Create address")
            print("q: Quit")
            user_choice = self.get_user_choice()
            if user_choice == "1":
                password = getpass.getpass()
                result = self.wallet.login(password)
                if result:
                    print("Logged into wallet successfully")
            elif user_choice == "2":
                password = getpass.getpass()
                result = self.wallet.create_login(password)
                if result:
                    print("Wallet created successfully")
            elif user_choice == "3":
                address = self.wallet.generate_address()
                self.wallet.save_address(address)
                print("Address created and saved")
            elif user_choice == "q":
                waiting_for_input = False
            else:
                print("Not an acceptable option\n")
                continue
            if self.wallet.logged_in:
                print(
                    "Wallet Address: {}\nBalance: {:6.2f}\n".format(
                        self.wallet.address, 0.0
                    )
                )
            else:
                print("Not logged in. No wallet to load")
        print("User left!")
        print("Done!")


if __name__ == "__main__":
    node = WalletNode()
    node.listen_for_input()
